"""Validate the raw HSE data, log every issue found, and write cleaned tables.

Outputs:
  data/clean/*.csv          cleaned tables for Power BI
  data/clean/dq_report.csv  one row per check (what was tested, how many failed, what was done)
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

loc = pd.read_csv(RAW / "locations.csv")
exp = pd.read_csv(RAW / "exposure_hours.csv")
inc = pd.read_csv(RAW / "incidents.csv", parse_dates=["Incident_Date"])
aud = pd.read_csv(RAW / "audits.csv", parse_dates=["Audit_Date"])
fnd = pd.read_csv(RAW / "findings.csv")
act = pd.read_csv(RAW / "corrective_actions.csv", parse_dates=["Raised_Date", "Due_Date", "Closed_Date"])

report = []
def log(check, table, n_fail, n_total, action):
    report.append({"Check": check, "Table": table, "Records_Checked": n_total,
                   "Issues_Found": int(n_fail), "Action_Taken": action})

# 1. Duplicate incident IDs
d = inc.duplicated("Incident_ID", keep="first")
log("Duplicate Incident_ID", "incidents", d.sum(), len(inc), "Duplicate rows removed")
inc = inc[~d].copy()

# 2. Missing root cause
m = inc.Root_Cause.isna()
log("Missing Root_Cause", "incidents", m.sum(), len(inc), "Set to 'Not recorded' and flagged for follow-up")
inc["Root_Cause"] = inc.Root_Cause.fillna("Not recorded")

# 3. Location referential integrity
unknown = ~inc.Location_ID.isin(loc.Location_ID)
log("Location_ID not in locations", "incidents", unknown.sum(), len(inc), "Mapped to L00 'Unassigned'")
inc.loc[unknown, "Location_ID"] = "L00"
loc = pd.concat([loc, pd.DataFrame([("L00", "Unassigned", "Unknown", "Unknown")], columns=loc.columns)], ignore_index=True)

# 4. Incident dates inside reporting period
out = ~inc.Incident_Date.between("2025-01-01", "2026-09-30")
log("Incident date outside reporting period", "incidents", out.sum(), len(inc), "None needed" if out.sum() == 0 else "Review")

# 5. Closed before raised
bad = act.Closed_Date.notna() & (act.Closed_Date < act.Raised_Date)
log("Closed_Date before Raised_Date", "corrective_actions", bad.sum(), len(act), "Flagged; excluded from close-out time")

# 6. Closed without a date
nod = (act.Status == "Closed") & act.Closed_Date.isna()
log("Status Closed but Closed_Date missing", "corrective_actions", nod.sum(), len(act), "Flagged; excluded from close-out time")

act["DQ_Flag"] = ""
act.loc[bad, "DQ_Flag"] = "Closed before raised"
act.loc[nod, "DQ_Flag"] = "Closed without date"

# 7. Orphan audit findings
orph = ~fnd.Audit_ID.isin(aud.Audit_ID)
log("Finding without parent audit", "findings", orph.sum(), len(fnd), "None needed" if orph.sum() == 0 else "Review")

# 8. Overall duplicate keys elsewhere
for name, df, key in [("audits", aud, "Audit_ID"), ("findings", fnd, "Finding_ID"),
                      ("corrective_actions", act, "Action_ID")]:
    dd = df.duplicated(key).sum()
    log(f"Duplicate {key}", name, dd, len(df), "None needed" if dd == 0 else "Review")

for name, df in [("locations", loc), ("exposure_hours", exp), ("incidents", inc),
                 ("audits", aud), ("findings", fnd), ("corrective_actions", act)]:
    df.to_csv(CLEAN / f"{name}.csv", index=False, date_format="%Y-%m-%d")

rep = pd.DataFrame(report)
rep.to_csv(CLEAN / "dq_report.csv", index=False)
print(rep.to_string(index=False))
