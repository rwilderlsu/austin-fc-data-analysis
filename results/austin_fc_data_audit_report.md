# Austin FC Sales History Data Audit Report

## 1. Executive Summary

An automated audit was performed on the PostgreSQL table
`austin_fc_sales_history` in the `data_analysis` database.

The dataset contains **5,326,581 records**.

The transaction period runs from **2019-08-15 18:42:04.997000**
through **2026-09-18 21:21:33.293000**.

The total recorded payment value is **$482,706,014.11**.
The average recorded payment is **$90.62**.
The minimum payment is **$0.00** and the maximum
payment is **$293,025.20**.

The audit did not modify or delete any source records.

## 2. Dataset Overview

| Measure | Result |
|---|---:|
| Total records | 5,326,581 |
| Rows with payment | 5,326,581 |
| Earliest transaction | 2019-08-15 18:42:04.997000 |
| Latest transaction | 2026-09-18 21:21:33.293000 |
| Total payment | $482,706,014.11 |
| Average payment | $90.62 |
| Minimum payment | $0.00 |
| Maximum payment | $293,025.20 |
| NULL payments | 0 |
| Zero payments | 2,062,980 |
| Negative payments | 0 |

## 3. Missing Data

The complete missing-value results are available in:

`03_missing_values_by_column.csv`

The audit treats NULL and blank text values as missing for the relevant
identifier and text fields.

Missing values should not automatically be replaced or deleted.
Their business meaning should be established first.

## 4. Identifier Analysis

The audit compares the following identifiers:

- primary_ticket_id
- subscription_instance_id
- sales_item_id
- product_item_id
- transaction_id
- product_id

Repeated identifiers were detected during the audit.

Repeated identifiers should not automatically be treated as duplicate
records. The dataset grain must first be established.

A primary ticket may legitimately appear in multiple sales or transaction
records.

## 5. Product Type

The complete product-type distribution is available in:

`04_product_type.csv`

The major product categories observed in the dataset should be analyzed
separately where their business meanings differ.

## 6. Sale Type

The complete sale-type distribution is available in:

`05_sale_type.csv`

Sale types should be considered when calculating sales performance because
different transaction types may represent different business events.

## 7. Application Channel

The application-channel distribution is available in:

`06_application_channel.csv`

Application channel should be included in future analysis because
transaction volume and payment value can differ substantially between
channels.

## 8. Hospitality Field

The hospitality analysis is available in:

`07_hospitality.csv`.

NULL hospitality values are reported separately from FALSE values.

This distinction is important. NULL should not automatically be converted
to FALSE without confirming the source-system meaning.

## 9. Financial Audit

The financial anomaly results are available in:

`13_financial_anomalies.csv`

The largest transactions are available in:

`14_largest_transactions_top100.csv`

Zero-value transactions and unusually large transactions should be
investigated before any records are removed.

A large payment is not automatically an error.

## 10. Date Audit

The dataset covers multiple years.

The yearly summary is available in:

`15_yearly_trend.csv`

The monthly summary is available in:

`16_monthly_trend.csv`

Date consistency checks are available in:

`17_date_consistency.csv`

## 11. Data-Type Validation

The database column definitions are available in:

`21_column_types.csv`

The `row` and `seat` fields are stored as text because ticket location
values can contain alphanumeric values.

This prevents values such as `GA1` from causing numeric conversion errors.

## 12. Potential Data Grain

The potential grain analysis is available in:

`22_potential_data_grain.csv`

Determining the exact meaning of one row is one of the most important
remaining steps.

The team should determine whether a row represents a ticket, sales item,
transaction, subscription event, resale event, or another business event.

## 13. Key Data Quality Findings

1. The dataset contains more than five million records.
2. The dataset covers transactions from 2019 through 2026.
3. Payment values contain zero-value transactions.
4. Identifier fields have different levels of completeness.
5. Some identifiers occur more than once.
6. NULL and blank values occur in several fields.
7. Hospitality NULL values must be distinguished from FALSE values.
8. The row and seat fields require text handling because ticket locations
   can be alphanumeric.
9. Product types and sale types represent different categories of records.
10. Large financial values should be investigated rather than automatically
    removed.

## 14. Recommended Next Steps

### Step 1: Establish the data grain

Determine exactly what one row represents.

### Step 2: Investigate missing identifiers

Determine why subscription records and other records may not contain a
primary ticket identifier.

### Step 3: Investigate repeated identifiers

Determine whether repeated identifiers represent legitimate business events
or true duplicate records.

### Step 4: Investigate financial anomalies

Review zero-value and unusually large transactions.

### Step 5: Create analytical views

Create purpose-specific PostgreSQL views for revenue, ticket activity,
subscriptions, resale activity, and time-series analysis.

### Step 6: Analyze with Python

Use pandas for sampled and aggregated analysis rather than loading the
entire dataset into memory.

### Step 7: Build Tableau dashboards

Connect Tableau to PostgreSQL after the analytical views have been
validated.

## 15. Conclusion

The Austin FC sales history dataset contains substantial historical
information and is suitable for further analysis after the remaining data
quality questions are addressed.

The audit was designed to preserve the source data. No records were
deleted or modified.

The most important remaining question is the dataset grain. Understanding
what each row represents will allow the team to distinguish legitimate
repeated identifiers from actual duplicate records.

The audit outputs in the `results` directory provide the evidence needed
for the next stage of the project.

---

**Audit generated automatically by `austin_fc_data_audit.py`.**
