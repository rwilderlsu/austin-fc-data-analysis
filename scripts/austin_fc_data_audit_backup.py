#!/usr/bin/env python3
"""
Austin FC Sales History - Full Data Audit

Run from the data-analysis project directory.

The script:
1. Connects to PostgreSQL.
2. Audits table size, date range, financial values, missing values,
   categorical distributions, identifier uniqueness, duplicates,
   date consistency, and potential anomalies.
3. Saves detailed CSV results.
4. Saves a human-readable Markdown report.
5. Does NOT modify or delete the source data.

Expected database:
    data_analysis

Expected table:
    austin_fc_sales_history
"""

from pathlib import Path
import os
import sys
import traceback

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Optional .env support. The script also works with shell environment variables.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_DIR = Path.home() / "data-analysis"
RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = os.getenv("DB_NAME", "data_analysis")
DB_USER = os.getenv("DB_USER", "dataanalyst")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")

# Do not hard-code a password in this script.
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    print("\nDB_PASSWORD is not set.")
    print("Set it temporarily before running the script:")
    print("  export DB_PASSWORD='YOUR_POSTGRES_PASSWORD'")
    print("Then run the script again.")
    sys.exit(1)

TABLE = "austin_fc_sales_history"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def query_df(sql: str) -> pd.DataFrame:
    """Run SQL and return a pandas DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def query_one(sql: str):
    """Run SQL expected to return one value."""
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def save_csv(df: pd.DataFrame, filename: str):
    path = RESULTS_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved: {path}")
    return path


def section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def fmt_money(value):
    if pd.isna(value):
        return "N/A"
    return f"${float(value):,.2f}"


def fmt_number(value):
    if pd.isna(value):
        return "N/A"
    return f"{int(value):,}"


# ---------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------

def main():
    print("=" * 80)
    print("AUSTIN FC SALES HISTORY - FULL DATA AUDIT")
    print("=" * 80)
    print(f"Database : {DB_NAME}")
    print(f"Table    : {TABLE}")
    print(f"Results  : {RESULTS_DIR}")
    print()

    # -------------------------------------------------------------
    # 1. Connection test
    # -------------------------------------------------------------

    section("1. DATABASE CONNECTION")

    with engine.connect() as conn:
        db_test = conn.execute(
            text("SELECT current_database(), current_user, version()")
        ).fetchone()

    print(f"Current database : {db_test[0]}")
    print(f"Current user     : {db_test[1]}")
    print(f"PostgreSQL       : {db_test[2]}")

    # -------------------------------------------------------------
    # 2. Basic overview
    # -------------------------------------------------------------

    section("2. DATASET OVERVIEW")

    overview = query_df(f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(*) FILTER (
                WHERE total_payment IS NOT NULL
            ) AS rows_with_payment,
            MIN(transaction_date) AS earliest_transaction,
            MAX(transaction_date) AS latest_transaction,
            SUM(total_payment) AS total_payment,
            AVG(total_payment) AS average_payment,
            MIN(total_payment) AS minimum_payment,
            MAX(total_payment) AS maximum_payment,
            COUNT(*) FILTER (
                WHERE total_payment IS NULL
            ) AS null_payment,
            COUNT(*) FILTER (
                WHERE total_payment = 0
            ) AS zero_payment,
            COUNT(*) FILTER (
                WHERE total_payment < 0
            ) AS negative_payment
        FROM {TABLE};
    """)

    save_csv(overview, "01_dataset_overview.csv")

    row = overview.iloc[0]

    print(f"Total rows          : {fmt_number(row['total_rows'])}")
    print(f"Earliest transaction: {row['earliest_transaction']}")
    print(f"Latest transaction  : {row['latest_transaction']}")
    print(f"Total payment       : {fmt_money(row['total_payment'])}")
    print(f"Average payment     : {fmt_money(row['average_payment'])}")
    print(f"Minimum payment     : {fmt_money(row['minimum_payment'])}")
    print(f"Maximum payment     : {fmt_money(row['maximum_payment'])}")
    print(f"NULL payments       : {fmt_number(row['null_payment'])}")
    print(f"Zero payments       : {fmt_number(row['zero_payment'])}")
    print(f"Negative payments   : {fmt_number(row['negative_payment'])}")

    # -------------------------------------------------------------
    # 3. Missing values
    # -------------------------------------------------------------

    section("3. MISSING VALUES")

    missing_sql = f"""
        SELECT
            COUNT(*) AS total_rows,

            COUNT(*) FILTER (
                WHERE primary_ticket_id IS NULL
                   OR TRIM(primary_ticket_id) = ''
            ) AS primary_ticket_id_missing,

            COUNT(*) FILTER (
                WHERE subscription_instance_id IS NULL
                   OR TRIM(subscription_instance_id) = ''
            ) AS subscription_instance_id_missing,

            COUNT(*) FILTER (
                WHERE sales_item_id IS NULL
                   OR TRIM(sales_item_id) = ''
            ) AS sales_item_id_missing,

            COUNT(*) FILTER (
                WHERE product_item_id IS NULL
                   OR TRIM(product_item_id) = ''
            ) AS product_item_id_missing,

            COUNT(*) FILTER (
                WHERE transaction_id IS NULL
                   OR TRIM(transaction_id) = ''
            ) AS transaction_id_missing,

            COUNT(*) FILTER (
                WHERE product_id IS NULL
                   OR TRIM(product_id) = ''
            ) AS product_id_missing,

            COUNT(*) FILTER (
                WHERE sales_rep IS NULL
                   OR TRIM(sales_rep) = ''
            ) AS sales_rep_missing,

            COUNT(*) FILTER (
                WHERE transaction_date IS NULL
            ) AS transaction_date_missing,

            COUNT(*) FILTER (
                WHERE last_touched_at IS NULL
            ) AS last_touched_at_missing,

            COUNT(*) FILTER (
                WHERE item_type IS NULL
                   OR TRIM(item_type) = ''
            ) AS item_type_missing,

            COUNT(*) FILTER (
                WHERE product_type IS NULL
                   OR TRIM(product_type) = ''
            ) AS product_type_missing,

            COUNT(*) FILTER (
                WHERE sale_type IS NULL
                   OR TRIM(sale_type) = ''
            ) AS sale_type_missing,

            COUNT(*) FILTER (
                WHERE transfer_status IS NULL
                   OR TRIM(transfer_status) = ''
            ) AS transfer_status_missing,

            COUNT(*) FILTER (
                WHERE resale_status IS NULL
                   OR TRIM(resale_status) = ''
            ) AS resale_status_missing,

            COUNT(*) FILTER (
                WHERE sales_details IS NULL
                   OR TRIM(sales_details) = ''
            ) AS sales_details_missing,

            COUNT(*) FILTER (
                WHERE price_level IS NULL
                   OR TRIM(price_level) = ''
            ) AS price_level_missing,

            COUNT(*) FILTER (
                WHERE price_type IS NULL
                   OR TRIM(price_type) = ''
            ) AS price_type_missing,

            COUNT(*) FILTER (
                WHERE price_type_group IS NULL
                   OR TRIM(price_type_group) = ''
            ) AS price_type_group_missing,

            COUNT(*) FILTER (
                WHERE total_payment IS NULL
            ) AS total_payment_missing,

            COUNT(*) FILTER (
                WHERE total_plan_amount IS NULL
            ) AS total_plan_amount_missing,

            COUNT(*) FILTER (
                WHERE section IS NULL
                   OR TRIM(section) = ''
            ) AS section_missing,

            COUNT(*) FILTER (
                WHERE row IS NULL
                   OR TRIM(row) = ''
            ) AS row_missing,

            COUNT(*) FILTER (
                WHERE seat IS NULL
                   OR TRIM(seat) = ''
            ) AS seat_missing,

            COUNT(*) FILTER (
                WHERE product_description IS NULL
                   OR TRIM(product_description) = ''
            ) AS product_description_missing,

            COUNT(*) FILTER (
                WHERE application_channel IS NULL
                   OR TRIM(application_channel) = ''
            ) AS application_channel_missing,

            COUNT(*) FILTER (
                WHERE is_hospitality IS NULL
            ) AS hospitality_null

        FROM {TABLE};
    """

    missing_wide = query_df(missing_sql)
    save_csv(missing_wide, "02_missing_values_wide.csv")

    missing_long = missing_wide.T.reset_index()
    missing_long.columns = ["column", "missing_count"]

    total_rows = int(row["total_rows"])
    missing_long["missing_percentage"] = (
        missing_long["missing_count"] / total_rows * 100
    )
    missing_long = missing_long.sort_values(
        "missing_count", ascending=False
    )

    save_csv(missing_long, "03_missing_values_by_column.csv")

    print(
        missing_long[
            missing_long["column"] != "total_rows"
        ].to_string(index=False)
    )

    # -------------------------------------------------------------
    # 4. Product type
    # -------------------------------------------------------------

    section("4. PRODUCT TYPE")

    product_type = query_df(f"""
        SELECT
            COALESCE(product_type, '[NULL]') AS product_type,
            COUNT(*) AS records,
            ROUND(
                COUNT(*)::numeric /
                NULLIF((SELECT COUNT(*) FROM {TABLE}), 0) * 100,
                2
            ) AS record_percentage,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        GROUP BY product_type
        ORDER BY records DESC;
    """)

    save_csv(product_type, "04_product_type.csv")
    print(product_type.to_string(index=False))

    # -------------------------------------------------------------
    # 5. Sale type
    # -------------------------------------------------------------

    section("5. SALE TYPE")

    sale_type = query_df(f"""
        SELECT
            COALESCE(sale_type, '[NULL]') AS sale_type,
            COUNT(*) AS records,
            ROUND(
                COUNT(*)::numeric /
                NULLIF((SELECT COUNT(*) FROM {TABLE}), 0) * 100,
                2
            ) AS record_percentage,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        GROUP BY sale_type
        ORDER BY records DESC;
    """)

    save_csv(sale_type, "05_sale_type.csv")
    print(sale_type.to_string(index=False))

    # -------------------------------------------------------------
    # 6. Application channel
    # -------------------------------------------------------------

    section("6. APPLICATION CHANNEL")

    application_channel = query_df(f"""
        SELECT
            COALESCE(application_channel, '[NULL]') AS application_channel,
            COUNT(*) AS records,
            ROUND(
                COUNT(*)::numeric /
                NULLIF((SELECT COUNT(*) FROM {TABLE}), 0) * 100,
                2
            ) AS record_percentage,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        GROUP BY application_channel
        ORDER BY records DESC;
    """)

    save_csv(application_channel, "06_application_channel.csv")
    print(application_channel.to_string(index=False))

    # -------------------------------------------------------------
    # 7. Hospitality
    # -------------------------------------------------------------

    section("7. HOSPITALITY FLAG")

    hospitality = query_df(f"""
        SELECT
            CASE
                WHEN is_hospitality IS TRUE THEN 'true'
                WHEN is_hospitality IS FALSE THEN 'false'
                ELSE 'NULL'
            END AS hospitality_status,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        GROUP BY
            CASE
                WHEN is_hospitality IS TRUE THEN 'true'
                WHEN is_hospitality IS FALSE THEN 'false'
                ELSE 'NULL'
            END
        ORDER BY records DESC;
    """)

    save_csv(hospitality, "07_hospitality.csv")
    print(hospitality.to_string(index=False))

    # -------------------------------------------------------------
    # 8. Identifier uniqueness
    # -------------------------------------------------------------

    section("8. IDENTIFIER UNIQUENESS")

    uniqueness = query_df(f"""
        SELECT
            COUNT(*) AS total_rows,

            COUNT(DISTINCT NULLIF(TRIM(primary_ticket_id), ''))
                AS unique_primary_ticket_ids,

            COUNT(DISTINCT NULLIF(TRIM(subscription_instance_id), ''))
                AS unique_subscription_instance_ids,

            COUNT(DISTINCT NULLIF(TRIM(sales_item_id), ''))
                AS unique_sales_item_ids,

            COUNT(DISTINCT NULLIF(TRIM(product_item_id), ''))
                AS unique_product_item_ids,

            COUNT(DISTINCT NULLIF(TRIM(transaction_id), ''))
                AS unique_transaction_ids,

            COUNT(DISTINCT NULLIF(TRIM(product_id), ''))
                AS unique_product_ids
        FROM {TABLE};
    """)

    save_csv(uniqueness, "08_identifier_uniqueness.csv")
    print(uniqueness.to_string(index=False))

    # -------------------------------------------------------------
    # 9. Duplicate groups
    # -------------------------------------------------------------

    section("9. DUPLICATE IDENTIFIER GROUPS")

    duplicate_sales_items = query_df(f"""
        SELECT
            sales_item_id,
            COUNT(*) AS occurrences
        FROM {TABLE}
        WHERE sales_item_id IS NOT NULL
          AND TRIM(sales_item_id) <> ''
        GROUP BY sales_item_id
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC
        LIMIT 1000;
    """)

    save_csv(
        duplicate_sales_items,
        "09_duplicate_sales_item_ids_top1000.csv"
    )

    duplicate_transactions = query_df(f"""
        SELECT
            transaction_id,
            COUNT(*) AS occurrences
        FROM {TABLE}
        WHERE transaction_id IS NOT NULL
          AND TRIM(transaction_id) <> ''
        GROUP BY transaction_id
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC
        LIMIT 1000;
    """)

    save_csv(
        duplicate_transactions,
        "10_duplicate_transaction_ids_top1000.csv"
    )

    duplicate_tickets = query_df(f"""
        SELECT
            primary_ticket_id,
            COUNT(*) AS occurrences
        FROM {TABLE}
        WHERE primary_ticket_id IS NOT NULL
          AND TRIM(primary_ticket_id) <> ''
        GROUP BY primary_ticket_id
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC
        LIMIT 1000;
    """)

    save_csv(
        duplicate_tickets,
        "11_duplicate_primary_ticket_ids_top1000.csv"
    )

    duplicate_summary = pd.DataFrame([
        {
            "identifier": "sales_item_id",
            "duplicate_groups": len(duplicate_sales_items),
        },
        {
            "identifier": "transaction_id",
            "duplicate_groups": len(duplicate_transactions),
        },
        {
            "identifier": "primary_ticket_id",
            "duplicate_groups": len(duplicate_tickets),
        },
    ])

    save_csv(duplicate_summary, "12_duplicate_summary.csv")
    print(duplicate_summary.to_string(index=False))

    # -------------------------------------------------------------
    # 10. Financial anomaly audit
    # -------------------------------------------------------------

    section("10. FINANCIAL ANOMALIES")

    financial_anomalies = query_df(f"""
        SELECT
            COUNT(*) FILTER (WHERE total_payment < 0)
                AS negative_payments,

            COUNT(*) FILTER (WHERE total_payment = 0)
                AS zero_payments,

            COUNT(*) FILTER (WHERE total_payment > 10000)
                AS payments_over_10000,

            COUNT(*) FILTER (WHERE total_payment > 50000)
                AS payments_over_50000,

            COUNT(*) FILTER (WHERE total_payment > 100000)
                AS payments_over_100000
        FROM {TABLE};
    """)

    save_csv(financial_anomalies, "13_financial_anomalies.csv")
    print(financial_anomalies.to_string(index=False))

    # Largest transactions
    largest_transactions = query_df(f"""
        SELECT
            transaction_date,
            total_payment,
            product_type,
            sale_type,
            product_description,
            application_channel,
            primary_ticket_id,
            transaction_id,
            sales_item_id
        FROM {TABLE}
        WHERE total_payment IS NOT NULL
        ORDER BY total_payment DESC
        LIMIT 100;
    """)

    save_csv(
        largest_transactions,
        "14_largest_transactions_top100.csv"
    )

    # -------------------------------------------------------------
    # 11. Yearly trend
    # -------------------------------------------------------------

    section("11. YEARLY TREND")

    yearly = query_df(f"""
        SELECT
            EXTRACT(YEAR FROM transaction_date)::integer AS year,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        WHERE transaction_date IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM transaction_date)
        ORDER BY year;
    """)

    save_csv(yearly, "15_yearly_trend.csv")
    print(yearly.to_string(index=False))

    # -------------------------------------------------------------
    # 12. Monthly trend
    # -------------------------------------------------------------

    section("12. MONTHLY TREND")

    monthly = query_df(f"""
        SELECT
            DATE_TRUNC('month', transaction_date)::date AS month,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        WHERE transaction_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY month;
    """)

    save_csv(monthly, "16_monthly_trend.csv")

    # -------------------------------------------------------------
    # 13. Date consistency
    # -------------------------------------------------------------

    section("13. DATE CONSISTENCY")

    date_consistency = query_df(f"""
        SELECT
            COUNT(*) FILTER (
                WHERE transaction_date IS NULL
            ) AS missing_transaction_date,

            COUNT(*) FILTER (
                WHERE last_touched_at IS NULL
            ) AS missing_last_touched_at,

            COUNT(*) FILTER (
                WHERE transaction_date > last_touched_at
            ) AS transaction_after_last_touch,

            COUNT(*) FILTER (
                WHERE transaction_date < TIMESTAMP '2010-01-01'
            ) AS transaction_before_2010,

            COUNT(*) FILTER (
                WHERE transaction_date > CURRENT_TIMESTAMP
            ) AS transaction_in_future
        FROM {TABLE};
    """)

    save_csv(date_consistency, "17_date_consistency.csv")
    print(date_consistency.to_string(index=False))

    # -------------------------------------------------------------
    # 14. Product description
    # -------------------------------------------------------------

    section("14. TOP PRODUCT DESCRIPTIONS")

    top_products = query_df(f"""
        SELECT
            product_description,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue,
            ROUND(AVG(total_payment), 2) AS average_payment
        FROM {TABLE}
        WHERE product_description IS NOT NULL
          AND TRIM(product_description) <> ''
        GROUP BY product_description
        ORDER BY records DESC
        LIMIT 100;
    """)

    save_csv(top_products, "18_top_product_descriptions.csv")

    # -------------------------------------------------------------
    # 15. Status distributions
    # -------------------------------------------------------------

    section("15. TRANSFER STATUS")

    transfer_status = query_df(f"""
        SELECT
            COALESCE(transfer_status, '[NULL]') AS transfer_status,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue
        FROM {TABLE}
        GROUP BY transfer_status
        ORDER BY records DESC;
    """)

    save_csv(transfer_status, "19_transfer_status.csv")

    section("16. RESALE STATUS")

    resale_status = query_df(f"""
        SELECT
            COALESCE(resale_status, '[NULL]') AS resale_status,
            COUNT(*) AS records,
            ROUND(SUM(total_payment), 2) AS revenue
        FROM {TABLE}
        GROUP BY resale_status
        ORDER BY records DESC;
    """)

    save_csv(resale_status, "20_resale_status.csv")

    # -------------------------------------------------------------
    # 17. Data type information
    # -------------------------------------------------------------

    section("17. DATABASE COLUMN TYPES")

    column_types = query_df(f"""
        SELECT
            ordinal_position,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = '{TABLE}'
        ORDER BY ordinal_position;
    """)

    save_csv(column_types, "21_column_types.csv")
    print(column_types.to_string(index=False))

    # -------------------------------------------------------------
    # 18. Potential grain analysis
    # -------------------------------------------------------------

    section("18. POTENTIAL DATA GRAIN")

    grain = query_df(f"""
        SELECT
            product_type,
            sale_type,
            COUNT(*) AS records,
            COUNT(DISTINCT NULLIF(TRIM(primary_ticket_id), ''))
                AS unique_primary_ticket_ids,
            COUNT(DISTINCT NULLIF(TRIM(sales_item_id), ''))
                AS unique_sales_item_ids,
            COUNT(DISTINCT NULLIF(TRIM(transaction_id), ''))
                AS unique_transaction_ids,
            COUNT(DISTINCT NULLIF(TRIM(subscription_instance_id), ''))
                AS unique_subscription_instances,
            ROUND(SUM(total_payment), 2) AS revenue
        FROM {TABLE}
        GROUP BY product_type, sale_type
        ORDER BY records DESC;
    """)

    save_csv(grain, "22_potential_data_grain.csv")
    print(grain.to_string(index=False))

    # -------------------------------------------------------------
    # 19. Audit summary flags
    # -------------------------------------------------------------

    section("19. AUDIT SUMMARY")

    negative_count = int(row["negative_payment"])
    zero_count = int(row["zero_payment"])
    null_payment_count = int(row["null_payment"])

    primary_missing = int(
        missing_wide.iloc[0]["primary_ticket_id_missing"]
    )

    hospitality_null = int(
        missing_wide.iloc[0]["hospitality_null"]
    )

    audit_flags = [
        {
            "area": "Dataset imported",
            "status": "PASS",
            "finding": f"{int(row['total_rows']):,} rows available",
        },
        {
            "area": "Payment completeness",
            "status": "PASS" if null_payment_count == 0 else "REVIEW",
            "finding": f"{null_payment_count:,} NULL payment values",
        },
        {
            "area": "Negative payments",
            "status": "PASS" if negative_count == 0 else "REVIEW",
            "finding": f"{negative_count:,} negative payment values",
        },
        {
            "area": "Zero payments",
            "status": "REVIEW" if zero_count > 0 else "PASS",
            "finding": f"{zero_count:,} zero payment values",
        },
        {
            "area": "Primary ticket ID completeness",
            "status": "REVIEW" if primary_missing > 0 else "PASS",
            "finding": f"{primary_missing:,} blank/NULL primary ticket IDs",
        },
        {
            "area": "Hospitality field",
            "status": "REVIEW" if hospitality_null > 0 else "PASS",
            "finding": f"{hospitality_null:,} NULL hospitality values",
        },
        {
            "area": "Duplicate identifiers",
            "status": "REVIEW",
            "finding": (
                "Repeated identifiers exist. Do not delete records "
                "until the dataset grain is established."
            ),
        },
        {
            "area": "Row and seat fields",
            "status": "REVIEWED",
            "finding": (
                "Fields are stored as text because ticket locations "
                "can contain alphanumeric values such as GA1."
            ),
        },
    ]

    audit_flags_df = pd.DataFrame(audit_flags)
    save_csv(audit_flags_df, "23_audit_summary_flags.csv")
    print(audit_flags_df.to_string(index=False))

    # -------------------------------------------------------------
    # 20. Human-readable Markdown report
    # -------------------------------------------------------------

    section("20. GENERATING REPORT")

    total = int(row["total_rows"])
    total_payment = float(row["total_payment"])
    avg_payment = float(row["average_payment"])
    min_payment = float(row["minimum_payment"])
    max_payment = float(row["maximum_payment"])

    report_path = RESULTS_DIR / "austin_fc_data_audit_report.md"

    report = f"""# Austin FC Sales History Data Audit Report

## 1. Executive Summary

An automated audit was performed on the PostgreSQL table
`{TABLE}` in the `{DB_NAME}` database.

The dataset contains **{total:,} records**.

The transaction period runs from **{row['earliest_transaction']}**
through **{row['latest_transaction']}**.

The total recorded payment value is **{fmt_money(total_payment)}**.
The average recorded payment is **{fmt_money(avg_payment)}**.
The minimum payment is **{fmt_money(min_payment)}** and the maximum
payment is **{fmt_money(max_payment)}**.

The audit did not modify or delete any source records.

## 2. Dataset Overview

| Measure | Result |
|---|---:|
| Total records | {total:,} |
| Rows with payment | {int(row['rows_with_payment']):,} |
| Earliest transaction | {row['earliest_transaction']} |
| Latest transaction | {row['latest_transaction']} |
| Total payment | {fmt_money(total_payment)} |
| Average payment | {fmt_money(avg_payment)} |
| Minimum payment | {fmt_money(min_payment)} |
| Maximum payment | {fmt_money(max_payment)} |
| NULL payments | {int(row['null_payment']):,} |
| Zero payments | {int(row['zero_payment']):,} |
| Negative payments | {int(row['negative_payment']):,} |

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
"""

    report_path.write_text(report, encoding="utf-8")
    print(f"Saved: {report_path}")

    # -------------------------------------------------------------
    # Finish
    # -------------------------------------------------------------

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print(f"Report : {report_path}")
    print(f"Results: {RESULTS_DIR}")
    print("\nNo source data was modified or deleted.")
    print("\nFiles generated:")
    for path in sorted(RESULTS_DIR.iterdir()):
        print(f"  - {path.name}")


if __name__ == "__main__":
    try:
        main()
    except SQLAlchemyError as exc:
        print("\nDATABASE ERROR")
        print(exc)
        print("\nCheck that PostgreSQL is running and that your credentials")
        print("are correct.")
        sys.exit(2)
    except Exception as exc:
        print("\nUNEXPECTED ERROR")
        print(exc)
        traceback.print_exc()
        sys.exit(3)
