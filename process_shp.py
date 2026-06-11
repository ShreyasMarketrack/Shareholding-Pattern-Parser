import os
import json

EXAMPLES_DIR = r"d:\My Drive\New Directories\WORK\XBRL\Shareholding Pattern\Examples"
OUTPUT_DIR = r"d:\My Drive\New Directories\WORK\XBRL\Shareholding Pattern\Viewer\public\data"
MAPPING_FILE = r"d:\My Drive\New Directories\WORK\XBRL\Shareholding Pattern\Viewer\src\shp_mapping.json"

with open(MAPPING_FILE, 'r') as f:
    mapping = json.load(f)

def clean_value(val):
    if not val or val == "******": return 0.0
    try:
        return float(val)
    except:
        return 0.0

def process_company(company_path, company_name):
    company_data = {}
    if not os.path.isdir(company_path): return None
    
    for quarter in os.listdir(company_path):
        quarter_path = os.path.join(company_path, quarter)
        if not os.path.isdir(quarter_path): continue
        
        processed_file = os.path.join(quarter_path, f"{company_name}_processed.json")
        if not os.path.exists(processed_file): continue
        
        with open(processed_file, 'r', encoding='utf-8') as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                continue
                
        quarter_data = {
            "Promoters": {"percentage": 0.0, "children": []},
            "Foreign Institutions": {"percentage": 0.0, "children": []},
            "Domestic Institutions": {"percentage": 0.0, "children": []},
            "Retail Individuals": {"percentage": 0.0, "children": []},
            "Government": {"percentage": 0.0, "children": []},
            "Others": {"percentage": 0.0, "children": []}
        }
        
        for category, tags in mapping.items():
            cat_sum = 0.0
            for tag in tags:
                # Check for top-level stats
                if tag in raw_data:
                    val = clean_value(raw_data[tag].get("ShareholdingAsAPercentageOfTotalNumberOfShares", 0))
                    # Avoid double counting if it's already a parent sum in the mapping
                    if tag == "ShareholdingOfPromoterAndPromoterGroupMember":
                        # We use this as the definitive promoter sum, so we overwrite cat_sum
                        cat_sum = val
                    elif tag not in ["InstitutionsForeignMember", "InstitutionsDomesticMember"]:
                        # Normal leaf node accumulation
                        if val > 0:
                            cat_sum += val
                            quarter_data[category]["children"].append({
                                "name": tag.replace("Member", ""),
                                "percentage": val,
                                "details": raw_data[tag]
                            })
                
                # Check for Domain contextrefs for this tag
                domain_key = tag.replace("Member", "Domain")
                # sometimes it's abbreviated like IndividualsOrHUFDomain
                if tag == "IndividualsOrHinduUndividedFamilyMember": domain_key = "IndividualsOrHUFDomain"
                
                if domain_key in raw_data:
                    for ctx_id, ctx_data in raw_data[domain_key].items():
                        ctx_val = clean_value(ctx_data.get("ShareholdingAsAPercentageOfTotalNumberOfShares", 0))
                        if ctx_val > 0:
                            quarter_data[category]["children"].append({
                                "name": ctx_data.get("NameOfTheShareholder", ctx_id),
                                "percentage": ctx_val,
                                "details": ctx_data
                            })
                            
            quarter_data[category]["percentage"] = round(cat_sum, 2)
            
        company_data[quarter] = quarter_data
    
    return company_data

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    all_data = {}
    companies = []
    
    for company in os.listdir(EXAMPLES_DIR):
        company_path = os.path.join(EXAMPLES_DIR, company)
        if os.path.isdir(company_path):
            comp_data = process_company(company_path, company)
            if comp_data:
                all_data[company] = comp_data
                companies.append(company)
                
    output_json = {
        "companies": sorted(companies),
        "data": all_data
    }
    
    with open(os.path.join(OUTPUT_DIR, "all_shp_data.json"), 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2)
        
    print(f"Processed {len(companies)} companies successfully.")

if __name__ == "__main__":
    main()
