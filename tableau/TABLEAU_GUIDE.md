# Build the Tableau dashboard (about 30-40 minutes)

Use Tableau Public (free): https://public.tableau.com/app/discover  -> "Create" -> "Web Authoring", or Tableau Public Desktop.
Data file: `telco_churn_tableau.csv` (7,043 rows).

## 1. Connect
Connect > Text file > select `telco_churn_tableau.csv` > open "Sheet 1".
Check in the Data pane: `ChurnFlag`, `MonthlyCharges`, `tenure`, `AddOnCount`, `ChurnProbability` should be numbers (#). `Contract`, `Segment`, `RiskTier` etc. should be text (Abc).

## 2. Calculated fields (Analysis > Create Calculated Field)
- **Churn Rate** = `AVG([ChurnFlag])`  -> right-click > Default Properties > Number Format > Percentage, 1 decimal
- **Revenue Lost** = `IF [ChurnFlag]=1 THEN [MonthlyCharges] END` -> Number Format > Currency, 0 decimals
- **Customers** = `COUNTD([customerID])`

## 3. Sheets (rename each sheet at the bottom tab)
1. **Churn by Contract**: Contract to Rows, Churn Rate to Columns. Drag Churn Rate onto Color and Label. Sort descending (toolbar sort icon).
2. **Churn by Tenure**: TenureGroup to Rows, Churn Rate to Columns, Color + Label. Right-click TenureGroup > Sort > Manual: 0-12 mo, 13-24 mo, 25-48 mo, 49-72 mo.
3. **Churn by Payment Method**: PaymentMethod to Rows, Churn Rate to Columns, Color + Label, sort descending.
4. **Revenue Lost by Segment**: Segment to Rows, Revenue Lost to Columns, Color + Label, sort descending. This is your headline chart (month-to-month fiber = about 72%).
5. **Heatmap**: Contract to Rows, InternetService to Columns, Mark type = Square, Churn Rate to Color (red palette) and to Label. Make squares bigger with the Size slider.
6. **Churn by Risk Tier**: RiskTier to Rows, Churn Rate to Columns, Label. Sort manually: High, Medium, Low.
7. **KPIs** (3 small sheets or one): 
   - `Churn Rate` as text (drag to Text, no dimensions) -> 26.5%
   - `Revenue Lost` as text -> $139,131
   - `Customers` as text -> 7,043

Tip: use the same two colours everywhere (dark blue = normal, red = high churn) so the dashboard reads quickly.

## 4. Dashboard
1. New Dashboard (tab at the bottom, grid icon). Size: Automatic or Range (min 1200 x 800).
2. Drag a Horizontal container to the top and put the 3 KPI sheets in it.
3. Below, add Revenue Lost by Segment (wide), then a row with Contract, Tenure and Payment Method, then the Heatmap and Risk Tier.
4. Add a title: "Customer churn: where are we losing revenue?"
5. Add a text box with a one-line takeaway: "Month-to-month fiber customers are 30% of the base but 72% of lost revenue."
6. Click each chart and enable "Use as Filter" (funnel icon) so clicking a bar filters the rest.
7. Add filters: right-click the data pane > drag Contract, InternetService, SeniorCitizen onto the dashboard as quick filters (Apply to Worksheets > All Using This Data Source).

## 5. Publish
File > Save to Tableau Public (or Publish in web authoring), set it to public, copy the URL. Put the link in your resume and at the top of the GitHub README.

## Common issues
- Bars show counts instead of percentages: Churn Rate was not created as `AVG([ChurnFlag])` or number format is not set.
- Sheet has a blue pill and a green pill swapped: right-click a pill > "Dimension"/"Measure" or "Discrete"/"Continuous" to switch.
- Tenure group order is alphabetical: sort manually (step 3.2).
