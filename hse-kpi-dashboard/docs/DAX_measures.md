# DAX: calculated tables, columns and measures

Paste each block into Power BI Desktop (Modeling > New table / New column / New measure).
Create a table named `_Measures` (Enter Data, one blank column) and keep all measures there.

## Calculated tables and columns

```dax
Dim_Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2025, 1, 1 ), DATE ( 2026, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM yyyy" ),
    "Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
)
```

Mark `Dim_Date` as a date table (Table tools > Mark as date table > `Date`). Sort `Month` by `Month Sort`.

On `exposure_hours` (new column), so hours can be related to the date table:

```dax
Month Start = DATEVALUE ( exposure_hours[Month] & "-01" )
```

On `corrective_actions` (new columns), for ageing:

```dax
Days Overdue =
IF (
    corrective_actions[Status] = "Open" && corrective_actions[Due_Date] < DATE ( 2026, 9, 30 ),
    DATEDIFF ( corrective_actions[Due_Date], DATE ( 2026, 9, 30 ), DAY )
)

Overdue Bucket =
SWITCH (
    TRUE (),
    ISBLANK ( corrective_actions[Days Overdue] ), "Not overdue",
    corrective_actions[Days Overdue] <= 30, "1-30 days",
    corrective_actions[Days Overdue] <= 60, "31-60 days",
    corrective_actions[Days Overdue] <= 90, "61-90 days",
    "90+ days"
)
```

The data runs to 30 Sep 2026, so the "as of" date is fixed. For live data replace `DATE ( 2026, 9, 30 )` with `TODAY ()`.

## Relationships (all many-to-one, single direction)

| From (many) | To (one) |
|---|---|
| incidents[Location_ID] | locations[Location_ID] |
| audits[Location_ID] | locations[Location_ID] |
| exposure_hours[Location_ID] | locations[Location_ID] |
| findings[Audit_ID] | audits[Audit_ID] |
| incidents[Incident_Date] | Dim_Date[Date] |
| audits[Audit_Date] | Dim_Date[Date] |
| exposure_hours[Month Start] | Dim_Date[Date] |
| corrective_actions[Raised_Date] | Dim_Date[Date] |

`dq_report` stands alone (no relationships).

## Incident and safety measures

```dax
Total Incidents = COUNTROWS ( incidents )

Near Misses = CALCULATE ( [Total Incidents], incidents[Incident_Type] = "Near Miss" )

Lost Time Injuries = CALCULATE ( [Total Incidents], incidents[Incident_Type] = "Lost Time Injury" )

Recordable Cases =
CALCULATE ( [Total Incidents], incidents[Incident_Type] IN { "Lost Time Injury", "Medical Treatment" } )

Hours Worked = SUM ( exposure_hours[Hours_Worked] )

LTIFR = DIVIDE ( [Lost Time Injuries] * 1000000, [Hours Worked] )

Recordable Case Frequency = DIVIDE ( [Recordable Cases] * 1000000, [Hours Worked] )

Near Miss Ratio = DIVIDE ( [Near Misses], [Total Incidents] )

Incidents 3M Avg =
AVERAGEX (
    DATESINPERIOD ( Dim_Date[Date], MAX ( Dim_Date[Date] ), -3, MONTH ),
    CALCULATE ( [Total Incidents] )
)
```

LTIFR and the recordable case frequency are per 1,000,000 hours worked.
Recordable cases here = lost time injuries + medical treatment cases (the dataset has no restricted-work category).

## Audit and finding measures

```dax
Total Audits = COUNTROWS ( audits )

Audit Findings = COUNTROWS ( findings )

High Risk Findings = CALCULATE ( [Audit Findings], findings[Risk_Rating] = "High" )

High Risk Share = DIVIDE ( [High Risk Findings], [Audit Findings] )

Findings per Audit = DIVIDE ( [Audit Findings], [Total Audits] )
```

## Corrective action measures

```dax
Total Actions = COUNTROWS ( corrective_actions )

Open Actions = CALCULATE ( [Total Actions], corrective_actions[Status] = "Open" )

Closed Actions = CALCULATE ( [Total Actions], corrective_actions[Status] = "Closed" )

Close-out Rate = DIVIDE ( [Closed Actions], [Total Actions] )

Overdue Actions =
VAR AsOf = DATE ( 2026, 9, 30 )
RETURN
    CALCULATE (
        [Total Actions],
        FILTER ( corrective_actions, corrective_actions[Status] = "Open" && corrective_actions[Due_Date] < AsOf )
    )

Overdue % of Open = DIVIDE ( [Overdue Actions], [Open Actions] )

Valid Closed Actions =
CALCULATE ( [Total Actions], corrective_actions[Status] = "Closed", corrective_actions[DQ_Flag] = "" )

Closed On Time =
CALCULATE (
    [Total Actions],
    FILTER (
        corrective_actions,
        corrective_actions[Status] = "Closed"
            && corrective_actions[DQ_Flag] = ""
            && corrective_actions[Closed_Date] <= corrective_actions[Due_Date]
    )
)

On-Time Closure % = DIVIDE ( [Closed On Time], [Valid Closed Actions] )

Avg Days to Close =
AVERAGEX (
    FILTER ( corrective_actions, corrective_actions[Status] = "Closed" && corrective_actions[DQ_Flag] = "" ),
    DATEDIFF ( corrective_actions[Raised_Date], corrective_actions[Closed_Date], DAY )
)
```

Records flagged by the validation script (`DQ_Flag`) are excluded from the on-time and close-out-time measures, so bad dates do not distort the KPIs.

## Reference values (full period, no filters)

If your cards match these, your model is correct. They were computed independently in Python.

| Measure | Expected |
|---|---|
| Total Incidents | 240 |
| Near Misses | 118 |
| Lost Time Injuries | 4 |
| Hours Worked | 795,922 |
| LTIFR | 5.03 |
| Recordable Case Frequency | 40.2 |
| Total Actions | 304 |
| Open Actions | 65 |
| Overdue Actions | 51 (78.5% of open) |
| On-Time Closure % | 84.1% |
| Avg Days to Close | 26.7 |
| Close-out Rate | 78.6% |
