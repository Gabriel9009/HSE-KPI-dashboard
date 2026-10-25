# Build guide: HSE and Compliance KPI Dashboard (Power BI Desktop)

Time needed: about 3 to 4 hours for a clean first version. Power BI Desktop is Windows-only.

## Step 1: Load the data (15 min)
1. Home > Get data > Text/CSV. Load all seven files from `data/clean/`: locations, exposure_hours, incidents, audits, findings, corrective_actions, dq_report.
2. In Power Query, check types: dates as Date, `Hours_Worked` as Whole number, everything else Text. Close and apply.
3. Tip: use Get data > Folder or set a parameter for the folder path so the dashboard refreshes when you replace the CSVs.

## Step 2: Model (20 min)
1. Create `Dim_Date`, `Month Start`, `Days Overdue`, `Overdue Bucket` from `DAX_measures.md`.
2. Build the relationships in the table in that file. Mark `Dim_Date` as the date table.
3. Create a `_Measures` table and paste in all measures.
4. Check the reference table at the bottom of `DAX_measures.md`. Do not build any visuals until your numbers match.

## Step 3: Pages (about 2 hours)

Use one consistent theme: a dark blue header band, one accent colour for "bad" (red/orange) and neutral greys. Put slicers (Year, Quarter, Location) in the same position on every page.

### Page 1: Executive Summary
- Cards: Total Incidents, LTIFR, Near Miss Ratio, Overdue % of Open, On-Time Closure %.
- Line chart: Total Incidents by `Dim_Date[Month]`, with `Incidents 3M Avg` as a second line.
- Stacked bar: incidents by Incident_Type.
- Table or matrix: location with Total Incidents, LTIFR, Open Actions, Overdue Actions.
- Text box titled "Key insights" with 3 bullet points. Write these yourself after you have looked at the numbers.

### Page 2: Incidents and Safety Performance
- Bar: incidents by Category. Donut or bar: incidents by Root_Cause (filter or highlight "Not recorded").
- Line: LTIFR by month. Column: incidents by Severity.
- Matrix: Location by Incident_Type.

### Page 3: Audits and Findings
- Cards: Total Audits, Audit Findings, High Risk Findings, High Risk Share.
- Bar: findings by Finding_Category, coloured by Risk_Rating.
- Column: findings per audit by Audit_Type.
- Table: location with Total Audits and Audit Findings.

### Page 4: Corrective Actions
- Cards: Open Actions, Overdue Actions, Close-out Rate, Avg Days to Close.
- Column chart: overdue actions by Overdue Bucket (ageing).
- Bar: Open and Overdue Actions by Owner_Department.
- Table: top overdue actions (Action_ID, Source_ID, Priority, Owner_Department, Days Overdue), sorted by Days Overdue descending.
- Use conditional formatting (red) on Days Overdue.

### Page 5: Data Quality
- Table from `dq_report`: Check, Table, Records_Checked, Issues_Found, Action_Taken.
- Cards: total issues found (sum of Issues_Found), checks run (count of rows).
- Short note: "Raw data was validated with `scripts/data_quality_checks.py` before loading. Flagged records are excluded from close-out time KPIs."

## Step 4: Polish (30 min)
- Rename every visual title to say what it shows. Set alt text on the main visuals.
- Align visuals to a grid, same fonts and colours throughout, hide the unused filter pane.
- Turn on Tooltips and Drill-through for Location if time allows.
- Test every slicer combination. Look for blanks and wrong totals.

## Step 5: Publish to GitHub (20 min)
1. Save the file as `HSE_KPI_Dashboard.pbix` into the repo root.
2. Export each page: File > Export > PDF, and save screenshots into `images/`.
3. Add the screenshots and a short "Key findings" section to `README.md`.
4. Create the repo on GitHub named `hse-kpi-dashboard`, push, and pin it on your profile.
   Large `.pbix` files are fine under 100 MB.

## Interview talking points
- Why synthetic data: real HSE data is confidential, and this lets you show the full workflow.
- The data-quality step: you found 40 problems in the raw files and handled each one before reporting.
- KPI definitions: LTIFR per million hours, overdue measured against an as-of date, close-out time excluding invalid dates.
- What you would do with real data: connect to SharePoint lists or an IMS export, schedule refresh, add role-based access.
