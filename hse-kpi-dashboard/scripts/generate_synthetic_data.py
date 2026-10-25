"""Generate SYNTHETIC HSE / compliance data for the Power BI dashboard.

All data is fictional. Names, vessels and figures do not describe any real
company. A few data-quality problems are injected on purpose so the
validation step (scripts/data_quality_checks.py) has realistic work to do.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

START, END = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-09-30")
months = pd.period_range(START, END, freq="M")

locations = pd.DataFrame([
    ("L01", "MV Atlantic Star",   "Vessel", "Marine Operations"),
    ("L02", "MV Delta Pioneer",   "Vessel", "Marine Operations"),
    ("L03", "MV Coastal Venture", "Vessel", "Marine Operations"),
    ("L04", "MV Bonny Spirit",    "Vessel", "Marine Operations"),
    ("L05", "Port Harcourt Office", "Shore", "Corporate"),
    ("L06", "Onne Base",          "Shore", "Technical"),
], columns=["Location_ID", "Location_Name", "Location_Type", "Department"])

rows = []
for m in months:
    for _, l in locations.iterrows():
        base = 8200 if l.Location_Type == "Vessel" else 2600
        rows.append((str(m), l.Location_ID, int(rng.normal(base, base * 0.06))))
exposure = pd.DataFrame(rows, columns=["Month", "Location_ID", "Hours_Worked"])

inc_types = ["Near Miss", "First Aid", "Medical Treatment", "Lost Time Injury",
             "Property Damage", "Environmental Release"]
inc_p = [0.52, 0.21, 0.10, 0.012, 0.14, 0.018]
categories = ["Slips, Trips and Falls", "Mooring and Deck Ops", "Engine Room",
              "Lifting Operations", "Chemical Handling", "Driving and Transport",
              "Housekeeping", "Fire and Emergency"]
causes = ["Procedure not followed", "Inadequate risk assessment", "Equipment failure",
          "Poor housekeeping", "Lack of training", "Communication breakdown",
          "Fatigue", "Weather / sea state"]
n_inc = 240
dates = START + pd.to_timedelta(rng.integers(0, (END - START).days + 1, n_inc), unit="D")
incidents = pd.DataFrame({
    "Incident_Date": dates,
    "Location_ID": rng.choice(locations.Location_ID, n_inc, p=[.22, .22, .2, .2, .08, .08]),
    "Incident_Type": rng.choice(inc_types, n_inc, p=inc_p),
    "Category": rng.choice(categories, n_inc),
    "Root_Cause": rng.choice(causes, n_inc),
}).sort_values("Incident_Date").reset_index(drop=True)
incidents.insert(0, "Incident_ID", [f"INC-{i:04d}" for i in range(1, n_inc + 1)])
incidents["Severity"] = incidents.Incident_Type.map({
    "Near Miss": "Low", "First Aid": "Low", "Medical Treatment": "Medium",
    "Lost Time Injury": "High", "Property Damage": "Medium",
    "Environmental Release": "High"})
incidents["Days_Lost"] = np.where(incidents.Incident_Type == "Lost Time Injury",
                                  rng.integers(1, 21, n_inc), 0)

audit_types = ["Internal Audit", "External Audit", "Vessel Inspection",
               "Vetting Inspection", "HSE Observation"]
n_aud = 60
adates = START + pd.to_timedelta(rng.integers(0, (END - START).days + 1, n_aud), unit="D")
audits = pd.DataFrame({
    "Audit_Date": adates,
    "Location_ID": rng.choice(locations.Location_ID, n_aud),
    "Audit_Type": rng.choice(audit_types, n_aud, p=[.25, .1, .3, .15, .2]),
}).sort_values("Audit_Date").reset_index(drop=True)
audits.insert(0, "Audit_ID", [f"AUD-{i:03d}" for i in range(1, n_aud + 1)])

find_cats = ["Documentation and Records", "Safety Equipment", "Navigation and Bridge",
             "Pollution Prevention", "Crew Competence", "Maintenance", "Emergency Preparedness"]
frows, fid = [], 1
for _, a in audits.iterrows():
    for _ in range(int(rng.integers(0, 7))):
        frows.append((f"FND-{fid:04d}", a.Audit_ID, rng.choice(find_cats),
                      rng.choice(["Low", "Medium", "High"], p=[.5, .35, .15])))
        fid += 1
findings = pd.DataFrame(frows, columns=["Finding_ID", "Audit_ID", "Finding_Category", "Risk_Rating"])

act, aid = [], 1
def add_action(src_type, src_id, raised, risk):
    global aid
    sla = {"High": 14, "Medium": 30, "Low": 60}[risk]
    due = raised + pd.Timedelta(days=sla)
    r = rng.random()
    if r < 0.68:
        closed = raised + pd.Timedelta(days=int(rng.integers(3, sla + 1)))
    elif r < 0.82:
        closed = due + pd.Timedelta(days=int(rng.integers(1, 40)))
    else:
        closed = pd.NaT
    if pd.notna(closed) and closed > END:
        closed = pd.NaT
    status = "Closed" if pd.notna(closed) else "Open"
    act.append((f"CA-{aid:04d}", src_type, src_id, raised, due, closed, status, risk,
                rng.choice(["Marine Operations", "Technical", "HSEQ", "Crewing", "Corporate"])))
    aid += 1

for _, i in incidents.iterrows():
    if i.Severity in ("Medium", "High") or rng.random() < 0.25:
        add_action("Incident", i.Incident_ID, i.Incident_Date + pd.Timedelta(days=int(rng.integers(1, 6))), i.Severity)
fa = findings.merge(audits[["Audit_ID", "Audit_Date"]], on="Audit_ID")
for _, f in fa.iterrows():
    add_action("Audit Finding", f.Finding_ID, f.Audit_Date + pd.Timedelta(days=int(rng.integers(1, 8))), f.Risk_Rating)
actions = pd.DataFrame(act, columns=["Action_ID", "Source_Type", "Source_ID", "Raised_Date",
                                     "Due_Date", "Closed_Date", "Status", "Priority", "Owner_Department"])
actions = actions[actions.Raised_Date <= END].reset_index(drop=True)

# Intentional data-quality problems (documented in README)
dup = incidents.sample(8, random_state=1)
incidents = pd.concat([incidents, dup], ignore_index=True)
incidents.loc[incidents.sample(14, random_state=2).index, "Root_Cause"] = np.nan
incidents.loc[incidents.sample(5, random_state=3).index, "Location_ID"] = "L99"
bad = actions[actions.Status == "Closed"].sample(7, random_state=4).index
actions.loc[bad, "Closed_Date"] = actions.loc[bad, "Raised_Date"] - pd.Timedelta(days=3)
nodate = actions[actions.Status == "Closed"].drop(bad).sample(6, random_state=5).index
actions.loc[nodate, "Closed_Date"] = pd.NaT

for name, df in [("locations", locations), ("exposure_hours", exposure), ("incidents", incidents),
                 ("audits", audits), ("findings", findings), ("corrective_actions", actions)]:
    df.to_csv(OUT / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    print(f"{name}: {len(df)} rows")
