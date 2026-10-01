#!/usr/bin/env python3

"""
Austin FC Sales Data - Comprehensive Data Audit

Purpose
-------
Perform a comprehensive audit of the complete Austin FC sales history
dataset stored in PostgreSQL.

IMPORTANT
---------
This script is designed for large datasets.

It does NOT load the complete source table into pandas.

Instead:
    PostgreSQL -> SQL aggregation -> small pandas result -> CSV/HTML/chart

The authoritative source table is:

    austin_fc_sales_history

The expected dataset contains approximately:

    5,326,581 rows

The script produces:
    results/
        audit/
        charts/
        tables/
        austin_fc_comprehensive_audit_report.md
        austin_fc_comprehensive_audit.html

The script intentionally avoids exporting transaction-level records.
"""

from __future__ import annotations

import math
import os
import shutil
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = PROJECT_ROOT / ".env"

RESULTS_DIR = PROJECT_ROOT / "results"
AUDIT_DIR = RESULTS_DIR / "audit"
TABLES_DIR = RESULTS_DIR / "tables"
CHARTS_DIR = RESULTS_DIR / "charts"

DB_SCHEMA = "public"
TABLE_NAME = "austin_fc_sales_history"

EXPECTED_MIN_ROWS = 5_000_000
EXPECTED_EXACT_ROWS = 5_326_581


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(dotenv_path=ENV_FILE)

required_environment = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

missing_environment = [
    variable
    for variable in required_environment
    if not os.getenv(variable)
]

if missing_environment:
    raise RuntimeError(
        "Missing database settings: "
        + ", ".join(missing_environment)
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    "postgresql+psycopg2://"
    f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}"
    f"/{os.environ['DB_NAME']}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

for directory in [
    RESULTS_DIR,
    AUDIT_DIR,
    TABLES_DIR,
    CHARTS_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# HELPERS
# ============================================================

def sql_df(query: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame."""
    with engine.connect() as connection:
        return pd.read_sql(
            text(query),
            connection,
        )


def sql_one(query: str):
    """Execute SQL and return one row."""
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchone()


def save_csv(
    dataframe: pd.DataFrame,
    filename: str,
) -> Path:
    """Save an aggregate dataframe as CSV."""
    path = TABLES_DIR / filename
    dataframe.to_csv(
        path,
        index=False,
    )
    return path


def format_money(value) -> str:
    """Format a numeric value as currency."""
    if value is None or pd.isna(value):
        return "$0.00"

    return f"${float(value):,.2f}"


def format_number(value) -> str:
    """Format a number with commas."""
    if value is None or pd.isna(value):
        return "0"

    return f"{int(value):,}"


def percentage(value) -> str:
    """Format a percentage."""
    if value is None or pd.isna(value):
        return "0.00%"

    return f"{float(value):.2f}%"


def safe_filename(value: str) -> str:
    """Create a safe filename."""
    return (
        value.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


# ============================================================
# START
# ============================================================

started_at = datetime.now()

print()
print("=" * 80)
print("AUSTIN FC COMPREHENSIVE DATA AUDIT")
print("=" * 80)
print()
print("Project:", PROJECT_ROOT)
print("Database:", os.environ["DB_NAME"])
print("Table:", f"{DB_SCHEMA}.{TABLE_NAME}")
print()
print("The audit will use PostgreSQL aggregation.")
print("The complete 5.3M-row table will NOT be loaded into pandas.")
print()


# ============================================================
# 1. DATABASE CONNECTION TEST
# ============================================================

print("[01/18] Testing PostgreSQL connection...")

connection_info = sql_one(
    """
    SELECT
        current_database(),
        current_user,
        version()
    """
)

database_name = connection_info[0]
database_user = connection_info[1]
database_version = connection_info[2]

print("Database:", database_name)
print("User:", database_user)
print("Connection: OK")
print()


# ============================================================
# 2. TABLE EXISTENCE
# ============================================================

print("[02/18] Checking source table...")

table_exists = sql_one(
    f"""
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = '{DB_SCHEMA}'
          AND table_name = '{TABLE_NAME}'
    )
    """
)[0]

if not table_exists:
    raise RuntimeError(
        f"Source table {DB_SCHEMA}.{TABLE_NAME} does not exist."
    )

print(
    f"Source table {DB_SCHEMA}.{TABLE_NAME}: FOUND"
)
print()


# ============================================================
# 3. DATASET OVERVIEW
# ============================================================

print("[03/18] Auditing complete dataset size and financial totals...")

overview = sql_df(
    f"""
    SELECT
        COUNT(*) AS total_rows,

        COUNT(total_payment) AS rows_with_payment,

        COUNT(*) FILTER (
            WHERE transaction_date IS NOT NULL
        ) AS rows_with_transaction_date,

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

    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    overview,
    "01_dataset_overview.csv",
)

total_rows = int(overview.iloc[0]["total_rows"])

print(
    f"Total rows: {total_rows:,}"
)

print(
    f"Total payment: "
    f"{format_money(overview.iloc[0]['total_payment'])}"
)

print()


# ============================================================
# 4. COMPLETE COLUMN INVENTORY
# ============================================================

print("[04/18] Inspecting all columns...")

column_types = sql_df(
    f"""
    SELECT
        ordinal_position,
        column_name,
        data_type,
        is_nullable,
        character_maximum_length,
        numeric_precision,
        numeric_scale
    FROM information_schema.columns
    WHERE table_schema = '{DB_SCHEMA}'
      AND table_name = '{TABLE_NAME}'
    ORDER BY ordinal_position
    """
)

save_csv(
    column_types,
    "02_column_inventory.csv",
)

print(
    f"Columns found: {len(column_types)}"
)

print()


# ============================================================
# 5. MISSING VALUES
# ============================================================

print("[05/18] Auditing missing values...")

columns = column_types["column_name"].tolist()

missing_selects = []

for column in columns:
    safe_column = '"' + column.replace('"', '""') + '"'

    missing_selects.append(
        f"""
        SELECT
            '{column}' AS column_name,
            COUNT(*) FILTER (
                WHERE {safe_column} IS NULL
            ) AS missing_count,
            ROUND(
                100.0 *
                COUNT(*) FILTER (
                    WHERE {safe_column} IS NULL
                )
                / NULLIF(COUNT(*), 0),
                4
            ) AS missing_percentage
        FROM {DB_SCHEMA}.{TABLE_NAME}
        """
    )

missing_query = "\nUNION ALL\n".join(
    missing_selects
)

missing_values = sql_df(
    missing_query
)

missing_values = missing_values.sort_values(
    "missing_count",
    ascending=False,
)

save_csv(
    missing_values,
    "03_missing_values_by_column.csv",
)

print(
    "Columns audited:",
    len(missing_values),
)

print()


# ============================================================
# 6. IDENTIFIER UNIQUENESS
# ============================================================

print("[06/18] Auditing identifiers and uniqueness...")

identifier_candidates = [
    "primary_ticket_id",
    "subscription_instance_id",
    "sales_item_id",
    "product_item_id",
    "transaction_id",
    "product_id",
]

existing_identifiers = [
    column
    for column in identifier_candidates
    if column in columns
]

identifier_selects = [
    "COUNT(*) AS total_rows"
]

for column in existing_identifiers:
    identifier_selects.append(
        f"""
        COUNT(DISTINCT "{column}")
        AS unique_{column}
        """
    )

identifier_uniqueness = sql_df(
    f"""
    SELECT
        {', '.join(identifier_selects)}
    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    identifier_uniqueness,
    "04_identifier_uniqueness.csv",
)

print(
    "Identifiers audited:",
    ", ".join(existing_identifiers),
)

print()


# ============================================================
# 7. DUPLICATE SUMMARY
# ============================================================

print("[07/18] Auditing duplicate identifiers...")

duplicate_results = []

for column in existing_identifiers:

    query = f"""
        SELECT
            '{column}' AS identifier,

            COUNT(*) AS duplicate_rows,

            COUNT(DISTINCT "{column}") AS duplicate_groups

        FROM (
            SELECT
                "{column}"
            FROM {DB_SCHEMA}.{TABLE_NAME}

            WHERE "{column}" IS NOT NULL

            GROUP BY "{column}"

            HAVING COUNT(*) > 1
        ) duplicates
    """

    result = sql_one(query)

    duplicate_results.append(
        {
            "identifier": column,
            "duplicate_rows": result[1],
            "duplicate_groups": result[2],
        }
    )

duplicate_summary = pd.DataFrame(
    duplicate_results
)

save_csv(
    duplicate_summary,
    "05_duplicate_summary.csv",
)

print()


# ============================================================
# 8. FINANCIAL QUALITY
# ============================================================

print("[08/18] Auditing financial values...")

financial_anomalies = sql_df(
    f"""
    SELECT

        COUNT(*) FILTER (
            WHERE total_payment IS NULL
        ) AS null_payments,

        COUNT(*) FILTER (
            WHERE total_payment = 0
        ) AS zero_payments,

        COUNT(*) FILTER (
            WHERE total_payment < 0
        ) AS negative_payments,

        COUNT(*) FILTER (
            WHERE total_payment > 10000
        ) AS payments_over_10000,

        COUNT(*) FILTER (
            WHERE total_payment > 50000
        ) AS payments_over_50000,

        COUNT(*) FILTER (
            WHERE total_payment > 100000
        ) AS payments_over_100000,

        COUNT(*) FILTER (
            WHERE total_payment >= 0
        ) AS nonnegative_payments,

        SUM(total_payment) FILTER (
            WHERE total_payment < 0
        ) AS negative_payment_value,

        SUM(total_payment) FILTER (
            WHERE total_payment = 0
        ) AS zero_payment_value

    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    financial_anomalies,
    "06_financial_anomalies.csv",
)

print()


# ============================================================
# 9. STATISTICAL PAYMENT ANALYSIS
# ============================================================

print("[09/18] Calculating payment distribution statistics...")

payment_statistics = sql_df(
    f"""
    SELECT

        COUNT(total_payment) AS non_null_payments,

        MIN(total_payment) AS minimum_payment,

        PERCENTILE_CONT(0.01)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p01,

        PERCENTILE_CONT(0.05)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p05,

        PERCENTILE_CONT(0.25)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p25,

        PERCENTILE_CONT(0.50)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS median_payment,

        PERCENTILE_CONT(0.75)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p75,

        PERCENTILE_CONT(0.95)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p95,

        PERCENTILE_CONT(0.99)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p99,

        AVG(total_payment) AS mean_payment,

        STDDEV_POP(total_payment)
            AS payment_standard_deviation,

        MAX(total_payment)
            AS maximum_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE total_payment IS NOT NULL
    """
)

save_csv(
    payment_statistics,
    "07_payment_statistics.csv",
)

print()


# ============================================================
# 10. PRODUCT TYPE
# ============================================================

print("[10/18] Auditing product types...")

product_type = sql_df(
    f"""
    SELECT
        COALESCE(
            product_type,
            '[NULL]'
        ) AS product_type,

        COUNT(*) AS records,

        ROUND(
            100.0 * COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment) AS revenue,

        AVG(total_payment) AS average_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY
        product_type

    ORDER BY
        records DESC
    """
)

save_csv(
    product_type,
    "08_product_type.csv",
)

print()


# ============================================================
# 11. SALE TYPE
# ============================================================

print("[11/18] Auditing sale types...")

sale_type = sql_df(
    f"""
    SELECT
        COALESCE(
            sale_type,
            '[NULL]'
        ) AS sale_type,

        COUNT(*) AS records,

        ROUND(
            100.0 * COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment) AS revenue,

        AVG(total_payment) AS average_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY
        sale_type

    ORDER BY
        records DESC
    """
)

save_csv(
    sale_type,
    "09_sale_type.csv",
)

print()


# ============================================================
# 12. APPLICATION CHANNEL
# ============================================================

print("[12/18] Auditing application channels...")

application_channel = sql_df(
    f"""
    SELECT
        COALESCE(
            application_channel,
            '[NULL]'
        ) AS application_channel,

        COUNT(*) AS records,

        ROUND(
            100.0 * COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment) AS revenue,

        AVG(total_payment) AS average_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY
        application_channel

    ORDER BY
        records DESC
    """
)

save_csv(
    application_channel,
    "10_application_channel.csv",
)

print()


# ============================================================
# 13. HOSPITALITY
# ============================================================

print("[13/18] Auditing hospitality records...")

hospitality_column = (
    "is_hospitality"
    if "is_hospitality" in columns
    else None
)

if hospitality_column:

    hospitality = sql_df(
        f"""
        SELECT

            CASE
                WHEN is_hospitality IS NULL
                    THEN '[NULL]'

                WHEN is_hospitality
                    THEN 'Hospitality'

                ELSE 'Non-Hospitality'
            END AS hospitality_status,

            COUNT(*) AS records,

            SUM(total_payment) AS revenue,

            AVG(total_payment) AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY
            1

        ORDER BY
            records DESC
        """
    )

else:

    hospitality = pd.DataFrame(
        columns=[
            "hospitality_status",
            "records",
            "revenue",
            "average_payment",
        ]
    )

save_csv(
    hospitality,
    "11_hospitality.csv",
)

print()


# ============================================================
# 14. YEARLY TREND
# ============================================================

print("[14/18] Building yearly trend...")

yearly_trend = sql_df(
    f"""
    SELECT

        EXTRACT(
            YEAR FROM transaction_date
        )::INTEGER AS year,

        COUNT(*) AS records,

        SUM(total_payment) AS revenue,

        AVG(total_payment) AS average_payment,

        COUNT(DISTINCT transaction_id)
            AS unique_transactions

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE transaction_date IS NOT NULL

    GROUP BY
        1

    ORDER BY
        1
    """
)

save_csv(
    yearly_trend,
    "12_yearly_trend.csv",
)

print()


# ============================================================
# 15. MONTHLY TREND
# ============================================================

print("[15/18] Building monthly trend...")

monthly_trend = sql_df(
    f"""
    SELECT

        DATE_TRUNC(
            'month',
            transaction_date
        )::DATE AS month,

        COUNT(*) AS records,

        SUM(total_payment) AS revenue,

        AVG(total_payment) AS average_payment,

        COUNT(DISTINCT transaction_id)
            AS unique_transactions

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE transaction_date IS NOT NULL

    GROUP BY
        1

    ORDER BY
        1
    """
)

save_csv(
    monthly_trend,
    "13_monthly_trend.csv",
)

print()


# ============================================================
# 16. DATE CONSISTENCY
# ============================================================

print("[16/18] Checking date consistency...")

date_consistency = sql_df(
    f"""
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
        ) AS transaction_in_future,

        MIN(transaction_date)
            AS earliest_transaction,

        MAX(transaction_date)
            AS latest_transaction

    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    date_consistency,
    "14_date_consistency.csv",
)

print()


# ============================================================
# 17. TRANSFER / RESALE STATUS
# ============================================================

print("[17/18] Auditing transfer and resale status...")

if "transfer_status" in columns:

    transfer_status = sql_df(
        f"""
        SELECT
            COALESCE(
                transfer_status,
                '[NULL]'
            ) AS transfer_status,

            COUNT(*) AS records,

            SUM(total_payment) AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY
            1

        ORDER BY
            records DESC
        """
    )

else:

    transfer_status = pd.DataFrame()

save_csv(
    transfer_status,
    "15_transfer_status.csv",
)

if "resale_status" in columns:

    resale_status = sql_df(
        f"""
        SELECT
            COALESCE(
                resale_status,
                '[NULL]'
            ) AS resale_status,

            COUNT(*) AS records,

            SUM(total_payment) AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY
            1

        ORDER BY
            records DESC
        """
    )

else:

    resale_status = pd.DataFrame()

save_csv(
    resale_status,
    "16_resale_status.csv",
)

print()


# ============================================================
# 18. DATA GRAIN / BUSINESS DIMENSIONS
# ============================================================

print("[18/18] Assessing potential data grain...")

grain_dimensions = [
    column
    for column in [
        "product_type",
        "sale_type",
    ]
    if column in columns
]

if grain_dimensions:

    grain_group = ", ".join(
        f'"{column}"'
        for column in grain_dimensions
    )

    grain_select = ", ".join(
        f'"{column}"'
        for column in grain_dimensions
    )

    grain = sql_df(
        f"""
        SELECT

            {grain_select},

            COUNT(*) AS records,

            COUNT(
                DISTINCT primary_ticket_id
            ) AS unique_primary_ticket_ids,

            COUNT(
                DISTINCT sales_item_id
            ) AS unique_sales_item_ids,

            COUNT(
                DISTINCT transaction_id
            ) AS unique_transaction_ids,

            COUNT(
                DISTINCT subscription_instance_id
            ) AS unique_subscription_instances,

            SUM(total_payment) AS revenue

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY
            {grain_group}

        ORDER BY
            records DESC
        """
    )

else:

    grain = pd.DataFrame()

save_csv(
    grain,
    "17_potential_data_grain.csv",
)

print()


# ============================================================
# 19. TOP PRODUCT DESCRIPTIONS
# ============================================================

print("Building product description analysis...")

if "product_description" in columns:

    top_products = sql_df(
        f"""
        SELECT

            COALESCE(
                product_description,
                '[NULL]'
            ) AS product_description,

            COUNT(*) AS records,

            SUM(total_payment) AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY
            1

        ORDER BY
            records DESC

        LIMIT 100
        """
    )

else:

    top_products = pd.DataFrame()

save_csv(
    top_products,
    "18_top_product_descriptions.csv",
)


# ============================================================
# 20. DATA QUALITY SCORECARD
# ============================================================

print("Building data-quality scorecard...")

overview_row = overview.iloc[0]
financial_row = financial_anomalies.iloc[0]
date_row = date_consistency.iloc[0]

quality_checks = []


def add_check(
    area,
    status,
    finding,
    recommendation,
):
    quality_checks.append(
        {
            "area": area,
            "status": status,
            "finding": finding,
            "recommendation": recommendation,
        }
    )


# Row count

if total_rows == EXPECTED_EXACT_ROWS:

    add_check(
        "Dataset completeness",
        "PASS",
        f"Dataset contains exactly {total_rows:,} rows.",
        "Retain the complete dataset as the audit baseline.",
    )

elif total_rows >= EXPECTED_MIN_ROWS:

    add_check(
        "Dataset completeness",
        "REVIEW",
        f"Dataset contains {total_rows:,} rows.",
        "Confirm the expected source row count.",
    )

else:

    add_check(
        "Dataset completeness",
        "FAIL",
        f"Only {total_rows:,} rows were found.",
        "Verify the source load before using the audit.",
    )


# Payment nulls

null_payments = int(
    overview_row["null_payment"]
)

if null_payments == 0:

    add_check(
        "Payment completeness",
        "PASS",
        "No NULL total_payment values were detected.",
        "No action required.",
    )

else:

    add_check(
        "Payment completeness",
        "REVIEW",
        f"{null_payments:,} payment values are NULL.",
        "Investigate missing payment records.",
    )


# Negative payments

negative_payments = int(
    financial_row["negative_payments"]
)

if negative_payments == 0:

    add_check(
        "Negative payments",
        "PASS",
        "No negative payment values were detected.",
        "No action required.",
    )

else:

    add_check(
        "Negative payments",
        "REVIEW",
        f"{negative_payments:,} negative payments were detected.",
        "Determine whether negative values represent refunds or invalid data.",
    )


# Zero payments

zero_payments = int(
    financial_row["zero_payments"]
)

if zero_payments == 0:

    add_check(
        "Zero payments",
        "PASS",
        "No zero-payment records were detected.",
        "No action required.",
    )

else:

    add_check(
        "Zero payments",
        "REVIEW",
        f"{zero_payments:,} zero-payment records were detected.",
        "Determine whether zero values represent complimentary or non-revenue transactions.",
    )


# Dates

future_dates = int(
    date_row["transaction_in_future"]
)

if future_dates == 0:

    add_check(
        "Future transactions",
        "PASS",
        "No transaction dates occur after the current timestamp.",
        "No action required.",
    )

else:

    add_check(
        "Future transactions",
        "FAIL",
        f"{future_dates:,} transactions have future dates.",
        "Investigate system clock or source-data issues.",
    )


# Transaction after last touched

after_touch = int(
    date_row["transaction_after_last_touch"]
)

if after_touch == 0:

    add_check(
        "Date ordering",
        "PASS",
        "No transaction_date values occur after last_touched_at.",
        "No action required.",
    )

else:

    add_check(
        "Date ordering",
        "REVIEW",
        f"{after_touch:,} transactions occur after last_touched_at.",
        "Investigate timestamp semantics before treating this as an error.",
    )


# Identifier duplication

for _, row in duplicate_summary.iterrows():

    identifier = row["identifier"]
    groups = int(row["duplicate_groups"])

    if groups == 0:

        status = "PASS"

        finding = (
            f"No duplicate {identifier} groups were detected."
        )

        recommendation = "No action required."

    else:

        status = "REVIEW"

        finding = (
            f"{groups:,} duplicate {identifier} groups were detected."
        )

        recommendation = (
            "Determine whether repeated identifiers are expected "
            "at the dataset's business grain."
        )

    add_check(
        f"Identifier: {identifier}",
        status,
        finding,
        recommendation,
    )


quality_scorecard = pd.DataFrame(
    quality_checks
)

save_csv(
    quality_scorecard,
    "19_data_quality_scorecard.csv",
)


# ============================================================
# 21. EXECUTIVE SUMMARY
# ============================================================

print("Building executive summary...")

status_counts = (
    quality_scorecard["status"]
    .value_counts()
    .to_dict()
)

pass_count = status_counts.get(
    "PASS",
    0,
)

review_count = status_counts.get(
    "REVIEW",
    0,
)

fail_count = status_counts.get(
    "FAIL",
    0,
)

executive_summary = pd.DataFrame(
    [
        {
            "metric": "Total rows",
            "value": total_rows,
        },
        {
            "metric": "Earliest transaction",
            "value": str(
                overview_row["earliest_transaction"]
            ),
        },
        {
            "metric": "Latest transaction",
            "value": str(
                overview_row["latest_transaction"]
            ),
        },
        {
            "metric": "Total payment",
            "value": float(
                overview_row["total_payment"]
            ),
        },
        {
            "metric": "Average payment",
            "value": float(
                overview_row["average_payment"]
            ),
        },
        {
            "metric": "Minimum payment",
            "value": float(
                overview_row["minimum_payment"]
            ),
        },
        {
            "metric": "Maximum payment",
            "value": float(
                overview_row["maximum_payment"]
            ),
        },
        {
            "metric": "PASS checks",
            "value": pass_count,
        },
        {
            "metric": "REVIEW checks",
            "value": review_count,
        },
        {
            "metric": "FAIL checks",
            "value": fail_count,
        },
    ]
)

save_csv(
    executive_summary,
    "20_executive_summary.csv",
)


# ============================================================
# CHARTS
# ============================================================

print()
print("=" * 80)
print("GENERATING CHARTS")
print("=" * 80)


# ------------------------------------------------------------
# Chart 1 - Yearly Revenue
# ------------------------------------------------------------

if not yearly_trend.empty:

    plt.figure(figsize=(12, 6))

    plt.plot(
        yearly_trend["year"],
        yearly_trend["revenue"],
        marker="o",
    )

    plt.title(
        "Austin FC Revenue by Year"
    )

    plt.xlabel("Year")
    plt.ylabel("Revenue")

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "01_yearly_revenue.png",
        dpi=180,
    )

    plt.close()


# ------------------------------------------------------------
# Chart 2 - Yearly Records
# ------------------------------------------------------------

if not yearly_trend.empty:

    plt.figure(figsize=(12, 6))

    plt.bar(
        yearly_trend["year"].astype(str),
        yearly_trend["records"],
    )

    plt.title(
        "Austin FC Records by Year"
    )

    plt.xlabel("Year")
    plt.ylabel("Records")

    plt.xticks(
        rotation=45
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "02_yearly_records.png",
        dpi=180,
    )

    plt.close()


# ------------------------------------------------------------
# Chart 3 - Monthly Revenue
# ------------------------------------------------------------

if not monthly_trend.empty:

    monthly_plot = monthly_trend.copy()

    monthly_plot["month"] = pd.to_datetime(
        monthly_plot["month"]
    )

    plt.figure(figsize=(14, 6))

    plt.plot(
        monthly_plot["month"],
        monthly_plot["revenue"],
    )

    plt.title(
        "Austin FC Monthly Revenue"
    )

    plt.xlabel("Month")
    plt.ylabel("Revenue")

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "03_monthly_revenue.png",
        dpi=180,
    )

    plt.close()


# ------------------------------------------------------------
# Chart 4 - Product Types
# ------------------------------------------------------------

if not product_type.empty:

    chart_data = product_type.head(15)

    plt.figure(figsize=(12, 7))

    plt.barh(
        chart_data["product_type"].astype(str),
        chart_data["records"],
    )

    plt.title(
        "Top Product Types by Record Count"
    )

    plt.xlabel("Records")

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "04_product_types.png",
        dpi=180,
    )

    plt.close()


# ------------------------------------------------------------
# Chart 5 - Sale Types
# ------------------------------------------------------------

if not sale_type.empty:

    chart_data = sale_type.head(15)

    plt.figure(figsize=(12, 7))

    plt.barh(
        chart_data["sale_type"].astype(str),
        chart_data["records"],
    )

    plt.title(
        "Sale Types by Record Count"
    )

    plt.xlabel("Records")

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "05_sale_types.png",
        dpi=180,
    )

    plt.close()


# ------------------------------------------------------------
# Chart 6 - Payment Distribution
# ------------------------------------------------------------

if not payment_statistics.empty:

    stats = payment_statistics.iloc[0]

    values = [
        stats["p01"],
        stats["p05"],
        stats["p25"],
        stats["median_payment"],
        stats["p75"],
        stats["p95"],
        stats["p99"],
    ]

    labels = [
        "P01",
        "P05",
        "P25",
        "Median",
        "P75",
        "P95",
        "P99",
    ]

    plt.figure(figsize=(12, 6))

    plt.plot(
        labels,
        values,
        marker="o",
    )

    plt.title(
        "Payment Distribution Percentiles"
    )

    plt.xlabel("Percentile")
    plt.ylabel("Payment")

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "06_payment_percentiles.png",
        dpi=180,
    )

    plt.close()


# ============================================================
# MARKDOWN REPORT
# ============================================================

print("Generating Markdown report...")

report_path = (
    RESULTS_DIR /
    "austin_fc_comprehensive_audit_report.md"
)

report_lines = []

report_lines.append(
    "# Austin FC Sales Data — Comprehensive Audit"
)

report_lines.append("")

report_lines.append(
    f"Audit generated: {datetime.now().isoformat(timespec='seconds')}"
)

report_lines.append("")

report_lines.append("## 1. Executive Summary")

report_lines.append("")

report_lines.append(
    f"- **Total rows:** {total_rows:,}"
)

report_lines.append(
    f"- **Earliest transaction:** "
    f"{overview_row['earliest_transaction']}"
)

report_lines.append(
    f"- **Latest transaction:** "
    f"{overview_row['latest_transaction']}"
)

report_lines.append(
    f"- **Total payment:** "
    f"{format_money(overview_row['total_payment'])}"
)

report_lines.append(
    f"- **Average payment:** "
    f"{format_money(overview_row['average_payment'])}"
)

report_lines.append(
    f"- **Minimum payment:** "
    f"{format_money(overview_row['minimum_payment'])}"
)

report_lines.append(
    f"- **Maximum payment:** "
    f"{format_money(overview_row['maximum_payment'])}"
)

report_lines.append("")

report_lines.append(
    "The audit was performed against the complete PostgreSQL "
    "source table. The source table was not sampled."
)

report_lines.append("")

report_lines.append("## 2. Dataset Completeness")

report_lines.append("")

if total_rows == EXPECTED_EXACT_ROWS:

    report_lines.append(
        f"PASS — The database contains exactly "
        f"**{total_rows:,} rows**, matching the verified "
        f"full dataset size."
    )

else:

    report_lines.append(
        f"REVIEW — The database contains "
        f"**{total_rows:,} rows**."
    )

report_lines.append("")

report_lines.append("## 3. Data Quality Scorecard")

report_lines.append("")

report_lines.append(
    f"- PASS checks: **{pass_count}**"
)

report_lines.append(
    f"- REVIEW checks: **{review_count}**"
)

report_lines.append(
    f"- FAIL checks: **{fail_count}**"
)

report_lines.append("")

report_lines.append(
    "| Area | Status | Finding | Recommendation |"
)

report_lines.append(
    "|---|---|---|---|"
)

for _, row in quality_scorecard.iterrows():

    finding = str(
        row["finding"]
    ).replace("|", "/")

    recommendation = str(
        row["recommendation"]
    ).replace("|", "/")

    report_lines.append(
        f"| {row['area']} | "
        f"{row['status']} | "
        f"{finding} | "
        f"{recommendation} |"
    )

report_lines.append("")

report_lines.append(
    "## 4. Missing Values"
)

report_lines.append("")

report_lines.append(
    "Missing-value analysis is available in "
    "`tables/03_missing_values_by_column.csv`."
)

report_lines.append("")

report_lines.append(
    "## 5. Financial Quality"
)

report_lines.append("")

report_lines.append(
    f"- NULL payments: "
    f"**{int(overview_row['null_payment']):,}**"
)

report_lines.append(
    f"- Zero payments: "
    f"**{int(overview_row['zero_payment']):,}**"
)

report_lines.append(
    f"- Negative payments: "
    f"**{int(overview_row['negative_payment']):,}**"
)

report_lines.append(
    f"- Payments above $10,000: "
    f"**{int(financial_row['payments_over_10000']):,}**"
)

report_lines.append(
    f"- Payments above $50,000: "
    f"**{int(financial_row['payments_over_50000']):,}**"
)

report_lines.append(
    f"- Payments above $100,000: "
    f"**{int(financial_row['payments_over_100000']):,}**"
)

report_lines.append("")

report_lines.append(
    "Payment percentile statistics are available in "
    "`tables/07_payment_statistics.csv`."
)

report_lines.append("")

report_lines.append(
    "## 6. Identifier Analysis"
)

report_lines.append("")

for _, row in duplicate_summary.iterrows():

    report_lines.append(
        f"- **{row['identifier']}**: "
        f"{int(row['duplicate_groups']):,} duplicate groups"
    )

report_lines.append("")

report_lines.append(
    "Duplicate identifiers are not automatically data errors. "
    "Their interpretation depends on the business grain of the "
    "source system."
)

report_lines.append("")

report_lines.append(
    "## 7. Time Analysis"
)

report_lines.append("")

report_lines.append(
    "Yearly and monthly trends were calculated directly from "
    "the PostgreSQL source table."
)

report_lines.append("")

report_lines.append(
    "## 8. Date Consistency"
)

report_lines.append("")

report_lines.append(
    f"- Missing transaction dates: "
    f"{int(date_row['missing_transaction_date']):,}"
)

report_lines.append(
    f"- Missing last-touched dates: "
    f"{int(date_row['missing_last_touched_at']):,}"
)

report_lines.append(
    f"- Transaction after last-touch timestamp: "
    f"{int(date_row['transaction_after_last_touch']):,}"
)

report_lines.append(
    f"- Transactions before 2010: "
    f"{int(date_row['transaction_before_2010']):,}"
)

report_lines.append(
    f"- Future transactions: "
    f"{int(date_row['transaction_in_future']):,}"
)

report_lines.append("")

report_lines.append(
    "## 9. Generated Outputs"
)

report_lines.append("")

report_lines.append(
    "The audit generates aggregate CSV tables and charts "
    "for team review."
)

report_lines.append("")

report_lines.append(
    "Transaction-level identifier exports are intentionally "
    "excluded from the published audit."
)

report_lines.append("")

report_lines.append(
    "## 10. Reproducibility"
)

report_lines.append("")

report_lines.append(
    "The audit uses PostgreSQL for large-scale aggregation "
    "and Python for reporting. This prevents the complete "
    "5.3M-row source table from being loaded into memory at once."
)

report_lines.append("")

report_lines.append(
    "The source database credentials are stored in `.env` "
    "and are not included in the repository."
)

report_lines.append("")

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)


# ============================================================
# HTML DASHBOARD
# ============================================================

print("Generating HTML dashboard...")

html_path = (
    RESULTS_DIR /
    "austin_fc_comprehensive_audit.html"
)

html = f"""
<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Austin FC Comprehensive Data Audit</title>

<style>

body {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    margin: 0;
    background: #f5f7fa;
    color: #1f2937;
}}

header {{
    background: #111827;
    color: white;
    padding: 40px;
}}

header h1 {{
    margin: 0 0 10px 0;
}}

.container {{
    max-width: 1200px;
    margin: auto;
    padding: 30px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(220px, 1fr)
        );

    gap: 20px;
}}

.card {{
    background: white;
    border-radius: 10px;
    padding: 22px;
    box-shadow:
        0 2px 8px
        rgba(0,0,0,0.08);
}}

.metric {{
    font-size: 28px;
    font-weight: bold;
}}

.label {{
    color: #6b7280;
    margin-top: 6px;
}}

section {{
    margin-top: 35px;
}}

img {{
    max-width: 100%;
    height: auto;
    background: white;
    padding: 10px;
    border-radius: 8px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

th,
td {{
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}}

th {{
    background: #f3f4f6;
}}

.pass {{
    font-weight: bold;
}}

.review {{
    font-weight: bold;
}}

.fail {{
    font-weight: bold;
}}

.small {{
    color: #6b7280;
}}

</style>

</head>

<body>

<header>

<h1>Austin FC Sales Data Audit</h1>

<p>
Comprehensive audit of the complete PostgreSQL dataset
</p>

<p class="small">
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
</p>

</header>

<div class="container">

<section>

<h2>Executive Summary</h2>

<div class="grid">

<div class="card">
<div class="metric">
{total_rows:,}
</div>
<div class="label">
Total Records
</div>
</div>

<div class="card">
<div class="metric">
{format_money(overview_row['total_payment'])}
</div>
<div class="label">
Total Payment
</div>
</div>

<div class="card">
<div class="metric">
{format_money(overview_row['average_payment'])}
</div>
<div class="label">
Average Payment
</div>
</div>

<div class="card">
<div class="metric">
{pass_count}
</div>
<div class="label">
PASS Checks
</div>
</div>

<div class="card">
<div class="metric">
{review_count}
</div>
<div class="label">
REVIEW Checks
</div>
</div>

<div class="card">
<div class="metric">
{fail_count}
</div>
<div class="label">
FAIL Checks
</div>
</div>

</div>

</section>

<section>

<h2>Dataset Coverage</h2>

<div class="card">

<p>
<b>Earliest transaction:</b>
{overview_row['earliest_transaction']}
</p>

<p>
<b>Latest transaction:</b>
{overview_row['latest_transaction']}
</p>

<p>
<b>Minimum payment:</b>
{format_money(overview_row['minimum_payment'])}
</p>

<p>
<b>Maximum payment:</b>
{format_money(overview_row['maximum_payment'])}
</p>

<p>
<b>NULL payments:</b>
{int(overview_row['null_payment']):,}
</p>

<p>
<b>Zero payments:</b>
{int(overview_row['zero_payment']):,}
</p>

<p>
<b>Negative payments:</b>
{int(overview_row['negative_payment']):,}
</p>

</div>

</section>

<section>

<h2>Data Quality Scorecard</h2>

<table>

<thead>

<tr>
<th>Area</th>
<th>Status</th>
<th>Finding</th>
<th>Recommendation</th>
</tr>

</thead>

<tbody>
"""

for _, row in quality_scorecard.iterrows():

    html += f"""
<tr>

<td>
{row['area']}
</td>

<td class="{str(row['status']).lower()}">
{row['status']}
</td>

<td>
{row['finding']}
</td>

<td>
{row['recommendation']}
</td>

</tr>
"""


html += """
</tbody>

</table>

</section>

<section>

<h2>Yearly Revenue</h2>

<img
src="charts/01_yearly_revenue.png"
alt="Yearly revenue chart">

</section>

<section>

<h2>Yearly Records</h2>

<img
src="charts/02_yearly_records.png"
alt="Yearly records chart">

</section>

<section>

<h2>Monthly Revenue</h2>

<img
src="charts/03_monthly_revenue.png"
alt="Monthly revenue chart">

</section>

<section>

<h2>Product Types</h2>

<img
src="charts/04_product_types.png"
alt="Product types chart">

</section>

<section>

<h2>Sale Types</h2>

<img
src="charts/05_sale_types.png"
alt="Sale types chart">

</section>

<section>

<h2>Payment Distribution</h2>

<img
src="charts/06_payment_percentiles.png"
alt="Payment distribution chart">

</section>

<section>

<h2>Audit Methodology</h2>

<div class="card">

<p>
This audit was performed against the complete PostgreSQL
source table.
</p>

<p>
The audit does not load all source records into pandas.
Large aggregations are performed by PostgreSQL and only
small aggregate result sets are transferred to Python.
</p>

<p>
The source dataset contains more than five million records.
Transaction-level exports are intentionally excluded from
the published audit.
</p>

</div>

</section>

</div>

</body>

</html>
"""

html_path.write_text(
    html,
    encoding="utf-8",
)


# ============================================================
# FINAL VERIFICATION
# ============================================================

finished_at = datetime.now()

elapsed = (
    finished_at - started_at
).total_seconds()

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
print()
print(
    f"Rows audited: {total_rows:,}"
)
print(
    f"Elapsed time: {elapsed:.2f} seconds"
)
print()
print("Reports:")
print(
    f"  {report_path}"
)
print(
    f"  {html_path}"
)
print()
print("Tables:")
print(
    f"  {TABLES_DIR}"
)
print()
print("Charts:")
print(
    f"  {CHARTS_DIR}"
)
print()
print(
    "IMPORTANT: The complete source dataset was audited "
    "through PostgreSQL aggregation."
)
print()


# ============================================================
# DATABASE CLEANUP
# ============================================================

engine.dispose()
