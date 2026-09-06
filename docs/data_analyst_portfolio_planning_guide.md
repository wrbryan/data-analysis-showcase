# Data Analyst Portfolio Planning Guide

## Purpose

Build a coherent set of polished portfolio projects that demonstrate the work employers expect from a Data Analyst: defining a business problem, preparing data, exploring patterns, building useful reporting, validating results, communicating findings, and recommending a measurable action.

The portfolio combines operations reporting, interactive dashboards, notebook workflows, public-data analysis, and business-facing data products.

## Portfolio Goal

Create a small set of interview-ready projects with different analytical surfaces rather than many generic dashboards.

1. Inventory Accuracy & Stockout Risk Dashboard
2. Warehouse Throughput & Labor Utilization Dashboard
3. CMMS Maintenance & Work-Order Analytics Dashboard

The broader repository also includes five completed or in-progress projects that
demonstrate additional data-analysis workflows. Their walkthroughs are included
below so every project in `projects/` has a clear business purpose, workflow,
and review path.

## Target Skills to Demonstrate

- Excel or Google Sheets: cleaning, formulas, validation checks, pivot tables, KPI models
- SQL: joins, aggregations, CTEs, date logic, ranking, exception reporting
- Power BI or Tableau: dashboard design, drilldowns, trend analysis, filters, executive reporting
- Python: optional data cleaning, exploratory analysis, forecasting, reproducible workflows
- Operations analysis: inventory, throughput, labor, backlog, service levels, maintenance, root-cause analysis
- Business communication: recommendations, impact estimates, limitations, and pilot plans

---

# Inventory Accuracy & Stockout Risk — Operations Reporting Case Study

## Business scenario

A distribution center has recurring inventory adjustments, stockouts, excess inventory, and inconsistent cycle-count results. Operations leadership needs to identify the products, locations, shifts, suppliers, and categories that create the largest financial and service risk.

## Core business question

How can the operation reduce inventory variance and stockout risk while focusing cycle-count resources on the highest-impact items?

## Questions to answer

- What is the overall inventory-record accuracy rate?
- Which SKUs have the highest quantity variance and dollar-value variance?
- Which locations, warehouse zones, shifts, or product categories create the largest adjustments?
- Which SKUs are at stockout risk based on on-hand quantity, demand, lead time, reorder points, and safety stock?
- Which items are slow-moving, obsolete, or overstocked?
- Which SKUs and locations should receive priority cycle counts?

## Suggested data tables

### inventory_snapshot

| Field | Description |
|---|---|
| snapshot_date | Date inventory was recorded |
| sku | Stock keeping unit |
| location | Warehouse/bin/location identifier |
| system_qty | Quantity recorded in the system |
| physical_qty | Counted physical quantity |
| unit_cost | Unit cost of the SKU |

### product_master

| Field | Description |
|---|---|
| sku | Stock keeping unit |
| description | Product description |
| category | Product category |
| supplier | Primary supplier |
| lead_time_days | Supplier lead time |
| reorder_point | Replenishment trigger quantity |
| safety_stock | Buffer inventory quantity |

### transactions

| Field | Description |
|---|---|
| transaction_date | Date of inventory transaction |
| sku | Stock keeping unit |
| transaction_type | Receipt, pick, adjustment, transfer, return, etc. |
| quantity | Transaction quantity |
| shift | Shift or processing period |
| location | Warehouse/bin/location identifier |

### orders

| Field | Description |
|---|---|
| order_id | Unique order identifier |
| order_date | Date order was placed or released |
| sku | Stock keeping unit |
| ordered_qty | Requested quantity |
| shipped_qty | Quantity shipped |
| promised_date | Customer promise date |
| ship_date | Actual shipment date |

### cycle_counts

| Field | Description |
|---|---|
| count_id | Unique count identifier |
| count_date | Date of count |
| sku | Stock keeping unit |
| location | Warehouse/bin/location identifier |
| counter | Counter or team identifier |
| variance_qty | Quantity variance found |
| recount_flag | Whether a recount was required |

## Key KPIs

| KPI | Calculation |
|---|---|
| Inventory accuracy | 1 - abs(System Quantity - Physical Quantity) / Physical Quantity |
| Adjustment value | abs(System Quantity - Physical Quantity) x Unit Cost |
| Stockout rate | Stockout Events / Total SKUs or Order Lines x 100 |
| Inventory turnover | Cost of Goods Sold / Average Inventory Value |
| Days of supply | On-hand Inventory / Average Daily Demand |
| Cycle-count completion | Completed Counts / Scheduled Counts x 100 |

## Dashboard pages

1. Executive overview: inventory accuracy, adjustment value, stockout-risk SKUs, inventory value, and priority actions.
2. Variance analysis: adjustment value by SKU, category, location, shift, and transaction type.
3. Stockout and excess risk: on-hand quantity, reorder point, safety stock, days of supply, demand trend, and supplier lead time.
4. Cycle-count performance: scheduled versus completed counts, recounts, variance trends, and high-risk count locations.
5. Action tracker: recommended action, owner, priority, expected impact, target date, and current status.

## Recommended analysis steps

1. Validate SKU, location, date, and quantity fields.
2. Calculate absolute quantity variance and dollar variance.
3. Rank SKUs by adjustment value and recurring variance frequency.
4. Identify low-on-hand SKUs using reorder point, safety stock, and demand measures.
5. Segment items into high-value/high-risk, high-value/low-risk, low-value/high-risk, and low-value/low-risk groups.
6. Recommend a risk-based cycle-count schedule.

## Example final recommendation

Prioritize weekly cycle counts for the 20 percent of SKUs responsible for most adjustment value. Create a location-level exception review for high-variance bins and require a recount/approval workflow for adjustments above a defined dollar threshold.

---

# Warehouse Throughput & Labor Utilization — Operations Reporting Case Study

## Business scenario

A warehouse is missing ship-by deadlines during peak periods. Leadership needs to determine whether the main cause is staffing, workload volume, order complexity, replenishment delays, picking performance, packing congestion, or carrier cutoff timing.

## Core business question

Which operational conditions drive late shipments and backlog, and what staffing or process change should be tested first?

## Questions to answer

- How many orders, lines, units, and pallets are processed by day, hour, shift, and department?
- Which workflow step has the lowest throughput or largest queue?
- When do productivity, backlog, or on-time shipment results decline?
- Are late orders linked to order size, product category, staffing level, warehouse zone, shift, or carrier cutoff?
- How many labor hours are needed to meet volume and service-level targets?
- Where is the primary operational bottleneck?

## Suggested data tables

### orders

| Field | Description |
|---|---|
| order_id | Unique order identifier |
| release_time | Time order entered the fulfillment queue |
| promised_ship_date | Required ship date/time |
| ship_time | Actual ship date/time |
| order_lines | Number of order lines |
| unit_count | Number of units |
| pallet_count | Number of pallets |
| priority | Customer or operational priority |
| zone | Warehouse zone |
| carrier | Carrier/service type |

### labor_hours

| Field | Description |
|---|---|
| work_date | Work date |
| shift | Shift identifier |
| department | Receiving, putaway, replenishment, picking, packing, shipping |
| scheduled_hours | Planned labor hours |
| worked_hours | Actual labor hours |
| overtime_hours | Overtime labor hours |
| headcount | Associates working |

### process_events

| Field | Description |
|---|---|
| order_id | Unique order identifier |
| process_step | Receiving, picking, packing, staging, shipping, etc. |
| start_time | Step start time |
| end_time | Step end time |
| status | Completed, delayed, exception, rework |
| exception_code | Delay/error category |

### exceptions

| Field | Description |
|---|---|
| exception_id | Unique exception identifier |
| event_time | Time of exception |
| order_id | Related order |
| exception_type | Short pick, damage, system issue, replenishment delay, etc. |
| shift | Shift identifier |
| zone | Warehouse zone |
| resolved_time | Time issue was resolved |

## Key KPIs

- Orders processed per labor hour
- Units picked per labor hour
- Lines picked per hour
- Receiving dock-to-stock time
- Order cycle time: order released to shipment
- On-time shipment rate
- Backlog volume and backlog aging
- Overtime percentage
- Error, damage, or rework rate
- Labor utilization by department and shift

## Dashboard pages

1. Executive overview: volume, on-time shipment rate, backlog, labor hours, overtime, and primary issue.
2. Throughput trends: orders, lines, units, and pallets by hour, day, shift, zone, and department.
3. Labor analysis: productivity by shift, department, workload band, and staffing level.
4. Process flow analysis: cycle time at receiving, putaway, replenishment, picking, packing, staging, and shipping.
5. Exceptions and action plan: late-order drivers, root-cause categories, owners, and pilot measures.

## Process map

Receiving -> Putaway -> Replenishment -> Picking -> Packing -> Staging -> Shipping

Measure time, queue size, volume, and exceptions at every stage. The stage with the highest queue, longest delay, or greatest association with late orders is a candidate bottleneck.

## Recommended analysis steps

1. Create a timestamp-based process-cycle-time table.
2. Flag late shipments based on promised versus actual ship time.
3. Compare labor hours, workload, and productivity by shift and department.
4. Analyze exception frequency and resolution time.
5. Identify the operational factors most associated with late shipments.
6. Propose a pilot staffing or workflow intervention and define success metrics.

## Example final recommendation

Move two cross-trained associates to replenishment from 1:00 PM to 4:00 PM during high-volume days. Replenishment delays occur before the largest increase in late picks and backlog. Pilot the adjustment for four weeks and measure on-time shipment, backlog aging, and lines picked per labor hour.

---

# CMMS Maintenance & Work-Order Analytics — Operations Reporting Case Study

## Business scenario

A manufacturing, industrial, or facilities team has growing work-order backlog, frequent unplanned downtime, and inconsistent preventive-maintenance completion. Management needs a recurring KPI dashboard and a work-prioritization method.

## Core business question

How can the maintenance team reduce backlog, downtime, and reactive work while protecting preventive-maintenance capacity for critical assets?

## Questions to answer

- How many work orders are open, completed, overdue, and aging?
- What share of work is preventive, corrective, emergency, planned, or reactive?
- Which assets, locations, or failure codes create the most downtime and cost?
- Are preventive-maintenance tasks completed on time?
- Which teams, shifts, or vendors have the longest response and completion times?
- Which open work orders should be prioritized based on asset criticality, safety, downtime risk, and age?

## Suggested data tables

### work_orders

| Field | Description |
|---|---|
| wo_id | Unique work-order identifier |
| created_date | Work-order creation date/time |
| due_date | Required completion date/time |
| start_date | Labor start date/time |
| completed_date | Completion date/time |
| status | Open, in progress, complete, deferred, cancelled |
| priority | Priority category |
| work_type | PM, corrective, emergency, inspection, etc. |
| asset_id | Related asset |
| estimated_hours | Estimated labor hours |
| actual_hours | Actual labor hours |
| labor_cost | Labor cost |

### assets

| Field | Description |
|---|---|
| asset_id | Unique asset identifier |
| asset_name | Asset name |
| asset_class | Equipment type/class |
| location | Asset location |
| criticality | Business/safety criticality rating |
| install_date | Installation date |

### downtime_events

| Field | Description |
|---|---|
| event_id | Unique event identifier |
| asset_id | Related asset |
| start_time | Downtime start |
| end_time | Downtime end |
| downtime_hours | Total downtime duration |
| failure_code | Failure reason/category |

### maintenance_labor

| Field | Description |
|---|---|
| technician_id | Technician identifier |
| team | Maintenance team |
| shift | Shift identifier |
| available_hours | Available work hours |
| worked_hours | Worked hours |

### parts_usage

| Field | Description |
|---|---|
| wo_id | Related work order |
| part_id | Part identifier |
| quantity | Quantity used |
| unit_cost | Unit cost |
| supplier | Supplier |
| lead_time_days | Part lead time |

## Key KPIs

| KPI | Meaning |
|---|---|
| Work-order completion rate | Completed work orders / total due work orders |
| On-time completion rate | Work orders completed by due date / work orders due |
| Backlog hours | Estimated labor hours for unfinished work orders |
| Average response time | Time from work-order creation to labor start |
| Mean time to repair (MTTR) | Average time needed to restore an asset after failure |
| Mean time between failures (MTBF) | Average operating time between failures |
| PM compliance | Preventive-maintenance tasks completed by due date |
| Planned vs. unplanned ratio | Scheduled work share compared with reactive work share |
| Downtime by asset | Total downtime attributable to each asset or asset class |

## Dashboard pages

1. Executive overview: open work orders, overdue work, backlog hours, PM compliance, downtime, and top risk assets.
2. Work-order backlog: aging, priority, status, work type, and labor-hour workload.
3. Asset reliability: downtime, MTTR, MTBF, failure code, and asset criticality.
4. Preventive maintenance: schedule compliance, late PMs, PM-to-reactive-work ratio, and critical-asset coverage.
5. Prioritization and action tracker: work-order risk score, recommended owner, due date, and expected impact.

## Prioritization model

Create a transparent score from factors such as:

- Asset criticality
- Safety or compliance impact
- Work-order priority
- Work-order age
- Downtime impact
- Recurring failure history
- Availability of parts

Clearly label this as a planning model, not an official maintenance-risk procedure.

## Recommended analysis steps

1. Standardize work-order statuses and work-type categories.
2. Calculate response time, completion time, due-date compliance, and backlog age.
3. Separate planned work from reactive and emergency work.
4. Join work orders to assets, downtime events, labor, and parts data.
5. Rank assets and failure codes by downtime, maintenance cost, repeat incidents, and criticality.
6. Create a work-order prioritization score and propose capacity protections for critical PM work.

## Example final recommendation

Protect weekly preventive-maintenance capacity for critical assets, establish escalation thresholds for work orders open longer than 14 days, and review the highest-downtime failure codes monthly. The intended result is less reactive maintenance, reduced backlog, and lower operational downtime.

---

# Additional Project Walkthroughs

## Athlete Events — Interactive Participation Explorer

### Purpose

Explore athlete participation and medal-related patterns across Olympic-style
event data. This project demonstrates how a public dataset can become a
filterable browser-based analysis rather than a static chart.

### Core questions

- Which countries, sports, seasons, and events have the highest participation?
- How do athlete demographics and medal outcomes vary across filters?
- Can a user move from an overview to a focused comparison without rerunning
  the analysis?

### Existing implementation

- Entrypoint: `projects/athlete_events/athlete_events.py`
- Interface: Dash with reusable layout and callback components.
- Supporting assets: `components/` and `assets/styles.css`.
- Setup: `projects/athlete_events/setup.sh`.

### Walkthrough

1. Start with the README and setup script to reproduce the local Dash app.
2. Inspect the layout components to see how the page is divided into analysis
    views.
3. Trace callback inputs and outputs to understand how filters update charts.
4. Review the CSS and component boundaries as evidence of reusable dashboard
    structure.
5. Use the project to discuss interactive exploration, callback design, and
    communicating patterns in public data.

### Portfolio takeaway

This project demonstrates interactive dashboard architecture, public-data
exploration, and the translation of user selections into updated evidence.

## Car Sales — Interactive Sales and Specification Dashboard

### Purpose

Compare vehicle sales, pricing, performance, and fuel-efficiency attributes in
an interactive Dash application. The project is useful for demonstrating a
business-facing filter workflow with multiple chart types.

### Core questions

- Which manufacturers and models lead sales?
- How do horsepower, fuel efficiency, and pricing relate?
- How does the selected manufacturer or model set change the visible evidence?

### Existing implementation

- Entrypoint: `projects/car-sales/car_sales_app.py`
- Utilities: `projects/car-sales/util_car.py`
- Source data: `projects/car-sales/Car_sales.csv`
- Visual components: `projects/car-sales/components_car/`.
- Narrative artifacts: `post.md` and `SUMMARY.md`.

### Walkthrough

1. Install the project requirements described in the README.
2. Start the Dash app and inspect the manufacturer and model dropdowns.
3. Compare the sales pie, vertical bar, horizontal bar, and specification
    scatter views.
4. Use the filters to move from a market overview to a model-level question.
5. Review the utility and component files to explain how data preparation and
    visualization responsibilities are separated.

### Portfolio takeaway

This project demonstrates interactive filtering, reusable chart components,
and concise communication of sales and product-specification patterns.

## DuckDB CSV GUI — Notebook Analytics Workflow

### Purpose

Turn uploaded CSV files into a lightweight relational analytics workflow using
DuckDB and notebooks. The focus is the workflow itself: inspect schemas,
approve relationships, query data, and produce report-ready views.

### Core questions

- How can a user move from several raw CSVs to a usable analytical model?
- Which relationships are plausible and should be approved?
- Can SQL results be inspected, visualized, and shared without a full backend?

### Existing implementation

- Core logic: `projects/duckdb-csv-gui/duckdb_csv_gui.py`
- Local notebook: `duckdb_csv_gui.ipynb`
- Colab notebook: `duckdb_csv_gui_colab.ipynb`
- Requirements: `projects/duckdb-csv-gui/requirements.txt`
- Reports: `projects/duckdb-csv-gui/reports/`.

### Walkthrough

1. Install the notebook requirements and open the local or Colab notebook.
2. Upload sample CSV files and inspect inferred schemas.
3. Review proposed relationships before approving them.
4. Run SQL against the DuckDB tables and inspect the result inline.
5. Generate a simple chart or export a query result to demonstrate the path
    from raw files to a shareable analysis.

### Portfolio takeaway

This project demonstrates lightweight data modeling, schema inspection,
interactive relationship review, SQL exploration, and notebook-based delivery.

## Heart Disease — Interactive Clinical Feature Explorer

### Purpose

Explore relationships between demographic, symptom, vital, laboratory, and
heart-disease outcome fields through an interactive Dash dashboard. This is a
public-data demonstration and not a clinical decision tool.

### Core questions

- How do disease outcomes vary by sex and chest-pain category?
- How do cholesterol and maximum heart-rate patterns differ across groups?
- What relationships can be explored through filtered distributions and
  scatterplots?

### Existing implementation

- Entrypoint: `projects/heart-disease/heart_analysis_app.py`
- Utility module: `projects/heart-disease/util_heart.py`
- Source data: `projects/heart-disease/heart.csv`
- Visual components: `projects/heart-disease/components_heart/`.

### Walkthrough

1. Install the documented Dash dependencies and start the application.
2. Filter by sex and chest-pain type to establish subgroup comparisons.
3. Review disease outcome counts, average cholesterol, and average maximum
    heart rate.
4. Use the age-versus-cholesterol scatterplot to discuss association without
    presenting it as causation or medical advice.
5. Inspect the component modules to show how the dashboard separates controls,
    chart construction, and layout.

### Portfolio takeaway

This project demonstrates responsible public-data visualization, subgroup
filtering, reusable dashboard components, and clear limits on interpretation.

## Excel-only Analysis — Business Reporting Workspace

### Purpose

Provide a business-facing analysis and dashboard workspace for operational
trends and exceptions using Excel artifacts. This project is a spreadsheet
reporting surface, distinct from the Python-generated Inventory Accuracy &
Stockout Risk reporting package.

### Core questions

- Which operational trends or exceptions need management attention?
- Can the workbook present a clear decision, supporting evidence, and a short
  narrative for business users?
- Which calculations, controls, and visuals should be refreshed together?

### Existing implementation

- Workbook artifacts: `projects/excel-only-analysis/`.
- Project guide: `README.md`.
- Summary and narrative: `SUMMARY.md` and `post.md`.
- Included workbooks cover inventory reconciliation, operations KPIs, and
  reporting automation examples.

### Walkthrough

1. Start with the project README and summary to understand the intended
    business question and workbook scope.
2. Open the relevant workbook and identify source tabs, calculation areas,
    KPI views, and exception outputs.
3. Trace a headline KPI back to its source fields and supporting table.
4. Review the dashboard layout for readable decision cues, not just chart
    variety.
5. Use the project to discuss spreadsheet controls, recurring reporting, and
    handoff to business users.

### Portfolio takeaway

This project demonstrates Excel-based reporting, operational KPI communication,
and the practical constraints of maintaining business-facing workbooks.

## Additional Project Options

## Vendor and purchase-order performance

Analyze supplier lead times, late deliveries, receipt discrepancies, price variance, defects, fill rate, and spend concentration.

Business question: Which suppliers create the most operational disruption, and where should procurement focus corrective action?

## Inventory replenishment and demand forecast

Forecast weekly demand by SKU or category, compare forecasts with actual demand, and recommend reorder points and safety-stock levels.

Business question: How can the business reduce stockouts without unnecessarily tying up working capital?

## Cost-to-serve analysis

Analyze the operating cost of serving customers, regions, products, facilities, or order types.

Business question: Which customers or products appear profitable by revenue but incur unusually high fulfillment, freight, return, or labor costs?

## Quality, rework, and defect analysis

Analyze quality inspections, defects, rework, production data, supplier issues, or equipment-related failures.

Business question: What drives defect costs, and which corrective action should be tested first?

## Capacity planning model

Forecast workload and estimate staffing requirements using order volume, lines, units, productivity standards, absenteeism, overtime constraints, and service-level targets.

Business question: How many labor hours and associates are needed to meet projected demand without excessive overtime?

## Service-level agreement performance

Analyze tickets, internal requests, customer orders, or service tasks against promised response and completion targets.

Business question: Where are SLA misses occurring, what drives response delays, and what workflow change could improve compliance?

---

# Required Deliverables for Every Project

## 1. Business problem statement

Write one sentence that explains the decision the analysis supports.

Example: Late shipments have increased, but leadership lacks visibility into the workflow stage, shift, and workload condition responsible for the delay.

## 2. Data dictionary

Define every table, field, metric, data type, grain, source assumption, and known limitation.

## 3. Data preparation evidence

Show raw-data assumptions, cleaning steps, quality checks, SQL transformations, formulas, or Python workflow.

## 4. Dashboard

Create an executive overview plus pages for trends, drivers, exceptions, and actions. Avoid decorative visuals that do not support a decision.

## 5. Insight narrative

Write three to five findings supported by evidence. Do not only describe charts.

## 6. Recommendation and pilot plan

Specify the action, accountable owner, pilot duration, affected process, success metric, expected impact, and review date.

## 7. Impact estimate

Estimate value in labor hours, inventory dollars, service level, cost, capacity, or risk reduction. Clearly state any assumption or use of synthetic data.

---

# Publishing Structure

Use a GitHub repository or a Notion case-study page. A suggested repository layout is below.

```text
operations-portfolio-project/
|
|-- README.md
|-- data/
|   |-- raw_data.csv
|   `-- cleaned_data.csv
|-- sql/
|   `-- operations_analysis.sql
|-- python/
|   `-- cleaning_and_analysis.ipynb
|-- dashboard/
|   `-- dashboard_screenshots.pdf
|-- presentation/
|   `-- executive_briefing.pdf
`-- documentation/
    `-- data_dictionary.xlsx
```

## README outline

1. Project title
2. Business problem
3. Business questions
4. Dataset and data limitations
5. Tools used
6. Data-cleaning approach
7. KPI definitions
8. Key findings
9. Recommendations and impact estimate
10. Dashboard preview
11. Files and reproducibility instructions

---

# Data and Confidentiality Rules

- Use synthetic data, public data, or fully anonymized and authorized data.
- Do not publish employer-confidential records, internal names, customer data, pricing, account information, security-sensitive information, or unpublished operational metrics.
- State that any synthetic scenario is a simulation created for portfolio demonstration.
- Keep project narratives realistic without identifying a current or former employer.

---

# 90-Day Project Plan

## Month 1: Inventory Accuracy & Stockout Risk

- Week 1: Define scenario, build/find data, create a data dictionary, and plan KPIs.
- Week 2: Clean data in Excel, SQL, or Python; validate totals and create calculated fields.
- Week 3: Build the inventory-risk dashboard and analyze top adjustment drivers.
- Week 4: Create an executive brief, publish the README, and document recommendations.

## Month 2: Warehouse Throughput & Labor Utilization

- Week 5: Design process map and create order, labor, and process-event tables.
- Week 6: Calculate process cycle times, late-order flags, workload, backlog, and labor productivity.
- Week 7: Build dashboard pages for throughput, labor, bottlenecks, and exceptions.
- Week 8: Write a pilot recommendation with metrics and an impact estimate.

## Month 3: CMMS Work-Order Analytics

- Week 9: Build work-order, asset, downtime, labor, and parts datasets.
- Week 10: Calculate backlog, aging, PM compliance, response time, completion time, downtime, MTTR, and MTBF.
- Week 11: Build a maintenance KPI dashboard and prioritization model.
- Week 12: Create a five-slide executive briefing, finish documentation, and publish the case study.

---

# Final Quality Checklist

Before publishing each project, confirm all items below.

- [ ] The business question is clear and operationally realistic.
- [ ] Data fields and assumptions are documented.
- [ ] Calculations are reproducible and validated.
- [ ] Dashboard titles state the insight or decision, not just the chart type.
- [ ] There are three to five evidence-based findings.
- [ ] The recommendation is specific, measurable, and feasible.
- [ ] Assumptions and limitations are disclosed.
- [ ] No confidential employer data is included.
- [ ] The README is readable in under five minutes.
- [ ] The project includes an executive-ready summary or slide deck.

# Recommended Sequence

Start with Inventory Accuracy & Stockout Risk. It is the strongest direct fit for inventory-control experience, provides a compelling way to demonstrate Excel, SQL, visualization, and operational judgment, and can be completed with synthetic data if needed. Then build Warehouse Throughput & Labor Utilization, followed by CMMS Work-Order Analytics for a differentiated maintenance/operations specialization.
