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

def get_root(data):
    if 'xbrli:xbrl' in data:
        return data['xbrli:xbrl']
    if 'xbrl' in data:
        return data['xbrl']
    return None

def find_contexts(data):
    contexts = {}
    root = get_root(data)
    if not root: return contexts
    
    # Contexts might be 'xbrli:context' or 'context'
    ctxs = root.get('xbrli:context') or root.get('context', [])
    if isinstance(ctxs, dict):
        ctxs = [ctxs]
        
    for ctx in ctxs:
        cid = ctx.get('@id') or ctx.get('@attributes', {}).get('id')
        if not cid: continue
        contexts[cid] = {'members': [], 'period': None}
        
        # Extract period
        period = ctx.get('xbrli:period') or ctx.get('period', {})
        if 'xbrli:instant' in period:
            contexts[cid]['period'] = period['xbrli:instant']
        elif 'instant' in period:
            contexts[cid]['period'] = period['instant']
        elif 'xbrli:endDate' in period:
            contexts[cid]['period'] = period['xbrli:endDate']
        elif 'endDate' in period:
            contexts[cid]['period'] = period['endDate']
            
        # Extract explicit members
        scenario = ctx.get('xbrli:scenario') or ctx.get('scenario', {})
        explicit_members = scenario.get('xbrldi:explicitMember') or scenario.get('explicitMember', [])
        typed_members = scenario.get('xbrldi:typedMember') or scenario.get('typedMember', [])
        
        # if not found in scenario, check segment
        if not explicit_members and not typed_members:
            entity = ctx.get('xbrli:entity') or ctx.get('entity', {})
            segment = entity.get('xbrli:segment') or entity.get('segment', {})
            explicit_members = segment.get('xbrldi:explicitMember') or segment.get('explicitMember', [])
            typed_members = segment.get('xbrldi:typedMember') or segment.get('typedMember', [])
            
        if isinstance(explicit_members, dict):
            explicit_members = [explicit_members]
        if isinstance(typed_members, dict):
            typed_members = [typed_members]
            
        for em in explicit_members:
            val = em.get('#text', '')
            if ':' in val:
                val = val.split(':')[1]
            contexts[cid]['members'].append(val)
            
        for tm in typed_members:
            dim = tm.get('@attributes', {}).get('dimension', '')
            if ':' in dim:
                dim = dim.split(':')[1]
            # Map Axis back to Member (heuristic)
            # e.g. DetailsSharesHeldByIndividualsOrHUFAxis -> IndividualsOrHinduUndividedFamilyMember (mapping is tricky, but we can do a substring match against TAG_TO_CATEGORY)
            dim_name = dim.replace('DetailsOfSharesHeldBy', '').replace('DetailsSharesHeldBy', '').replace('Axis', '')
            
            # Special case mappings
            if dim_name == 'IndividualsOrHUF': dim_name = 'IndividualsOrHinduUndividedFamily'
            if dim_name == 'InstitutionsForeignPortfolioInvestorOne': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryOne'
            if dim_name == 'InstitutionsForeignPortfolioInvestorTwo': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryTwo'
            
            # Find closest member in TAG_TO_CATEGORY
            best_match = None
            for tag in TAG_TO_CATEGORY.keys():
                if tag.startswith(dim_name):
                    best_match = tag
                    break
            
            if best_match:
                contexts[cid]['members'].append(best_match)
            else:
                contexts[cid]['members'].append(dim)
            
    return contexts

def get_value(data, tag, context_ref=None):
    root = get_root(data)
    if not root: return None
    
    # Check for tag with and without namespace
    unprefixed_tag = tag.split(':')[-1] if ':' in tag else tag
    
    elements = root.get(tag) or root.get(unprefixed_tag, [])
    if isinstance(elements, dict):
        elements = [elements]
        
    if context_ref is None:
        if len(elements) > 0:
            return elements[0].get('#text', elements[0]) if isinstance(elements[0], dict) else elements[0]
        return None
        
    for el in elements:
        if isinstance(el, dict):
            c_ref = el.get('@contextRef') or el.get('@attributes', {}).get('contextRef')
            if c_ref == context_ref:
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
        
        mapped_category = None
        primary_member = None
        
        for member in ctx['members']:
            if member in TAG_TO_CATEGORY:
                mapped_category = TAG_TO_CATEGORY[member]
                primary_member = member
                
        if not mapped_category:
            continue
            
        name = get_value(data, "NameOfTheShareholder", cid)
        shares = get_value(data, "NumberOfFullyPaidUpEquityShares", cid)
        percentage = get_value(data, "ShareholdingAsAPercentageOfTotalNumberOfShares", cid)
        
        if not name:
            name = primary_member
            
        try:
            shares = float(shares) if shares else 0.0
            percentage = float(percentage) if percentage else 0.0
        except ValueError:
            shares = 0.0
            percentage = 0.0
            
        is_specific = get_value(data, "NameOfTheShareholder", cid) is not None
        
        categories[mapped_category]["entities"].append({
            "name": name,
            "shares": shares,
            "percentage": percentage,
            "member_type": primary_member,
            "is_specific": is_specific
        })

    for cat in categories:
        specific_sum_pct = sum(e["percentage"] for e in categories[cat]["entities"] if e["is_specific"])
        root_pct = 0.0
        for e in categories[cat]["entities"]:
            if not e["is_specific"]:
                root_pct = max(root_pct, e["percentage"])
                
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
                        processed = process_file(file)
                        output_data["data"][company][quarter] = processed
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                        
    output_data["companies"].sort()
    
    os.makedirs('public/data', exist_ok=True)
    with open('public/data/all_shp_data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print("Processing complete! Data output to public/data/all_shp_data.json")

if __name__ == "__main__":
    main()
