# Austin FC Sales Data — Comprehensive Audit

Generated: 2026-10-02T06:52:50

## Executive Summary

- Records audited: **5,335,362**
- Total revenue: **$482,907,804.90**
- Average transaction: **$90.51**
- Median transaction: **$35.62**
- Minimum payment: **$0.00**
- Maximum payment: **$293,025.20**
- Earliest transaction: **2019-08-15 18:42:04.997000**
- Latest transaction: **2026-09-24 20:04:57.997000**

The analysis was performed against the complete PostgreSQL source table. The source table was not sampled.

## Business Issues Requiring Attention

| Category | Severity | Issue | Evidence | Business Impact | Recommended Action |
|---|---|---|---|---|---|
| Data completeness | INFO | Dataset row count matches the verified updated dataset. | 5,335,362 records audited. | Supports confidence in the current database load. | Retain this dataset as the current audit baseline. |
| Revenue data | REVIEW | Zero-payment transactions exist. | 2,069,655 records have a zero payment. | May represent complimentary, adjusted, test, or non-revenue transactions. | Classify zero-payment transactions by business purpose. |
| Transaction monitoring | REVIEW | Very high-value transactions require validation. | 1 transactions exceed $100,000. | Unusual values can materially affect aggregate revenue. | Validate high-value transactions against source-system records. |
| Data completeness | REVIEW | Missing primary_ticket_id values exist. | 162,859 records are missing the identifier. | May affect customer, ticket, or subscription-level analysis. | Interpret missingness by product type before labeling it as an error. |
| Data completeness | REVIEW | Missing subscription_instance_id values exist. | 1,937,352 records are missing the identifier. | May affect customer, ticket, or subscription-level analysis. | Interpret missingness by product type before labeling it as an error. |
| Reporting period | INFO | September 2026 is a partial month. | The latest transaction date is September 24, 2026. | Monthly comparisons can be misleading if partial periods are treated as complete. | Flag September 2026 as partial in dashboards and reports. |
| Duplicate transactions | REVIEW | Repeated transaction IDs were detected. | 10,000 duplicate transaction groups are present in the exported sample. | Could represent legitimate multi-line transactions or duplicate records. | Investigate transaction grain before deduplicating. |

## Financial Quality

- NULL payments: **0**
- Zero payments: **2,069,655**
- Negative payments: **0**
- Payments above $10,000: **2,928**
- Payments above $50,000: **1**
- Payments above $100,000: **1**

## Payment Distribution

- P25: **$0.00**
- Median: **$35.62**
- P75: **$69.51**
- P90: **$155.60**
- P95: **$298.70**
- P99: **$931.95**

## Product Performance

| Product Type | Records | Revenue | Average Payment | Revenue Share |
|---|---:|---:|---:|---:|
| Ticket | 3,117,996 | $250,837,782.74 | $80.45 | 51.94% |
| Subscription | 162,859 | $186,437,253.16 | $1,144.78 | 38.61% |
| Resale | 2,054,507 | $45,632,769.00 | $22.21 | 9.45% |

## Application Channel Performance

| Channel | Records | Revenue | Average Payment | Revenue Share |
|---|---:|---:|---:|---:|
| Internal | 1,882,587 | $259,192,883.48 | $137.68 | 53.67% |
| bSRO | 639,498 | $114,083,690.16 | $178.40 | 23.62% |
| eSRO | 2,813,277 | $109,631,231.26 | $38.97 | 22.70% |

## Date Coverage

- Earliest transaction: **2019-08-15 18:42:04.997000**
- Latest transaction: **2026-09-24 20:04:57.997000**
- September 2026 is a partial reporting month.

## Methodology

Large-scale calculations were performed in PostgreSQL. Only small aggregate result sets were transferred to pandas.

This prevents the complete 5.3-million-row dataset from being loaded into memory.

Unusual values are treated as investigation candidates. They are not automatically classified as fraud or errors.

## Generated Outputs

The `results/tables/` directory contains aggregate CSV outputs. The `results/charts/` directory contains visualizations.
