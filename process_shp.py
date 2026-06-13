import os
import json
from pathlib import Path

# Load mapping
with open('src/shp_mapping.json', 'r') as f:
    MAPPING_TREE = json.load(f)

# Create lookup: tag -> path in tree
TAG_TO_PATH = {}
def build_tag_path(node, current_path):
    if "member" in node:
        TAG_TO_PATH[node["member"]] = current_path
    if "children" in node:
        for child in node["children"]:
            build_tag_path(child, current_path + [child["name"]])

for child in MAPPING_TREE.get("children", []):
    build_tag_path(child, [child["name"]])

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
    
    ctxs = root.get('xbrli:context') or root.get('context', [])
    if isinstance(ctxs, dict):
        ctxs = [ctxs]
        
    for ctx in ctxs:
        cid = ctx.get('@id') or ctx.get('@attributes', {}).get('id')
        if not cid: continue
        contexts[cid] = {'members': [], 'period': None}
        
        period = ctx.get('xbrli:period') or ctx.get('period', {})
        if 'xbrli:instant' in period:
            contexts[cid]['period'] = period['xbrli:instant']
        elif 'instant' in period:
            contexts[cid]['period'] = period['instant']
        elif 'xbrli:endDate' in period:
            contexts[cid]['period'] = period['xbrli:endDate']
        elif 'endDate' in period:
            contexts[cid]['period'] = period['endDate']
            
        scenario = ctx.get('xbrli:scenario') or ctx.get('scenario', {})
        explicit_members = scenario.get('xbrldi:explicitMember') or scenario.get('explicitMember', [])
        typed_members = scenario.get('xbrldi:typedMember') or scenario.get('typedMember', [])
        
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
            dim_name = dim.replace('DetailsOfSharesHeldBy', '').replace('DetailsSharesHeldBy', '').replace('Axis', '')
            
            if dim_name == 'IndividualsOrHUF': dim_name = 'IndividualsOrHinduUndividedFamily'
            if dim_name == 'InstitutionsForeignPortfolioInvestorOne': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryOne'
            if dim_name == 'InstitutionsForeignPortfolioInvestorTwo': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryTwo'
            
            best_match = None
            for tag in TAG_TO_PATH.keys():
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

def init_tree(node):
    res = {
        "name": node.get("name"),
        "member": node.get("member"),
        "explicit_percentage": 0.0,
        "explicit_shares": 0.0,
        "percentage": 0.0,
        "shares": 0.0,
        "entities": []
    }
    if "children" in node:
        res["children_dict"] = {c["name"]: init_tree(c) for c in node["children"]}
    return res

def rollup(node):
    entities_pct = sum(e["percentage"] for e in node["entities"])
    entities_shares = sum(e["shares"] for e in node["entities"])
    
    children_pct = 0.0
    children_shares = 0.0
    
    if "children_dict" in node:
        for child in node["children_dict"].values():
            rollup(child)
            children_pct += child["percentage"]
            children_shares += child["shares"]
            
        # Convert children_dict to list for frontend
        node["children"] = list(node["children_dict"].values())
        del node["children_dict"]
        
    node["percentage"] = max(node.get("explicit_percentage", 0.0), entities_pct, children_pct)
    node["shares"] = max(node.get("explicit_shares", 0.0), entities_shares, children_shares)
    
def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    contexts = find_contexts(data)
    
    gen_info = {
        "NameOfTheCompany": get_value(data, "NameOfTheCompany"),
        "ScripCode": get_value(data, "ScripCode"),
        "Symbol": get_value(data, "Symbol"),
        "DateOfReport": get_value(data, "DateOfReport")
    }
    
    categories = {c["name"]: init_tree(c) for c in MAPPING_TREE["children"]}
    
    for cid, ctx in contexts.items():
        if len(ctx['members']) == 0: continue
        
        longest_path = []
        primary_member = None
        
        for member in ctx['members']:
            if member in TAG_TO_PATH:
                path = TAG_TO_PATH[member]
                if len(path) > len(longest_path):
                    longest_path = path
                    primary_member = member
                    
        if not longest_path:
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
        
        # Traverse tree to the correct node
        curr_node = categories[longest_path[0]]
        for p in longest_path[1:]:
            curr_node = curr_node["children_dict"][p]
            
        if is_specific:
            curr_node["entities"].append({
                "name": name,
                "shares": shares,
                "percentage": percentage,
                "member_type": primary_member
            })
        else:
            curr_node["explicit_percentage"] = percentage
            curr_node["explicit_shares"] = shares

    # Rollup totals
    for cat in categories.values():
        rollup(cat)
        
    # FIX: The user requested "Retail Public" and "Others" as separate root buckets.
    # However, in the XBRL taxonomy, "Retail Public" (Resident Individuals) are children of "NonInstitutionsMember".
    # Because "Others" maps "NonInstitutionsMember", its explicit percentage will include "Retail Public", causing double counting.
    # We must deduct "Retail Public" from "Others" if "Others" relied on the explicit "NonInstitutionsMember" value.
    retail_cat = next((c for c in categories.values() if c["name"] == "Retail Public"), None)
    others_cat = next((c for c in categories.values() if c["name"] == "Others"), None)
    
    if retail_cat and others_cat:
        # Find the 'Non Institutions' child under 'Others'
        non_inst = next((c for c in others_cat["children"] if c["name"] == "Non Institutions"), None)
        if non_inst:
            # If the explicit percentage was used and it's >= retail, subtract retail
            # We determine if explicit was used if its percentage > sum of its children's percentages
            children_pct = sum(c["percentage"] for c in non_inst["children"])
            if non_inst["percentage"] > children_pct and non_inst["percentage"] >= retail_cat["percentage"]:
                deduction_pct = retail_cat["percentage"]
                deduction_shares = retail_cat["shares"]
                
                non_inst["percentage"] -= deduction_pct
                non_inst["shares"] -= deduction_shares
                
                # Re-rollup Others
                others_cat["percentage"] = sum(c["percentage"] for c in others_cat["children"])
                others_cat["shares"] = sum(c["shares"] for c in others_cat["children"])
        
    return {"general_info": gen_info, "categories": list(categories.values())}

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
