# Austin FC Sales Data — Comprehensive Audit

Audit generated: 2026-10-01T02:57:44

## 1. Executive Summary

- **Total rows:** 5,326,581
- **Earliest transaction:** 2019-08-15 18:42:04.997000
- **Latest transaction:** 2026-09-18 21:21:33.293000
- **Total payment:** $482,706,014.11
- **Average payment:** $90.62
- **Minimum payment:** $0.00
- **Maximum payment:** $293,025.20

The audit was performed against the complete PostgreSQL source table. The source table was not sampled.

## 2. Dataset Completeness

PASS — The database contains exactly **5,326,581 rows**, matching the verified full dataset size.

## 3. Data Quality Scorecard

- PASS checks: **5**
- REVIEW checks: **7**
- FAIL checks: **0**

| Area | Status | Finding | Recommendation |
|---|---|---|---|
| Dataset completeness | PASS | Dataset contains exactly 5,326,581 rows. | Retain the complete dataset as the audit baseline. |
| Payment completeness | PASS | No NULL total_payment values were detected. | No action required. |
| Negative payments | PASS | No negative payment values were detected. | No action required. |
| Zero payments | REVIEW | 2,062,980 zero-payment records were detected. | Determine whether zero values represent complimentary or non-revenue transactions. |
| Future transactions | PASS | No transaction dates occur after the current timestamp. | No action required. |
| Date ordering | PASS | No transaction_date values occur after last_touched_at. | No action required. |
| Identifier: primary_ticket_id | REVIEW | 1,586,095 duplicate primary_ticket_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |
| Identifier: subscription_instance_id | REVIEW | 125,430 duplicate subscription_instance_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |
| Identifier: sales_item_id | REVIEW | 178 duplicate sales_item_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |
| Identifier: product_item_id | REVIEW | 178 duplicate product_item_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |
| Identifier: transaction_id | REVIEW | 888,928 duplicate transaction_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |
| Identifier: product_id | REVIEW | 575 duplicate product_id groups were detected. | Determine whether repeated identifiers are expected at the dataset's business grain. |

## 4. Missing Values

Missing-value analysis is available in `tables/03_missing_values_by_column.csv`.

## 5. Financial Quality

- NULL payments: **0**
- Zero payments: **2,062,980**
- Negative payments: **0**
- Payments above $10,000: **2,924**
- Payments above $50,000: **1**
- Payments above $100,000: **1**

Payment percentile statistics are available in `tables/07_payment_statistics.csv`.

## 6. Identifier Analysis

- **primary_ticket_id**: 1,586,095 duplicate groups
- **subscription_instance_id**: 125,430 duplicate groups
- **sales_item_id**: 178 duplicate groups
- **product_item_id**: 178 duplicate groups
- **transaction_id**: 888,928 duplicate groups
- **product_id**: 575 duplicate groups

Duplicate identifiers are not automatically data errors. Their interpretation depends on the business grain of the source system.

## 7. Time Analysis

Yearly and monthly trends were calculated directly from the PostgreSQL source table.

## 8. Date Consistency

- Missing transaction dates: 0
- Missing last-touched dates: 0
- Transaction after last-touch timestamp: 0
- Transactions before 2010: 0
- Future transactions: 0

## 9. Generated Outputs

The audit generates aggregate CSV tables and charts for team review.

Transaction-level identifier exports are intentionally excluded from the published audit.

## 10. Reproducibility

The audit uses PostgreSQL for large-scale aggregation and Python for reporting. This prevents the complete 5.3M-row source table from being loaded into memory at once.

The source database credentials are stored in `.env` and are not included in the repository.
