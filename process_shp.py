import os
import json
from pathlib import Path

# Load mapping
with open('src/shp_mapping.json', 'r') as f:
    MAPPING_TREE = json.load(f)

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
    if 'xbrli:xbrl' in data: return data['xbrli:xbrl']
    if 'xbrl' in data: return data['xbrl']
    return None

def find_contexts(data):
    contexts = {}
    root = get_root(data)
    if not root: return contexts
    
    ctxs = root.get('xbrli:context') or root.get('context', [])
    if isinstance(ctxs, dict): ctxs = [ctxs]
        
    for ctx in ctxs:
        cid = ctx.get('@id') or ctx.get('@attributes', {}).get('id')
        if not cid: continue
        contexts[cid] = {'members': [], 'period': None}
        
        period = ctx.get('xbrli:period') or ctx.get('period', {})
        if 'xbrli:instant' in period: contexts[cid]['period'] = period['xbrli:instant']
        elif 'instant' in period: contexts[cid]['period'] = period['instant']
        elif 'xbrli:endDate' in period: contexts[cid]['period'] = period['xbrli:endDate']
        elif 'endDate' in period: contexts[cid]['period'] = period['endDate']
            
        scenario = ctx.get('xbrli:scenario') or ctx.get('scenario', {})
        explicit_members = scenario.get('xbrldi:explicitMember') or scenario.get('explicitMember', [])
        typed_members = scenario.get('xbrldi:typedMember') or scenario.get('typedMember', [])
        
        if not explicit_members and not typed_members:
            entity = ctx.get('xbrli:entity') or ctx.get('entity', {})
            segment = entity.get('xbrli:segment') or entity.get('segment', {})
            explicit_members = segment.get('xbrldi:explicitMember') or segment.get('explicitMember', [])
            typed_members = segment.get('xbrldi:typedMember') or segment.get('typedMember', [])
            
        if isinstance(explicit_members, dict): explicit_members = [explicit_members]
        if isinstance(typed_members, dict): typed_members = [typed_members]
            
        for em in explicit_members:
            val = em.get('#text', '')
            if ':' in val: val = val.split(':')[1]
            contexts[cid]['members'].append(val)
            
        for tm in typed_members:
            dim = tm.get('@attributes', {}).get('dimension', '')
            if ':' in dim: dim = dim.split(':')[1]
            dim_name = dim.replace('DetailsOfSharesHeldBy', '').replace('DetailsSharesHeldBy', '').replace('Axis', '')
            if dim_name == 'IndividualsOrHUF': dim_name = 'IndividualsOrHinduUndividedFamily'
            if dim_name == 'InstitutionsForeignPortfolioInvestorOne': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryOne'
            if dim_name == 'InstitutionsForeignPortfolioInvestorTwo': dim_name = 'InstitutionsForeignPortfolioInvestorCategoryTwo'
            if dim_name.startswith('Others'): dim_name = 'Other' + dim_name[6:]
            
            best_match = next((t for t in TAG_TO_PATH.keys() if t.startswith(dim_name)), None)
            contexts[cid]['members'].append(best_match if best_match else dim)
            
    return contexts

def get_value(data, tag, context_ref=None):
    root = get_root(data)
    if not root: return None
    unprefixed_tag = tag.split(':')[-1] if ':' in tag else tag
    
    elements = root.get(tag) or root.get(unprefixed_tag, [])
    if isinstance(elements, dict): elements = [elements]
        
    if context_ref is None:
        if len(elements) > 0:
            return elements[0].get('#text', elements[0]) if isinstance(elements[0], dict) else elements[0]
        return None
        
    for el in elements:
        if isinstance(el, dict):
            c_ref = el.get('@contextRef') or el.get('@attributes', {}).get('contextRef')
            if c_ref == context_ref or c_ref == context_ref.replace('D_', '') or c_ref == 'D_' + context_ref:
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
            
        node["children"] = list(node["children_dict"].values())
        del node["children_dict"]
        
    node["percentage"] = max(node.get("explicit_percentage", 0.0), entities_pct, children_pct)
    node["shares"] = max(node.get("explicit_shares", 0.0), entities_shares, children_shares)
    
    # Sort entities descending by percentage
    node["entities"].sort(key=lambda x: x["percentage"], reverse=True)

def parse_raw(filepath):
    with open(filepath, 'r', encoding='utf-8') as f: data = json.load(f)
    contexts = find_contexts(data)
    
    gen_info = {
        "NameOfTheCompany": get_value(data, "NameOfTheCompany"),
        "ScripCode": get_value(data, "ScripCode"),
        "Symbol": get_value(data, "Symbol"),
        "DateOfReport": get_value(data, "DateOfReport"),
        "Disclosure": get_value(data, "DisclosureOfNotesOnShareholdingPatternExplanatoryTextBlock")
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
                    
        if not longest_path: continue
            
        name = get_value(data, "NameOfTheShareholder", cid)
        shares = get_value(data, "NumberOfFullyPaidUpEquityShares", cid)
        percentage = get_value(data, "ShareholdingAsAPercentageOfTotalNumberOfShares", cid)
        
        if not name: name = primary_member
            
        try: shares = float(shares) if shares else 0.0
        except ValueError: shares = 0.0
        try: percentage = float(percentage) if percentage else 0.0
        except ValueError: percentage = 0.0
            
        is_specific = get_value(data, "NameOfTheShareholder", cid) is not None
        
        curr_node = categories[longest_path[0]]
        for p in longest_path[1:]:
            curr_node = curr_node["children_dict"][p]
            
        if is_specific:
            # check if entity already exists to prevent duplication via D_ context bug
            existing = next((e for e in curr_node["entities"] if e["name"] == name), None)
            if existing:
                existing["shares"] = max(existing["shares"], shares)
                existing["percentage"] = max(existing["percentage"], percentage)
            else:
                curr_node["entities"].append({
                    "name": name,
                    "shares": shares,
                    "percentage": percentage,
                    "member_type": primary_member
                })
        else:
            curr_node["explicit_percentage"] = max(curr_node["explicit_percentage"], percentage)
            curr_node["explicit_shares"] = max(curr_node["explicit_shares"], shares)

    for cat in categories.values():
        rollup(cat)
        
    retail_cat = next((c for c in categories.values() if c["name"] == "Retail Public"), None)
    others_cat = next((c for c in categories.values() if c["name"] == "Others"), None)
    if retail_cat and others_cat:
        non_inst = next((c for c in others_cat["children"] if c["name"] == "Non Institutions"), None)
        if non_inst:
            children_pct = sum(c["percentage"] for c in non_inst["children"])
            if non_inst["percentage"] > children_pct and non_inst["percentage"] >= retail_cat["percentage"]:
                non_inst["percentage"] -= retail_cat["percentage"]
                non_inst["shares"] -= retail_cat["shares"]
                others_cat["percentage"] = sum(c["percentage"] for c in others_cat["children"])
                others_cat["shares"] = sum(c["shares"] for c in others_cat["children"])
        
    return {"general_info": gen_info, "categories": list(categories.values())}

def parse_processed(filepath):
    with open(filepath, 'r', encoding='utf-8') as f: data = json.load(f)
    
    gen_info = {
        "NameOfTheCompany": data.get("NameOfTheCompany"),
        "ScripCode": data.get("ScripCode"),
        "Symbol": data.get("Symbol"),
        "DateOfReport": data.get("DateOfReport"),
        "Disclosure": data.get("DisclosureOfNotesOnShareholdingPatternExplanatoryTextBlock")
    }
    
    categories = {c["name"]: init_tree(c) for c in MAPPING_TREE["children"]}
    
    # Processed JSON uses flat keys for aggregates (e.g. data['IndianMember'])
    # and domain keys for specific entities (e.g. data['IndividualsOrHUFDomain'])
    
    def process_node(node):
        member = node.get("member")
        if member and member in data:
            agg_data = data[member]
            if isinstance(agg_data, dict):
                try: node["explicit_percentage"] = float(agg_data.get("ShareholdingAsAPercentageOfTotalNumberOfShares", 0.0))
                except ValueError: pass
                try: node["explicit_shares"] = float(agg_data.get("NumberOfFullyPaidUpEquityShares", 0.0))
                except ValueError: pass
                
        # Find matching domain for entities (heuristically by replacing Member with Domain)
        if member:
            domain_name = member.replace('Member', 'Domain')
            domain_candidates = [
                domain_name,
                domain_name.replace('IndividualsOrHinduUndividedFamily', 'IndividualsOrHUF'),
                domain_name.replace('Other', 'Others'),
                domain_name.replace('InstitutionsForeignPortfolioInvestorCategoryOne', 'DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorOne'),
                domain_name.replace('InstitutionsForeignPortfolioInvestorCategoryTwo', 'DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorTwo'),
                domain_name.replace('OtherInstitutionsForeign', 'DetailsOfSharesHeldByOtherInstitutionsForeign')
            ]
            
            matched_domain = next((d for d in domain_candidates if d in data), None)
            
            if matched_domain:
                entities_dict = data[matched_domain]
                for entity_data in entities_dict.values():
                    try: pct = float(entity_data.get("ShareholdingAsAPercentageOfTotalNumberOfShares", 0.0))
                    except ValueError: pct = 0.0
                    try: shs = float(entity_data.get("NumberOfFullyPaidUpEquityShares", 0.0))
                    except ValueError: shs = 0.0
                    
                    node["entities"].append({
                        "name": entity_data.get("NameOfTheShareholder", "Unknown"),
                        "shares": shs,
                        "percentage": pct,
                        "member_type": member
                    })
        
        if "children_dict" in node:
            for child in node["children_dict"].values():
                process_node(child)
                
    for cat in categories.values():
        process_node(cat)
        rollup(cat)
        
    retail_cat = next((c for c in categories.values() if c["name"] == "Retail Public"), None)
    others_cat = next((c for c in categories.values() if c["name"] == "Others"), None)
    if retail_cat and others_cat:
        non_inst = next((c for c in others_cat["children"] if c["name"] == "Non Institutions"), None)
        if non_inst:
            children_pct = sum(c["percentage"] for c in non_inst["children"])
            if non_inst["percentage"] > children_pct and non_inst["percentage"] >= retail_cat["percentage"]:
                non_inst["percentage"] -= retail_cat["percentage"]
                non_inst["shares"] -= retail_cat["shares"]
                others_cat["percentage"] = sum(c["percentage"] for c in others_cat["children"])
                others_cat["shares"] = sum(c["shares"] for c in others_cat["children"])
                
    return {"general_info": gen_info, "categories": list(categories.values())}

def main():
    examples_dir = Path("D:/My Drive/New Directories/WORK/XBRL/Shareholding Pattern/Examples")
    out_raw = {"companies": [], "data": {}}
    out_proc = {"companies": [], "data": {}}
    
    if not examples_dir.exists(): return
        
    for company_dir in examples_dir.iterdir():
        if not company_dir.is_dir(): continue
        company = company_dir.name
        
        has_raw = False
        has_proc = False
        raw_data_map = {}
        proc_data_map = {}
        
        for quarter_dir in company_dir.iterdir():
            if not quarter_dir.is_dir(): continue
            quarter = quarter_dir.name
            
            for file in quarter_dir.iterdir():
                if file.suffix == '.json':
                    if 'raw' in file.name.lower():
                        try:
                            raw_data_map[quarter] = parse_raw(file)
                            has_raw = True
                        except Exception as e: print(f"Error raw {file}: {e}")
                    elif 'processed' in file.name.lower():
                        try:
                            proc_data_map[quarter] = parse_processed(file)
                            has_proc = True
                        except Exception as e: print(f"Error processed {file}: {e}")
                        
        if has_raw:
            out_raw["companies"].append(company)
            out_raw["data"][company] = raw_data_map
        if has_proc:
            out_proc["companies"].append(company)
            out_proc["data"][company] = proc_data_map
            
    out_raw["companies"].sort()
    out_proc["companies"].sort()
    
    os.makedirs('public/data', exist_ok=True)
    with open('public/data/all_shp_data_raw.json', 'w', encoding='utf-8') as f:
        json.dump(out_raw, f, indent=2)
    with open('public/data/all_shp_data_processed.json', 'w', encoding='utf-8') as f:
        json.dump(out_proc, f, indent=2)
    print("Processing complete! Output to all_shp_data_raw.json and all_shp_data_processed.json")

if __name__ == "__main__":
    main()
