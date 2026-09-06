"""Analyze required source CSVs and write five analysis CSVs plus quality checks."""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUTPUTS = ROOT / "outputs"
def read(name): 
    with (DATA / name).open(encoding="utf-8") as f: return list(csv.DictReader(f))
def write(name, rows):
    OUTPUTS.mkdir(exist_ok=True)
    with (OUTPUTS / name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["message"]); w.writeheader(); w.writerows(rows)
def main():
    products={r["sku"]:r for r in read("product_master.csv")}; snapshots=read("inventory_snapshot.csv")
    transactions=read("transactions.csv"); counts=read("cycle_counts.csv"); orders=read("orders.csv")
    by_key=defaultdict(lambda: {"system":0,"variance":0,"events":0,"bad":0,"zero":0,"demand":[],"last":0})
    for r in snapshots:
        k=(r["sku"],r["location_id"]); q=int(r["closing_quantity"]); by_key[k]["last"]=q; by_key[k]["zero"]+=q<=0
    for r in transactions:
        if r["transaction_type"]=="SALE": by_key[(r["sku"],r["location_id"])]["demand"].append(int(r["quantity"]))
    for r in counts:
        k=(r["sku"],r["location_id"]); a=by_key[k]; s,c=int(r["system_quantity"]),int(r["counted_quantity"])
        a["system"]+=s; a["variance"]+=abs(s-c); a["events"]+=1; a["bad"]+=abs(s-c)>1
    accuracy=[]; risk=[]; action=[]; variance=[]
    for (sku,loc), a in by_key.items():
        pct=max(0,100*(1-a["variance"]/max(1,a["system"])))
        demand=a["demand"]; avg=sum(demand)/len(demand) if demand else 0
        sd=math.sqrt(sum((x-avg)**2 for x in demand)/len(demand)) if demand else 0
        p=products[sku]; safety=1.65*sd*math.sqrt(int(p["lead_time_days"]))
        score=min(100,100*(.55*a["zero"]/731+.45*max(0,(int(p["reorder_point"])+safety-a["last"])/max(1,int(p["reorder_point"])+safety))))
        band="High" if score>=55 else "Medium" if score>=25 else "Low"
        accuracy.append({"sku":sku,"location_id":loc,"count_events":a["events"],"absolute_variance_units":a["variance"],"accuracy_pct":f"{pct:.2f}"})
        risk.append({"sku":sku,"location_id":loc,"current_stock":a["last"],"avg_daily_demand":f"{avg:.2f}","safety_stock":f"{safety:.2f}","days_of_cover":f"{a['last']/avg:.2f}" if avg else "999.00","stockout_days":a["zero"],"risk_score":f"{score:.2f}","risk_band":band})
        variance.append({"sku":sku,"location_id":loc,"absolute_variance_units":a["variance"],"variance_events_over_1_unit":a["bad"],"system_units_counted":a["system"]})
        if band!="Low": action.append({"priority":band,"sku":sku,"location_id":loc,"recommended_action":"Expedite or transfer" if band=="High" else "Review reorder point","risk_score":f"{score:.2f}","accuracy_pct":f"{pct:.2f}"})
    months=defaultdict(lambda: [0,0])
    for r in snapshots: months[r["snapshot_date"][:7]][0]+=int(r["closing_quantity"]); months[r["snapshot_date"][:7]][1]+=int(int(r["closing_quantity"])<=0)
    monthly=[{"month":m,"total_closing_units":v[0],"stockout_observations":v[1]} for m,v in sorted(months.items())]
    quality=[]
    for name, rows, key in [("inventory_snapshot.csv",snapshots,["sku","location_id","snapshot_date"]),("transactions.csv",transactions,["sku","location_id","transaction_date"]),("cycle_counts.csv",counts,["sku","location_id","count_date"])]:
        duplicates=len(rows)-len({tuple(r[k] for k in key) for r in rows})
        nulls=sum(sum(not v for v in r.values()) for r in rows)
        quality.append({"file_name":name,"row_count":len(rows),"duplicate_key_count":duplicates,
                        "null_value_count":nulls,"status":"PASS" if not duplicates and not nulls else "WARN"})
    for name, rows in [("inventory_accuracy_summary.csv",accuracy),("stockout_risk_scores.csv",risk),("sku_location_action_queue.csv",sorted(action,key=lambda r:({"High":0,"Medium":1}[r["priority"]],-float(r["risk_score"])))),("inventory_variance_summary.csv",variance),("monthly_inventory_kpis.csv",monthly),("data_quality_checks.csv",quality)]: write(name,rows)
    print(json.dumps({"accuracy_pct":round(sum(float(r["accuracy_pct"]) for r in accuracy)/len(accuracy),2),"high_risk_pairs":sum(r["risk_band"]=="High" for r in risk),"outputs":6},indent=2))
if __name__=="__main__": main()
