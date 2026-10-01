# Austin FC Sales Data Audit

## Project Overview

This project performs a large-scale data quality and exploratory audit of the Austin FC sales history dataset.

The analysis uses the complete dataset containing **5,326,581 records** covering transactions from **August 15, 2019 through September 18, 2026**.

The raw dataset is approximately 2.5 GB and is therefore not stored in this Git repository. The data is loaded into PostgreSQL for efficient analysis. Python, pandas, SQLAlchemy, and Jupyter are used to generate audit results and supporting analysis.

## Dataset

The complete dataset contains:

- **5,326,581 rows**
- Transaction period: **2019-08-15 to 2026-09-18**
- Total recorded payment: **$482,706,014.11**
- Database table: `austin_fc_sales_history`
- Database system: PostgreSQL 16

The raw CSV and ZIP archive are intentionally excluded from Git because of their size.

## Analysis Areas

The audit examines:

- Dataset size and structure
- Missing values
- Product types
- Sale types
- Application channels
- Hospitality records
- Identifier uniqueness
- Duplicate records
- Financial anomalies
- Yearly sales trends
- Monthly sales trends
- Date consistency
- Product descriptions
- Transfer status
- Resale status
- Database column types
- Potential data grain
- Overall audit findings

## Project Structure

```text
data-analysis/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── notebooks/
│   └── 01_austin_fc_data_audit.ipynb
├── results/
│   ├── 01_dataset_overview.csv
│   ├── 02_missing_values_wide.csv
│   ├── 03_missing_values_by_column.csv
│   ├── 04_product_type.csv
│   ├── 05_sale_type.csv
│   ├── 06_application_channel.csv
│   ├── 07_hospitality.csv
│   ├── 08_identifier_uniqueness.csv
│   ├── 12_duplicate_summary.csv
│   ├── 13_financial_anomalies.csv
│   ├── 15_yearly_trend.csv
│   ├── 16_monthly_trend.csv
│   ├── 17_date_consistency.csv
│   ├── 18_top_product_descriptions.csv
│   ├── 19_transfer_status.csv
│   ├── 20_resale_status.csv
│   ├── 21_column_types.csv
│   ├── 22_potential_data_grain.csv
│   ├── 23_audit_summary_flags.csv
│   └── austin_fc_data_audit_report.md
├── scripts/
│   ├── austin_fc_data_audit.py
│   └── test_postgres.py
└── sql/

exit
q
