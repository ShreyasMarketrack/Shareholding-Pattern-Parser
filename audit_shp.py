import os
import glob
import json

DATA_DIR = "D:/My Drive/New Directories/WORK/XBRL/Shareholding Pattern/Examples"
MAPPING_FILE = "src/shp_mapping.json"
OUTPUT_FILE = "C:/Users/jshre/.gemini/antigravity-ide/brain/34c6cc58-c67d-4763-9ad8-e76a59ca4aa0/taxonomy_drift_report.md"

def load_mapping():
    with open(MAPPING_FILE, 'r') as f:
        return json.load(f)

def extract_valid_members(node):
    members = set()
    if "member" in node and node["member"]:
        members.add(node["member"])
    for child in node.get("children", []):
        members.update(extract_valid_members(child))
    return members

def run_audit():
    mapping = load_mapping()
    valid_members = extract_valid_members(mapping)
    # Also valid domains just in case
    valid_domains = {m.replace('Member', 'Domain') for m in valid_members}
    
    anomalies = []
    
    for comp_dir in glob.glob(os.path.join(DATA_DIR, "*")):
        if not os.path.isdir(comp_dir): continue
        comp = os.path.basename(comp_dir)
        
        for q_dir in glob.glob(os.path.join(comp_dir, "*")):
            if not os.path.isdir(q_dir): continue
            q = os.path.basename(q_dir)
            
            raw_path = os.path.join(q_dir, f"{comp}_raw_xbrl.json")
            proc_path = os.path.join(q_dir, f"{comp}_processed.json")
            
            # --- Audit Raw JSON ---
            if os.path.exists(raw_path):
                with open(raw_path, 'r', encoding='utf-8') as f:
                    try:
                        raw_data = json.load(f)
                        root = raw_data.get("xbrl", {})
                        contexts = root.get("context", [])
                        if isinstance(contexts, dict): contexts = [contexts]
                        
                        context_member_map = {}
                        for ctx in contexts:
                            ctx_id = ctx.get("@attributes", {}).get("id")
                            entity = ctx.get("entity", {})
                            segment = entity.get("segment", {})
                            member_val = None
                            
                            # Typed member
                            if "xbrldi:typedMember" in segment:
                                typed = segment["xbrldi:typedMember"]
                                if isinstance(typed, list): typed = typed[0]
                                for k, v in typed.items():
                                    if k.startswith("@"): continue
                                    member_val = k
                            # Explicit member
                            elif "xbrldi:explicitMember" in segment:
                                exp = segment["xbrldi:explicitMember"]
                                if isinstance(exp, list): exp = exp[0]
                                member_val = exp.get("#text", "").split(":")[-1]
                            
                            if ctx_id and member_val:
                                context_member_map[ctx_id] = member_val
                                
                        # Find contexts that actually have shares
                        shares = root.get("NumberOfShares", [])
                        if isinstance(shares, dict): shares = [shares]
                        for share in shares:
                            val_str = share.get("#text", "0")
                            try:
                                val = float(val_str)
                                if val > 0:
                                    ctx_id = share.get("@attributes", {}).get("contextRef")
                                    if ctx_id in context_member_map:
                                        mem = context_member_map[ctx_id]
                                        if mem not in valid_members and mem not in valid_domains:
                                            anomalies.append({
                                                "company": comp, "quarter": q, "source": "raw",
                                                "tag": mem, "value": val, "context": ctx_id
                                            })
                            except:
                                pass
                    except Exception as e:
                        print(f"Error reading raw {raw_path}: {e}")

            # --- Audit Processed JSON ---
            if os.path.exists(proc_path):
                with open(proc_path, 'r', encoding='utf-8') as f:
                    try:
                        proc_data = json.load(f)
                        for domain_key, entities in proc_data.items():
                            if 'Domain' in domain_key or 'Member' in domain_key:
                                # Check if domain has any shares > 0
                                has_shares = False
                                for ent in entities.values():
                                    try:
                                        if float(ent.get("NumberOfShares", 0)) > 0:
                                            has_shares = True
                                            break
                                    except: pass
                                
                                if has_shares:
                                    # Fallbacks previously in process_shp.py
                                    d_test = domain_key
                                    d_test2 = domain_key.replace('IndividualsOrHinduUndividedFamily', 'IndividualsOrHUF')
                                    d_test3 = domain_key.replace('Other', 'Others')
                                    d_test4 = domain_key.replace('InstitutionsForeignPortfolioInvestorCategoryOne', 'DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorOne')
                                    d_test5 = domain_key.replace('InstitutionsForeignPortfolioInvestorCategoryTwo', 'DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorTwo')
                                    d_test6 = domain_key.replace('OtherInstitutionsForeign', 'DetailsOfSharesHeldByOtherInstitutionsForeign')
                                    
                                    # We just check if it literally matches any valid domain directly
                                    # To report drifts, we check against valid_domains
                                    if domain_key not in valid_domains and domain_key not in valid_members:
                                        # It's an anomaly (drift)
                                        anomalies.append({
                                            "company": comp, "quarter": q, "source": "processed",
                                            "tag": domain_key, "value": "N/A", "context": "N/A"
                                        })
                    except Exception as e:
                        print(f"Error reading proc {proc_path}: {e}")

    # Generate Report
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Taxonomy Drift & Leakage Report\n\n")
        
        # Deduplicate anomalies for summary
        drift_summary = {}
        for a in anomalies:
            tag = a["tag"]
            if tag not in drift_summary:
                drift_summary[tag] = []
            drift_summary[tag].append(a)
            
        if not drift_summary:
            f.write("✅ **Zero taxonomy drifts found! All data-bearing tags map perfectly to the schema.**\n")
        else:
            f.write(f"⚠️ **Found {len(drift_summary)} anomalous/legacy tags bearing numerical data!**\n\n")
            for tag, occurrences in drift_summary.items():
                f.write(f"### `{tag}`\n")
                f.write(f"- **Occurrences:** {len(occurrences)} times\n")
                f.write("- **Examples:**\n")
                for occ in occurrences[:3]:
                    f.write(f"  - Company: {occ['company']} | Quarter: {occ['quarter']} | Source: {occ['source']} | Value: {occ['value']}\n")
                if len(occurrences) > 3:
                    f.write(f"  - *...and {len(occurrences) - 3} more*\n")
                f.write("\n")

if __name__ == "__main__":
    run_audit()
