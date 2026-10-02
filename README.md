# Austin FC Sales Data Audit

## Project Overview

This project performs a large-scale data quality audit and exploratory analysis of the Austin FC sales history dataset.

The analysis uses the updated dataset containing **5,335,362 records** covering transactions from **August 15, 2019 through September 24, 2026**.

Because the raw CSV is approximately **2.5 GB**, it is not stored in this Git repository. The dataset is loaded into PostgreSQL for efficient full-data analysis. Python, pandas, SQLAlchemy, and Jupyter Notebook are used to perform the analysis and generate tables, statistics, and visualizations.

The analysis is designed to work with the complete dataset without attempting to load all 5.3 million records into pandas at once. PostgreSQL performs the large-scale aggregations while Python and pandas are used for analysis summaries and visualization.

## Dataset

The updated dataset contains:

* **5,335,362 rows**
* Transaction period: **2019-08-15 through 2026-09-24**
* Total recorded payment: **$482,907,804.90**
* Average payment: **$90.51**
* Minimum payment: **$0.00**
* Maximum payment: **$293,025.20**
* Database table: `austin_fc_sales_history_updated_2026_09_24`
* Database system: **PostgreSQL 16**

The September 2026 data is **partial**, because the dataset ends on September 24, 2026.

The raw CSV and ZIP archive are intentionally excluded from Git because of their size.

## Data Quality Findings

The full dataset contains several missing-value patterns.

Important results include:

* **162,859** records have a missing `primary_ticket_id`.
* **1,937,352** records have a missing `subscription_instance_id`.
* `sales_item_id`, `product_item_id`, `transaction_id`, `product_id`, `transaction_date`, `total_payment`, `product_type`, `application_channel`, and `product_description` contain no missing values.
* `section`, `row`, and `seat` each have **156,695** missing values.

The missing identifier patterns are associated with product type. For example, all **162,859 Subscription** records have a missing `primary_ticket_id`, while all Subscription records have a `subscription_instance_id`.

These patterns are treated as data characteristics that require interpretation rather than automatically being classified as errors.

## Payment Analysis

The full dataset was analyzed using PostgreSQL.

Payment distribution results include:

* First quartile: **$0.00**
* Median: **$35.62**
* Third quartile: **$69.51**
* 90th percentile: **$155.60**
* 95th percentile: **$298.70**
* 99th percentile: **$931.95**

The large difference between the median payment and the maximum payment indicates a highly dispersed payment distribution. The analysis therefore considers both typical transaction values and unusually large payments.

## Product Type Analysis

The updated dataset contains three major product types:

| Product Type | Transactions |   Total Payment | Average Payment |
| ------------ | -----------: | --------------: | --------------: |
| Ticket       |    3,117,996 | $250,837,782.74 |          $80.45 |
| Subscription |      162,859 | $186,437,253.16 |       $1,144.78 |
| Resale       |    2,054,507 |  $45,632,769.00 |          $22.21 |

These categories show substantially different transaction volumes and payment distributions.

## Application Channel Analysis

The analysis identifies three application channels:

| Application Channel | Transactions |   Total Payment | Average Payment |
| ------------------- | -----------: | --------------: | --------------: |
| Internal            |    1,882,587 | $259,192,883.48 |         $137.68 |
| bSRO                |      639,498 | $114,083,690.16 |         $178.40 |
| eSRO                |    2,813,277 | $109,631,231.26 |          $38.97 |

These results are calculated from the complete updated dataset.

## Analysis Areas

The audit examines:

* Dataset size and structure
* Transaction date coverage
* Missing values
* Missingness by product type
* Payment distribution
* Product types
* Sale types
* Application channels
* Hospitality records
* Price levels
* Price types
* Sales representatives
* Identifier completeness
* Duplicate transactions
* Potential financial anomalies
* Monthly sales trends
* Yearly sales trends
* Product descriptions
* Transfer status
* Resale status
* Database column types
* Potential data grain
* Overall data quality findings

## Methodology

The analysis follows a database-first approach.

Large-scale calculations are performed directly in PostgreSQL to avoid loading the entire 5.3 million-row dataset into memory.

Python is then used to retrieve summarized results and create analysis tables and visualizations.

The main tools are:

* **PostgreSQL 16** — full-dataset storage, filtering, aggregation, and statistical calculations
* **Python** — analysis and automation
* **pandas** — summary data manipulation
* **SQLAlchemy** — Python-to-PostgreSQL connection
* **Matplotlib** — data visualization
* **Jupyter Notebook** — reproducible analysis and documentation

A small **1,000-row sample** of the raw data is also loaded into pandas for direct record-level inspection. The full dataset remains in PostgreSQL during the analysis.

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
```

> **Note:** The files listed under `results/`, `scripts/`, and `sql/` should reflect the files actually present in the repository. The executed Jupyter notebook is the primary reproducible analysis artifact.

## Reproducibility

The database connection is configured through environment variables stored in `.env`.

The `.env` file is intentionally excluded from Git to protect database credentials.

A template is provided through:

```text
.env.example
```

To reproduce the analysis, configure the PostgreSQL connection variables and make sure the updated Austin FC dataset is available in the PostgreSQL database.

The main analysis notebook is:

```text
notebooks/01_austin_fc_data_audit.ipynb
```

## Important Data Limitation

The dataset represents transaction records available through **September 24, 2026**.

Because September 2026 ends on September 30, the September 2026 monthly results represent a **partial month** and should not be directly interpreted as a complete-month result.

The analysis also distinguishes between missing values that may represent legitimate differences in transaction structure and values that may require further investigation.

## Conclusion

This project provides a full-data audit of more than **5.3 million Austin FC sales-history records** using a PostgreSQL-based analytical workflow.

The analysis combines database-level processing with Python-based statistical analysis and visualization. This approach makes it possible to examine the complete dataset while avoiding the memory limitations that would occur if all records were loaded into pandas simultaneously.

The resulting Jupyter Notebook provides a reproducible record of the analysis, including dataset coverage, data quality findings, transaction characteristics, payment distributions, product categories, application channels, and time-based sales patterns.

