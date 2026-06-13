import os
import json
from pathlib import Path

# Load mapping
with open('src/shp_mapping.json', 'r') as f:
    MAPPING = json.load(f)

# Reverse mapping for O(1) lookup: tag -> Category
TAG_TO_CATEGORY = {}
for category, tags in MAPPING.items():
    for tag in tags:
        TAG_TO_CATEGORY[tag] = category

def find_contexts(data):
    contexts = {}
    if 'xbrli:xbrl' in data:
        ctxs = data['xbrli:xbrl'].get('xbrli:context', [])
        if isinstance(ctxs, dict):
            ctxs = [ctxs]
        for ctx in ctxs:
            cid = ctx.get('@id')
            if not cid: continue
            contexts[cid] = {'members': [], 'period': None}
            
            # Extract period
            period = ctx.get('xbrli:period', {})
            if 'xbrli:instant' in period:
                contexts[cid]['period'] = period['xbrli:instant']
            elif 'xbrli:endDate' in period:
                contexts[cid]['period'] = period['xbrli:endDate']
                
            # Extract explicit members
            entity = ctx.get('xbrli:entity', {})
            segment = entity.get('xbrli:segment', {})
            explicit_members = segment.get('xbrldi:explicitMember', [])
            if isinstance(explicit_members, dict):
                explicit_members = [explicit_members]
            for em in explicit_members:
                val = em.get('#text', '')
                if ':' in val:
                    val = val.split(':')[1]
                contexts[cid]['members'].append(val)
    return contexts

def get_value(data, tag, context_ref=None):
    if 'xbrli:xbrl' not in data: return None
    elements = data['xbrli:xbrl'].get(tag, [])
    if isinstance(elements, dict):
        elements = [elements]
    
    if context_ref is None:
        if len(elements) > 0:
            return elements[0].get('#text', elements[0])
        return None
        
    for el in elements:
        if isinstance(el, dict) and el.get('@contextRef') == context_ref:
            return el.get('#text', el)
    return None

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    contexts = find_contexts(data)
    
    # Extract General Info
    gen_info = {
        "NameOfTheCompany": get_value(data, "in-bse-shp:NameOfTheCompany"),
        "ScripCode": get_value(data, "in-bse-shp:ScripCode"),
        "Symbol": get_value(data, "in-bse-shp:Symbol"),
        "DateOfReport": get_value(data, "in-bse-shp:DateOfReport")
    }
    
    # Initialize categories
    categories = {cat: {"percentage": 0.0, "shares": 0, "entities": []} for cat in MAPPING.keys()}
    
    # Find all shareholder details based on context
    for cid, ctx in contexts.items():
        if len(ctx['members']) == 0: continue
        
        # Determine the lowest level member mapped in our taxonomy
        mapped_category = None
        primary_member = None
        
        for member in ctx['members']:
            if member in TAG_TO_CATEGORY:
                mapped_category = TAG_TO_CATEGORY[member]
                primary_member = member
                
        if not mapped_category:
            continue
            
        # Extract data for this context
        name = get_value(data, "in-bse-shp:NameOfTheShareholders", cid)
        shares = get_value(data, "in-bse-shp:NumberOfFullyPaidUpEquitySharesHeld", cid)
        percentage = get_value(data, "in-bse-shp:ShareholdingAsAPercentageOfTotalNoOfShares", cid)
        
        if not name:
            name = primary_member
            
        try:
            shares = float(shares) if shares else 0.0
            percentage = float(percentage) if percentage else 0.0
        except ValueError:
            shares = 0.0
            percentage = 0.0
            
        # We only want to add leaf nodes (specific shareholders or sub-groups) to avoid double counting
        # For simplicity in this logic, if it has a NameOfTheShareholders, it's a specific entry
        is_specific = get_value(data, "in-bse-shp:NameOfTheShareholders", cid) is not None
        
        categories[mapped_category]["entities"].append({
            "name": name,
            "shares": shares,
            "percentage": percentage,
            "member_type": primary_member,
            "is_specific": is_specific
        })

    # Rollup totals to avoid exceeding 100%. We take the max of (sum of specific children) OR the root member value.
    for cat in categories:
        specific_sum_pct = sum(e["percentage"] for e in categories[cat]["entities"] if e["is_specific"])
        
        # Find the root aggregate for this category if present
        root_pct = 0.0
        for e in categories[cat]["entities"]:
            if not e["is_specific"]:
                root_pct = max(root_pct, e["percentage"])
                
        # The category percentage is whichever is higher: the sum of explicit children, or the root aggregate value
        categories[cat]["percentage"] = max(specific_sum_pct, root_pct)
        
    return {"general_info": gen_info, "categories": categories}

def main():
    examples_dir = Path("D:/My Drive/New Directories/WORK/XBRL/Shareholding Pattern/Examples")
    output_data = {"companies": [], "data": {}}
    
    if not examples_dir.exists():
        print(f"Directory not found: {examples_dir}")
        return
        
    for company_dir in examples_dir.iterdir():
        if not company_dir.is_dir(): continue
        company = company_dir.name
        output_data["companies"].append(company)
        output_data["data"][company] = {}
        
        for quarter_dir in company_dir.iterdir():
            if not quarter_dir.is_dir(): continue
            quarter = quarter_dir.name
            
            for file in quarter_dir.iterdir():
                if file.suffix == '.json' and 'raw' in file.name.lower():
                    try:
                        print(f"Processing {company}/{quarter}/{file.name}")
                        processed = process_file(file)
                        output_data["data"][company][quarter] = processed
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                        
    output_data["companies"].sort()
    
    os.makedirs('public/data', exist_ok=True)
    with open('public/data/all_shp_data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print("Processing complete!")

if __name__ == "__main__":
    main()
