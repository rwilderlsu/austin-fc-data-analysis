#!/usr/bin/env python3

"""
Austin FC Sales Data
Comprehensive Data Quality, Business Performance,
Anomaly and Revenue Audit

Purpose
-------
Audit the complete Austin FC sales-history dataset in PostgreSQL.

Design
------
The source contains more than 5 million records.

The complete source table is NOT loaded into pandas.

Instead:

    PostgreSQL
        |
        +-- full-table aggregation
        |
        +-- statistical analysis
        |
        +-- business KPI calculations
        |
        +-- small pandas result sets
        |
        +-- CSV outputs
        +-- charts
        +-- Markdown report
        +-- HTML dashboard

Current authoritative source table:

    austin_fc_sales_history_updated_2026_09_24

Verified dataset:

    5,335,362 rows

Transaction coverage:

    2019-08-15 through 2026-09-24

Important
---------
September 2026 is a partial month because the source data ends
on September 24, 2026.

The audit identifies anomalies and business risks for investigation.
It does not automatically classify unusual transactions as fraud
or data errors.
"""

from __future__ import annotations

import os
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
TABLES_DIR = RESULTS_DIR / "tables"
CHARTS_DIR = RESULTS_DIR / "charts"
AUDIT_DIR = RESULTS_DIR / "audit"

DB_SCHEMA = "public"

TABLE_NAME = (
    "austin_fc_sales_history_updated_2026_09_24"
)

EXPECTED_MIN_ROWS = 5_000_000

EXPECTED_EXACT_ROWS = 5_335_362

# September 2026 is intentionally treated as partial.
PARTIAL_MONTH = "2026-09"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)

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
# DATABASE
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
# DIRECTORIES
# ============================================================

for directory in [
    RESULTS_DIR,
    TABLES_DIR,
    CHARTS_DIR,
    AUDIT_DIR,
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
        result = connection.execute(
            text(query)
        )

        return result.fetchone()


def save_csv(
    dataframe: pd.DataFrame,
    filename: str,
) -> Path:

    path = TABLES_DIR / filename

    dataframe.to_csv(
        path,
        index=False,
    )

    return path


def money(value) -> str:

    if value is None or pd.isna(value):
        return "$0.00"

    return f"${float(value):,.2f}"


def number(value) -> str:

    if value is None or pd.isna(value):
        return "0"

    return f"{int(value):,}"


def pct(value) -> str:

    if value is None or pd.isna(value):
        return "0.00%"

    return f"{float(value):.2f}%"


def safe_column(column: str) -> str:

    return '"' + column.replace('"', '""') + '"'


def safe_text(value) -> str:

    return str(value).replace(
        "|",
        "/",
    )


# ============================================================
# START
# ============================================================

started_at = datetime.now()

print()
print("=" * 90)
print("AUSTIN FC COMPREHENSIVE SALES DATA AUDIT")
print("=" * 90)
print()

print(
    "Project:",
    PROJECT_ROOT,
)

print(
    "Database:",
    os.environ["DB_NAME"],
)

print(
    "Table:",
    f"{DB_SCHEMA}.{TABLE_NAME}",
)

print()

print(
    "Full-table PostgreSQL analysis enabled."
)

print(
    "The complete source table will NOT be loaded into pandas."
)

print()


# ============================================================
# 01. CONNECTION
# ============================================================

print("[01] Testing PostgreSQL connection...")

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

print(
    "Database:",
    database_name,
)

print(
    "User:",
    database_user,
)

print("Connection: OK")

print()


# ============================================================
# 02. TABLE EXISTENCE
# ============================================================

print("[02] Checking source table...")

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
        f"Source table "
        f"{DB_SCHEMA}.{TABLE_NAME} does not exist."
    )

print("Source table: FOUND")

print()


# ============================================================
# 03. DATASET OVERVIEW
# ============================================================

print("[03] Auditing complete dataset...")

overview = sql_df(
    f"""
    SELECT

        COUNT(*) AS total_rows,

        COUNT(total_payment)
            AS rows_with_payment,

        COUNT(transaction_date)
            AS rows_with_transaction_date,

        MIN(transaction_date)
            AS earliest_transaction,

        MAX(transaction_date)
            AS latest_transaction,

        SUM(total_payment)
            AS total_revenue,

        AVG(total_payment)
            AS average_payment,

        MIN(total_payment)
            AS minimum_payment,

        MAX(total_payment)
            AS maximum_payment,

        STDDEV_POP(total_payment)
            AS payment_stddev,

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

overview_row = overview.iloc[0]

total_rows = int(
    overview_row["total_rows"]
)

print(
    "Rows:",
    f"{total_rows:,}",
)

print(
    "Revenue:",
    money(overview_row["total_revenue"]),
)

print(
    "Date range:",
    overview_row["earliest_transaction"],
    "to",
    overview_row["latest_transaction"],
)

print()


# ============================================================
# 04. COLUMN INVENTORY
# ============================================================

print("[04] Inspecting columns...")

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

columns = column_types[
    "column_name"
].tolist()

print(
    "Columns:",
    len(columns),
)

print()


# ============================================================
# 05. MISSINGNESS
# ============================================================

print("[05] Auditing missing values...")

missing_queries = []

for column in columns:

    quoted = safe_column(column)

    missing_queries.append(
        f"""
        SELECT

            '{column}' AS column_name,

            COUNT(*) FILTER (
                WHERE {quoted} IS NULL
            ) AS missing_count,

            ROUND(
                100.0 *
                COUNT(*) FILTER (
                    WHERE {quoted} IS NULL
                )
                / NULLIF(COUNT(*), 0),
                4
            ) AS missing_percentage

        FROM {DB_SCHEMA}.{TABLE_NAME}
        """
    )

missing_values = sql_df(
    "\nUNION ALL\n".join(
        missing_queries
    )
)

missing_values = missing_values.sort_values(
    "missing_count",
    ascending=False,
)

save_csv(
    missing_values,
    "03_missing_values_by_column.csv",
)

print()


# ============================================================
# 06. MISSINGNESS BY PRODUCT TYPE
# ============================================================

print(
    "[06] Analyzing missingness by product type..."
)

if "product_type" in columns:

    missing_by_product = sql_df(
        f"""
        SELECT

            product_type,

            COUNT(*) AS total_records,

            COUNT(*) FILTER (
                WHERE primary_ticket_id IS NULL
            ) AS missing_primary_ticket_id,

            COUNT(*) FILTER (
                WHERE subscription_instance_id IS NULL
            ) AS missing_subscription_instance_id,

            COUNT(*) FILTER (
                WHERE section IS NULL
            ) AS missing_section,

            COUNT(*) FILTER (
                WHERE row IS NULL
            ) AS missing_row,

            COUNT(*) FILTER (
                WHERE seat IS NULL
            ) AS missing_seat

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY product_type

        ORDER BY total_records DESC
        """
    )

else:

    missing_by_product = pd.DataFrame()

save_csv(
    missing_by_product,
    "04_missingness_by_product_type.csv",
)


# ============================================================
# 07. IDENTIFIER UNIQUENESS
# ============================================================

print("[07] Auditing identifiers...")

identifier_candidates = [
    "primary_ticket_id",
    "subscription_instance_id",
    "sales_item_id",
    "product_item_id",
    "transaction_id",
    "product_id",
    "internal_account_id",
]

existing_identifiers = [
    column
    for column in identifier_candidates
    if column in columns
]

identifier_results = []

for column in existing_identifiers:

    quoted = safe_column(column)

    result = sql_one(
        f"""
        SELECT

            COUNT(*) AS total_rows,

            COUNT({quoted})
                AS non_null_rows,

            COUNT(DISTINCT {quoted})
                AS distinct_values,

            COUNT(*) -
            COUNT(DISTINCT {quoted})
                AS repeated_value_count

        FROM {DB_SCHEMA}.{TABLE_NAME}

        WHERE {quoted} IS NOT NULL
        """
    )

    identifier_results.append(
        {
            "identifier": column,
            "total_rows": result[0],
            "non_null_rows": result[1],
            "distinct_values": result[2],
            "repeated_value_count": result[3],
        }
    )

identifier_uniqueness = pd.DataFrame(
    identifier_results
)

save_csv(
    identifier_uniqueness,
    "05_identifier_uniqueness.csv",
)


# ============================================================
# 08. DUPLICATE IDENTIFIERS
# ============================================================

print("[08] Auditing duplicate identifiers...")

duplicate_results = []

for column in existing_identifiers:

    quoted = safe_column(column)

    result = sql_one(
        f"""
        SELECT

            COUNT(*) AS duplicate_rows,

            COUNT(*) -
            COUNT(DISTINCT {quoted})
                AS repeated_rows

        FROM {DB_SCHEMA}.{TABLE_NAME}

        WHERE {quoted} IS NOT NULL
        """
    )

    duplicate_results.append(
        {
            "identifier": column,
            "duplicate_rows": result[0],
            "repeated_rows": result[1],
        }
    )

duplicate_summary = pd.DataFrame(
    duplicate_results
)

save_csv(
    duplicate_summary,
    "06_duplicate_identifier_summary.csv",
)


# ============================================================
# 09. EXACT DUPLICATE TRANSACTIONS
# ============================================================

print("[09] Searching for duplicate transaction IDs...")

if "transaction_id" in columns:

    duplicate_transactions = sql_df(
        f"""
        SELECT

            transaction_id,

            COUNT(*) AS record_count,

            SUM(total_payment)
                AS combined_payment,

            MIN(transaction_date)
                AS first_transaction,

            MAX(transaction_date)
                AS last_transaction

        FROM {DB_SCHEMA}.{TABLE_NAME}

        WHERE transaction_id IS NOT NULL

        GROUP BY transaction_id

        HAVING COUNT(*) > 1

        ORDER BY record_count DESC

        LIMIT 10000
        """
    )

else:

    duplicate_transactions = pd.DataFrame()

save_csv(
    duplicate_transactions,
    "07_duplicate_transactions.csv",
)


# ============================================================
# 10. FINANCIAL QUALITY
# ============================================================

print("[10] Auditing financial values...")

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

        SUM(total_payment) FILTER (
            WHERE total_payment < 0
        ) AS negative_payment_value,

        SUM(total_payment) FILTER (
            WHERE total_payment = 0
        ) AS zero_payment_value,

        SUM(total_payment) FILTER (
            WHERE total_payment > 100000
        ) AS payments_over_100000_value

    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    financial_anomalies,
    "08_financial_anomalies.csv",
)

financial_row = financial_anomalies.iloc[0]


# ============================================================
# 11. PAYMENT DISTRIBUTION
# ============================================================

print("[11] Calculating payment statistics...")

payment_statistics = sql_df(
    f"""
    SELECT

        COUNT(total_payment)
            AS non_null_payments,

        MIN(total_payment)
            AS minimum_payment,

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

        PERCENTILE_CONT(0.90)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p90,

        PERCENTILE_CONT(0.95)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p95,

        PERCENTILE_CONT(0.99)
            WITHIN GROUP (
                ORDER BY total_payment
            ) AS p99,

        AVG(total_payment)
            AS mean_payment,

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
    "09_payment_statistics.csv",
)


# ============================================================
# 12. OUTLIER TRANSACTIONS
# ============================================================

print("[12] Identifying high-value transactions...")

high_value_transactions = sql_df(
    f"""
    SELECT

        transaction_id,

        transaction_date,

        product_type,

        sale_type,

        application_channel,

        product_description,

        total_payment,

        primary_ticket_id,

        subscription_instance_id,

        internal_account_id

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE total_payment IS NOT NULL

    ORDER BY total_payment DESC

    LIMIT 500
    """
)

save_csv(
    high_value_transactions,
    "10_high_value_transactions.csv",
)


# ============================================================
# 13. PRODUCT TYPE
# ============================================================

print("[13] Analyzing product types...")

product_type = sql_df(
    f"""
    SELECT

        COALESCE(
            product_type,
            '[NULL]'
        ) AS product_type,

        COUNT(*) AS records,

        ROUND(
            100.0 *
            COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment)
            AS revenue,

        ROUND(
            100.0 *
            SUM(total_payment) /
            NULLIF(
                SUM(SUM(total_payment))
                OVER (),
                0
            ),
            4
        ) AS revenue_percentage,

        AVG(total_payment)
            AS average_payment,

        MIN(total_payment)
            AS minimum_payment,

        MAX(total_payment)
            AS maximum_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY product_type

    ORDER BY revenue DESC
    """
)

save_csv(
    product_type,
    "11_product_type_performance.csv",
)


# ============================================================
# 14. SALE TYPE
# ============================================================

print("[14] Analyzing sale types...")

sale_type = sql_df(
    f"""
    SELECT

        COALESCE(
            sale_type,
            '[NULL]'
        ) AS sale_type,

        COUNT(*) AS records,

        ROUND(
            100.0 *
            COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment)
            AS revenue,

        ROUND(
            100.0 *
            SUM(total_payment) /
            NULLIF(
                SUM(SUM(total_payment))
                OVER (),
                0
            ),
            4
        ) AS revenue_percentage,

        AVG(total_payment)
            AS average_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY sale_type

    ORDER BY revenue DESC
    """
)

save_csv(
    sale_type,
    "12_sale_type_performance.csv",
)


# ============================================================
# 15. APPLICATION CHANNEL
# ============================================================

print("[15] Analyzing application channels...")

application_channel = sql_df(
    f"""
    SELECT

        COALESCE(
            application_channel,
            '[NULL]'
        ) AS application_channel,

        COUNT(*) AS records,

        ROUND(
            100.0 *
            COUNT(*) /
            SUM(COUNT(*)) OVER (),
            4
        ) AS record_percentage,

        SUM(total_payment)
            AS revenue,

        ROUND(
            100.0 *
            SUM(total_payment) /
            NULLIF(
                SUM(SUM(total_payment))
                OVER (),
                0
            ),
            4
        ) AS revenue_percentage,

        AVG(total_payment)
            AS average_payment

    FROM {DB_SCHEMA}.{TABLE_NAME}

    GROUP BY application_channel

    ORDER BY revenue DESC
    """
)

save_csv(
    application_channel,
    "13_application_channel_performance.csv",
)


# ============================================================
# 16. HOSPITALITY
# ============================================================

print("[16] Analyzing hospitality...")

if "is_hospitality" in columns:

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

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY revenue DESC
        """
    )

else:

    hospitality = pd.DataFrame()

save_csv(
    hospitality,
    "14_hospitality_performance.csv",
)


# ============================================================
# 17. PRICE LEVEL
# ============================================================

print("[17] Analyzing price levels...")

if "price_level" in columns:

    price_level = sql_df(
        f"""
        SELECT

            COALESCE(
                price_level,
                '[NULL]'
            ) AS price_level,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY revenue DESC
        """
    )

else:

    price_level = pd.DataFrame()

save_csv(
    price_level,
    "15_price_level_performance.csv",
)


# ============================================================
# 18. PRICE TYPE
# ============================================================

print("[18] Analyzing price types...")

if "price_type" in columns:

    price_type = sql_df(
        f"""
        SELECT

            COALESCE(
                price_type,
                '[NULL]'
            ) AS price_type,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY revenue DESC
        """
    )

else:

    price_type = pd.DataFrame()

save_csv(
    price_type,
    "16_price_type_performance.csv",
)


# ============================================================
# 19. SALES REPRESENTATIVE
# ============================================================

print("[19] Analyzing sales representatives...")

if "sales_rep" in columns:

    sales_rep = sql_df(
        f"""
        SELECT

            COALESCE(
                sales_rep,
                '[NULL]'
            ) AS sales_rep,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment,

            COUNT(
                DISTINCT internal_account_id
            ) AS accounts

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY revenue DESC
        """
    )

else:

    sales_rep = pd.DataFrame()

save_csv(
    sales_rep,
    "17_sales_representative_performance.csv",
)


# ============================================================
# 20. TRANSFER STATUS
# ============================================================

print("[20] Analyzing transfer status...")

if "transfer_status" in columns:

    transfer_status = sql_df(
        f"""
        SELECT

            COALESCE(
                transfer_status,
                '[NULL]'
            ) AS transfer_status,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY records DESC
        """
    )

else:

    transfer_status = pd.DataFrame()

save_csv(
    transfer_status,
    "18_transfer_status.csv",
)


# ============================================================
# 21. RESALE STATUS
# ============================================================

print("[21] Analyzing resale status...")

if "resale_status" in columns:

    resale_status = sql_df(
        f"""
        SELECT

            COALESCE(
                resale_status,
                '[NULL]'
            ) AS resale_status,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY records DESC
        """
    )

else:

    resale_status = pd.DataFrame()

save_csv(
    resale_status,
    "19_resale_status.csv",
)


# ============================================================
# 22. MONTHLY TREND
# ============================================================

print("[22] Building monthly trend...")

monthly_trend = sql_df(
    f"""
    SELECT

        DATE_TRUNC(
            'month',
            transaction_date
        )::DATE AS month,

        COUNT(*) AS records,

        SUM(total_payment)
            AS revenue,

        AVG(total_payment)
            AS average_payment,

        COUNT(
            DISTINCT transaction_id
        ) AS unique_transactions

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE transaction_date IS NOT NULL

    GROUP BY 1

    ORDER BY 1
    """
)

save_csv(
    monthly_trend,
    "20_monthly_trend.csv",
)


# ============================================================
# 23. YEARLY TREND
# ============================================================

print("[23] Building yearly trend...")

yearly_trend = sql_df(
    f"""
    SELECT

        EXTRACT(
            YEAR FROM transaction_date
        )::INTEGER AS year,

        COUNT(*) AS records,

        SUM(total_payment)
            AS revenue,

        AVG(total_payment)
            AS average_payment,

        COUNT(
            DISTINCT transaction_id
        ) AS unique_transactions

    FROM {DB_SCHEMA}.{TABLE_NAME}

    WHERE transaction_date IS NOT NULL

    GROUP BY 1

    ORDER BY 1
    """
)

save_csv(
    yearly_trend,
    "21_yearly_trend.csv",
)


# ============================================================
# 24. DATE CONSISTENCY
# ============================================================

print("[24] Checking date consistency...")

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
            WHERE transaction_date >
                  last_touched_at
        ) AS transaction_after_last_touch,

        COUNT(*) FILTER (
            WHERE transaction_date <
                  TIMESTAMP '2010-01-01'
        ) AS transaction_before_2010,

        MIN(transaction_date)
            AS earliest_transaction,

        MAX(transaction_date)
            AS latest_transaction

    FROM {DB_SCHEMA}.{TABLE_NAME}
    """
)

save_csv(
    date_consistency,
    "22_date_consistency.csv",
)

date_row = date_consistency.iloc[0]


# ============================================================
# 25. PRODUCT DESCRIPTIONS
# ============================================================

print("[25] Analyzing product descriptions...")

if "product_description" in columns:

    top_products = sql_df(
        f"""
        SELECT

            COALESCE(
                product_description,
                '[NULL]'
            ) AS product_description,

            COUNT(*) AS records,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment

        FROM {DB_SCHEMA}.{TABLE_NAME}

        GROUP BY 1

        ORDER BY revenue DESC

        LIMIT 500
        """
    )

else:

    top_products = pd.DataFrame()

save_csv(
    top_products,
    "23_product_description_performance.csv",
)


# ============================================================
# 26. ACCOUNT ACTIVITY
# ============================================================

print("[26] Analyzing internal accounts...")

if "internal_account_id" in columns:

    account_activity = sql_df(
        f"""
        SELECT

            internal_account_id,

            COUNT(*) AS transactions,

            SUM(total_payment)
                AS revenue,

            AVG(total_payment)
                AS average_payment,

            MIN(transaction_date)
                AS first_transaction,

            MAX(transaction_date)
                AS last_transaction

        FROM {DB_SCHEMA}.{TABLE_NAME}

        WHERE internal_account_id IS NOT NULL

        GROUP BY internal_account_id

        ORDER BY revenue DESC

        LIMIT 10000
        """
    )

else:

    account_activity = pd.DataFrame()

save_csv(
    account_activity,
    "24_top_account_activity.csv",
)


# ============================================================
# 27. REVENUE CONCENTRATION
# ============================================================

print("[27] Measuring revenue concentration...")

if "internal_account_id" in columns:

    revenue_concentration = sql_df(
        f"""
        WITH account_revenue AS (

            SELECT

                internal_account_id,

                SUM(total_payment)
                    AS revenue

            FROM {DB_SCHEMA}.{TABLE_NAME}

            WHERE internal_account_id IS NOT NULL

            GROUP BY internal_account_id
        ),

        ranked AS (

            SELECT

                internal_account_id,

                revenue,

                SUM(revenue)
                    OVER (
                        ORDER BY revenue DESC
                        ROWS BETWEEN
                            UNBOUNDED PRECEDING
                            AND CURRENT ROW
                    ) AS cumulative_revenue,

                SUM(revenue)
                    OVER () AS total_revenue

            FROM account_revenue
        )

        SELECT

            internal_account_id,

            revenue,

            ROUND(
                100.0 *
                revenue /
                NULLIF(total_revenue, 0),
                4
            ) AS revenue_percentage,

            ROUND(
                100.0 *
                cumulative_revenue /
                NULLIF(total_revenue, 0),
                4
            ) AS cumulative_revenue_percentage

        FROM ranked

        ORDER BY revenue DESC

        LIMIT 10000
        """
    )

else:

    revenue_concentration = pd.DataFrame()

save_csv(
    revenue_concentration,
    "25_revenue_concentration.csv",
)


# ============================================================
# 28. BUSINESS ISSUE DETECTION
# ============================================================

print("[28] Building business issue register...")

issues = []


def add_issue(
    category,
    severity,
    issue,
    evidence,
    business_impact,
    recommended_action,
):
    issues.append(
        {
            "category": category,
            "severity": severity,
            "issue": issue,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
        }
    )


# Dataset completeness

if total_rows == EXPECTED_EXACT_ROWS:

    add_issue(
        "Data completeness",
        "INFO",
        "Dataset row count matches the verified updated dataset.",
        f"{total_rows:,} records audited.",
        "Supports confidence in the current database load.",
        "Retain this dataset as the current audit baseline.",
    )

else:

    add_issue(
        "Data completeness",
        "HIGH",
        "Dataset row count differs from the verified baseline.",
        f"Found {total_rows:,}; expected {EXPECTED_EXACT_ROWS:,}.",
        "Analysis may not represent the complete source dataset.",
        "Reconcile the source file and database load.",
    )


# Missing payments

null_payments = int(
    overview_row["null_payment"]
)

if null_payments > 0:

    add_issue(
        "Revenue data",
        "HIGH",
        "Payment values are missing.",
        f"{null_payments:,} records have NULL total_payment.",
        "Revenue reporting may be incomplete.",
        "Investigate missing payment records.",
    )


# Zero payments

zero_payments = int(
    overview_row["zero_payment"]
)

if zero_payments > 0:

    add_issue(
        "Revenue data",
        "REVIEW",
        "Zero-payment transactions exist.",
        f"{zero_payments:,} records have a zero payment.",
        "May represent complimentary, adjusted, test, or non-revenue transactions.",
        "Classify zero-payment transactions by business purpose.",
    )


# Negative payments

negative_payments = int(
    overview_row["negative_payment"]
)

if negative_payments > 0:

    add_issue(
        "Revenue data",
        "HIGH",
        "Negative payment values exist.",
        f"{negative_payments:,} records have negative payments.",
        "Could affect revenue reporting and reconciliation.",
        "Reconcile negative values against refunds, credits, or reversals.",
    )


# High-value transactions

high_value_count = int(
    financial_row["payments_over_100000"]
)

if high_value_count > 0:

    add_issue(
        "Transaction monitoring",
        "REVIEW",
        "Very high-value transactions require validation.",
        f"{high_value_count:,} transactions exceed $100,000.",
        "Unusual values can materially affect aggregate revenue.",
        "Validate high-value transactions against source-system records.",
    )


# Future dates

if "transaction_in_future" in date_row:

    future_dates = int(
        date_row["transaction_in_future"]
    )

else:

    future_dates = 0


if future_dates > 0:

    add_issue(
        "Date quality",
        "HIGH",
        "Future transaction dates were detected.",
        f"{future_dates:,} records occur after the audit timestamp.",
        "Can distort reporting periods and forecasting.",
        "Investigate timestamp generation and source-system clocks.",
    )


# Missing identifiers

for identifier in [
    "primary_ticket_id",
    "subscription_instance_id",
]:

    if identifier in missing_values["column_name"].values:

        missing_count = int(
            missing_values.loc[
                missing_values["column_name"]
                == identifier,
                "missing_count",
            ].iloc[0]
        )

        if missing_count > 0:

            add_issue(
                "Data completeness",
                "REVIEW",
                f"Missing {identifier} values exist.",
                f"{missing_count:,} records are missing the identifier.",
                "May affect customer, ticket, or subscription-level analysis.",
                "Interpret missingness by product type before labeling it as an error.",
            )


# Partial month

add_issue(
    "Reporting period",
    "INFO",
    "September 2026 is a partial month.",
    "The latest transaction date is September 24, 2026.",
    "Monthly comparisons can be misleading if partial periods are treated as complete.",
    "Flag September 2026 as partial in dashboards and reports.",
)


# Duplicate transactions

duplicate_transaction_count = len(
    duplicate_transactions
)

if duplicate_transaction_count > 0:

    add_issue(
        "Duplicate transactions",
        "REVIEW",
        "Repeated transaction IDs were detected.",
        f"{duplicate_transaction_count:,} duplicate transaction groups are present in the exported sample.",
        "Could represent legitimate multi-line transactions or duplicate records.",
        "Investigate transaction grain before deduplicating.",
    )


business_issues = pd.DataFrame(
    issues
)

save_csv(
    business_issues,
    "26_business_issue_register.csv",
)


# ============================================================
# 29. EXECUTIVE KPI SUMMARY
# ============================================================

print("[29] Building executive KPI summary...")

payment_stats = payment_statistics.iloc[0]

executive_summary = pd.DataFrame(
    [
        {
            "metric": "Total records",
            "value": total_rows,
        },
        {
            "metric": "Total revenue",
            "value": float(
                overview_row["total_revenue"]
            ),
        },
        {
            "metric": "Average transaction",
            "value": float(
                overview_row["average_payment"]
            ),
        },
        {
            "metric": "Median transaction",
            "value": float(
                payment_stats["median_payment"]
            ),
        },
        {
            "metric": "Maximum transaction",
            "value": float(
                overview_row["maximum_payment"]
            ),
        },
        {
            "metric": "Zero-payment records",
            "value": int(
                overview_row["zero_payment"]
            ),
        },
        {
            "metric": "Negative-payment records",
            "value": int(
                overview_row["negative_payment"]
            ),
        },
        {
            "metric": "Missing-payment records",
            "value": int(
                overview_row["null_payment"]
            ),
        },
        {
            "metric": "Business issues identified",
            "value": len(business_issues),
        },
    ]
)

save_csv(
    executive_summary,
    "27_executive_kpis.csv",
)


# ============================================================
# 30. CHARTS
# ============================================================

print("[30] Generating charts...")


def save_chart(
    filename,
):
    path = CHARTS_DIR / filename

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=180,
    )

    plt.close()


# Yearly revenue

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

    save_chart(
        "01_yearly_revenue.png"
    )


# Yearly records

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

    save_chart(
        "02_yearly_records.png"
    )


# Monthly revenue

if not monthly_trend.empty:

    plot_data = monthly_trend.copy()

    plot_data["month"] = pd.to_datetime(
        plot_data["month"]
    )

    plt.figure(figsize=(14, 6))

    plt.plot(
        plot_data["month"],
        plot_data["revenue"],
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

    save_chart(
        "03_monthly_revenue.png"
    )


# Product type revenue

if not product_type.empty:

    chart_data = product_type.head(15)

    plt.figure(figsize=(12, 7))

    plt.barh(
        chart_data[
            "product_type"
        ].astype(str),
        chart_data["revenue"],
    )

    plt.title(
        "Revenue by Product Type"
    )

    plt.xlabel("Revenue")

    save_chart(
        "04_product_type_revenue.png"
    )


# Channel revenue

if not application_channel.empty:

    chart_data = application_channel

    plt.figure(figsize=(12, 7))

    plt.barh(
        chart_data[
            "application_channel"
        ].astype(str),
        chart_data["revenue"],
    )

    plt.title(
        "Revenue by Application Channel"
    )

    plt.xlabel("Revenue")

    save_chart(
        "05_application_channel_revenue.png"
    )


# Payment percentiles

if not payment_statistics.empty:

    labels = [
        "P01",
        "P05",
        "P25",
        "Median",
        "P75",
        "P90",
        "P95",
        "P99",
    ]

    values = [
        payment_stats["p01"],
        payment_stats["p05"],
        payment_stats["p25"],
        payment_stats["median_payment"],
        payment_stats["p75"],
        payment_stats["p90"],
        payment_stats["p95"],
        payment_stats["p99"],
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

    save_chart(
        "06_payment_percentiles.png"
    )


# ============================================================
# 31. MARKDOWN REPORT
# ============================================================

print("[31] Generating comprehensive Markdown report...")

report_path = (
    RESULTS_DIR /
    "austin_fc_comprehensive_audit_report.md"
)

report = []

report.append(
    "# Austin FC Sales Data — Comprehensive Audit"
)

report.append("")

report.append(
    f"Generated: {datetime.now().isoformat(timespec='seconds')}"
)

report.append("")

report.append("## Executive Summary")

report.append("")

report.append(
    f"- Records audited: **{total_rows:,}**"
)

report.append(
    f"- Total revenue: **{money(overview_row['total_revenue'])}**"
)

report.append(
    f"- Average transaction: **{money(overview_row['average_payment'])}**"
)

report.append(
    f"- Median transaction: **{money(payment_stats['median_payment'])}**"
)

report.append(
    f"- Minimum payment: **{money(overview_row['minimum_payment'])}**"
)

report.append(
    f"- Maximum payment: **{money(overview_row['maximum_payment'])}**"
)

report.append(
    f"- Earliest transaction: **{overview_row['earliest_transaction']}**"
)

report.append(
    f"- Latest transaction: **{overview_row['latest_transaction']}**"
)

report.append("")

report.append(
    "The analysis was performed against the complete PostgreSQL "
    "source table. The source table was not sampled."
)

report.append("")

report.append("## Business Issues Requiring Attention")

report.append("")

if business_issues.empty:

    report.append(
        "No business issues were automatically flagged."
    )

else:

    report.append(
        "| Category | Severity | Issue | Evidence | Business Impact | Recommended Action |"
    )

    report.append(
        "|---|---|---|---|---|---|"
    )

    for _, row in business_issues.iterrows():

        report.append(
            f"| {safe_text(row['category'])} | "
            f"{safe_text(row['severity'])} | "
            f"{safe_text(row['issue'])} | "
            f"{safe_text(row['evidence'])} | "
            f"{safe_text(row['business_impact'])} | "
            f"{safe_text(row['recommended_action'])} |"
        )

report.append("")

report.append("## Financial Quality")

report.append("")

report.append(
    f"- NULL payments: **{number(overview_row['null_payment'])}**"
)

report.append(
    f"- Zero payments: **{number(overview_row['zero_payment'])}**"
)

report.append(
    f"- Negative payments: **{number(overview_row['negative_payment'])}**"
)

report.append(
    f"- Payments above $10,000: "
    f"**{number(financial_row['payments_over_10000'])}**"
)

report.append(
    f"- Payments above $50,000: "
    f"**{number(financial_row['payments_over_50000'])}**"
)

report.append(
    f"- Payments above $100,000: "
    f"**{number(financial_row['payments_over_100000'])}**"
)

report.append("")

report.append("## Payment Distribution")

report.append("")

report.append(
    f"- P25: **{money(payment_stats['p25'])}**"
)

report.append(
    f"- Median: **{money(payment_stats['median_payment'])}**"
)

report.append(
    f"- P75: **{money(payment_stats['p75'])}**"
)

report.append(
    f"- P90: **{money(payment_stats['p90'])}**"
)

report.append(
    f"- P95: **{money(payment_stats['p95'])}**"
)

report.append(
    f"- P99: **{money(payment_stats['p99'])}**"
)

report.append("")

report.append("## Product Performance")

report.append("")

if not product_type.empty:

    report.append(
        "| Product Type | Records | Revenue | Average Payment | Revenue Share |"
    )

    report.append(
        "|---|---:|---:|---:|---:|"
    )

    for _, row in product_type.iterrows():

        report.append(
            f"| {safe_text(row['product_type'])} | "
            f"{number(row['records'])} | "
            f"{money(row['revenue'])} | "
            f"{money(row['average_payment'])} | "
            f"{pct(row['revenue_percentage'])} |"
        )

report.append("")

report.append("## Application Channel Performance")

report.append("")

if not application_channel.empty:

    report.append(
        "| Channel | Records | Revenue | Average Payment | Revenue Share |"
    )

    report.append(
        "|---|---:|---:|---:|---:|"
    )

    for _, row in application_channel.iterrows():

        report.append(
            f"| {safe_text(row['application_channel'])} | "
            f"{number(row['records'])} | "
            f"{money(row['revenue'])} | "
            f"{money(row['average_payment'])} | "
            f"{pct(row['revenue_percentage'])} |"
        )

report.append("")

report.append("## Date Coverage")

report.append("")

report.append(
    f"- Earliest transaction: "
    f"**{overview_row['earliest_transaction']}**"
)

report.append(
    f"- Latest transaction: "
    f"**{overview_row['latest_transaction']}**"
)

report.append(
    "- September 2026 is a partial reporting month."
)

report.append("")

report.append("## Methodology")

report.append("")

report.append(
    "Large-scale calculations were performed in PostgreSQL. "
    "Only small aggregate result sets were transferred to pandas."
)

report.append("")

report.append(
    "This prevents the complete 5.3-million-row dataset from "
    "being loaded into memory."
)

report.append("")

report.append(
    "Unusual values are treated as investigation candidates. "
    "They are not automatically classified as fraud or errors."
)

report.append("")

report.append("## Generated Outputs")

report.append("")

report.append(
    "The `results/tables/` directory contains aggregate CSV "
    "outputs. The `results/charts/` directory contains "
    "visualizations."
)

report.append("")

report_path.write_text(
    "\n".join(report),
    encoding="utf-8",
)


# ============================================================
# 32. HTML DASHBOARD
# ============================================================

print("[32] Generating HTML dashboard...")

html_path = (
    RESULTS_DIR /
    "austin_fc_comprehensive_audit.html"
)

issue_rows = ""

for _, row in business_issues.iterrows():

    issue_rows += f"""
    <tr>
        <td>{safe_text(row['category'])}</td>
        <td>{safe_text(row['severity'])}</td>
        <td>{safe_text(row['issue'])}</td>
        <td>{safe_text(row['evidence'])}</td>
        <td>{safe_text(row['business_impact'])}</td>
        <td>{safe_text(row['recommended_action'])}</td>
    </tr>
    """


html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
Austin FC Comprehensive Sales Audit
</title>

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

.container {{
    max-width: 1400px;

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

    padding: 22px;

    border-radius: 10px;

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

table {{
    width: 100%;

    border-collapse: collapse;

    background: white;
}}

th,
td {{
    padding: 10px;

    border-bottom:
        1px solid #e5e7eb;

    text-align: left;

    vertical-align: top;
}}

th {{
    background: #f3f4f6;
}}

img {{
    max-width: 100%;

    height: auto;

    background: white;

    padding: 10px;

    border-radius: 8px;
}}

</style>

</head>

<body>

<header>

<h1>
Austin FC Comprehensive Sales Data Audit
</h1>

<p>
Full PostgreSQL dataset analysis
</p>

<p>
Generated:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
</p>

</header>

<div class="container">

<section>

<h2>Executive KPIs</h2>

<div class="grid">

<div class="card">
<div class="metric">
{total_rows:,}
</div>
<div class="label">
Records Audited
</div>
</div>

<div class="card">
<div class="metric">
{money(overview_row['total_revenue'])}
</div>
<div class="label">
Total Revenue
</div>
</div>

<div class="card">
<div class="metric">
{money(overview_row['average_payment'])}
</div>
<div class="label">
Average Transaction
</div>
</div>

<div class="card">
<div class="metric">
{money(payment_stats['median_payment'])}
</div>
<div class="label">
Median Transaction
</div>
</div>

<div class="card">
<div class="metric">
{money(overview_row['maximum_payment'])}
</div>
<div class="label">
Maximum Transaction
</div>
</div>

<div class="card">
<div class="metric">
{len(business_issues)}
</div>
<div class="label">
Business Issues
</div>
</div>

</div>

</section>


<section>

<h2>Business Issue Register</h2>

<table>

<thead>

<tr>
<th>Category</th>
<th>Severity</th>
<th>Issue</th>
<th>Evidence</th>
<th>Business Impact</th>
<th>Recommended Action</th>
</tr>

</thead>

<tbody>

{issue_rows}

</tbody>

</table>

</section>


<section>

<h2>Yearly Revenue</h2>

<img
src="charts/01_yearly_revenue.png"
alt="Yearly revenue">

</section>


<section>

<h2>Monthly Revenue</h2>

<img
src="charts/03_monthly_revenue.png"
alt="Monthly revenue">

</section>


<section>

<h2>Revenue by Product Type</h2>

<img
src="charts/04_product_type_revenue.png"
alt="Product type revenue">

</section>


<section>

<h2>Revenue by Application Channel</h2>

<img
src="charts/05_application_channel_revenue.png"
alt="Application channel revenue">

</section>


<section>

<h2>Payment Distribution</h2>

<img
src="charts/06_payment_percentiles.png"
alt="Payment distribution">

</section>


<section>

<h2>Methodology</h2>

<div class="card">

<p>
The audit analyzes the complete PostgreSQL source table.
</p>

<p>
The 5.3-million-row source table is not loaded into pandas
at once.
</p>

<p>
PostgreSQL performs full-table aggregation and statistical
processing. Python and pandas process the resulting small
datasets.
</p>

<p>
Anomalies are investigation candidates and are not
automatically classified as fraud or errors.
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
# FINAL VALIDATION
# ============================================================

print()
print("=" * 90)
print("AUDIT COMPLETE")
print("=" * 90)
print()

print(
    f"Rows audited: {total_rows:,}"
)

print(
    f"Revenue: {money(overview_row['total_revenue'])}"
)

print(
    f"Business issues: {len(business_issues)}"
)

print()

print(
    "Markdown report:",
    report_path,
)

print(
    "HTML dashboard:",
    html_path,
)

print(
    "Tables:",
    TABLES_DIR,
)

print(
    "Charts:",
    CHARTS_DIR,
)

elapsed = (
    datetime.now() - started_at
).total_seconds()

print()

print(
    f"Elapsed time: {elapsed:.2f} seconds"
)

print()

print(
    "The complete source table was analyzed "
    "through PostgreSQL aggregation."
)

print()


# ============================================================
# CLEANUP
# ============================================================

engine.dispose()
