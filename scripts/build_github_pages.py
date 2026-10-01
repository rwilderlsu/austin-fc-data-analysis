#!/usr/bin/env python3

from pathlib import Path
import html
import json
import math
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path.home() / "data-analysis"
RESULTS_DIR = PROJECT_DIR / "results"
DOCS_DIR = PROJECT_DIR / "docs"
ASSETS_DIR = DOCS_DIR / "assets"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def read_csv(filename):
    path = RESULTS_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def money(value):
    try:
        return "${:,.2f}".format(float(value))
    except Exception:
        return "N/A"


def integer(value):
    try:
        return "{:,.0f}".format(float(value))
    except Exception:
        return "N/A"


def percent(value):
    try:
        return "{:.2f}%".format(float(value))
    except Exception:
        return "N/A"


def safe(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def find_column(df, candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def table_html(df, max_rows=15):
    if df.empty:
        return '<p class="muted">No data available.</p>'

    display = df.head(max_rows).copy()

    rows = []

    header = "".join(
        f"<th>{html.escape(str(col))}</th>"
        for col in display.columns
    )

    rows.append(f"<tr>{header}</tr>")

    for _, row in display.iterrows():
        cells = "".join(
            f"<td>{safe(value)}</td>"
            for value in row
        )
        rows.append(f"<tr>{cells}</tr>")

    return f"""
    <div class="table-wrap">
        <table>
            <thead>{rows[0]}</thead>
            <tbody>
                {''.join(rows[1:])}
            </tbody>
        </table>
    </div>
    """


def bar_chart_svg(df, label_col, value_col, title, max_items=10):
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return '<p class="muted">Chart data unavailable.</p>'

    data = df[[label_col, value_col]].copy()
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna()
    data = data.head(max_items)

    if data.empty:
        return '<p class="muted">Chart data unavailable.</p>'

    max_value = data[value_col].max()
    if max_value <= 0:
        max_value = 1

    width = 760
    row_height = 42
    left = 190
    chart_height = 70 + len(data) * row_height

    svg = [
        f'<svg viewBox="0 0 {width} {chart_height}" '
        f'role="img" aria-label="{html.escape(title)}">'
    ]

    svg.append(
        f'<text x="20" y="30" class="svg-title">'
        f'{html.escape(title)}</text>'
    )

    y = 58

    for _, row in data.iterrows():
        label = str(row[label_col])
        value = float(row[value_col])

        bar_width = (value / max_value) * 500

        svg.append(
            f'<text x="15" y="{y + 17}" class="svg-label">'
            f'{html.escape(label[:26])}</text>'
        )

        svg.append(
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" '
            f'height="25" rx="5" class="bar"/>'
        )

        svg.append(
            f'<text x="{left + bar_width + 10:.1f}" '
            f'y="{y + 18}" class="svg-value">'
            f'{html.escape(f"{value:,.0f}")}</text>'
        )

        y += row_height

    svg.append("</svg>")

    return "".join(svg)


# ============================================================
# LOAD AUDIT RESULTS
# ============================================================

overview = read_csv("01_dataset_overview.csv")
missing = read_csv("03_missing_values_by_column.csv")
product_type = read_csv("04_product_type.csv")
sale_type = read_csv("05_sale_type.csv")
application_channel = read_csv("06_application_channel.csv")
hospitality = read_csv("07_hospitality.csv")
identifier = read_csv("08_identifier_uniqueness.csv")
duplicate_summary = read_csv("12_duplicate_summary.csv")
financial = read_csv("13_financial_anomalies.csv")
yearly = read_csv("15_yearly_trend.csv")
monthly = read_csv("16_monthly_trend.csv")
date_consistency = read_csv("17_date_consistency.csv")
products = read_csv("18_top_product_descriptions.csv")
transfer = read_csv("19_transfer_status.csv")
resale = read_csv("20_resale_status.csv")
column_types = read_csv("21_column_types.csv")
grain = read_csv("22_potential_data_grain.csv")
flags = read_csv("23_audit_summary_flags.csv")


# ============================================================
# CORE PROJECT FACTS
# ============================================================

ROW_COUNT = 5_326_581
START_DATE = "2019-08-15"
END_DATE = "2026-09-18"
TOTAL_PAYMENTS = "$482,706,014.11"
AVERAGE_PAYMENT = "$90.62"


# ============================================================
# DERIVE DISPLAY DATA
# ============================================================

year_col = find_column(
    yearly,
    ["year", "transaction_year", "calendar_year"]
)

year_rows_col = find_column(
    yearly,
    ["row_count", "rows", "count", "transaction_count"]
)

year_payment_col = find_column(
    yearly,
    ["total_payment", "total_payments", "payment_total", "sum_total_payment"]
)

product_label = find_column(
    product_type,
    ["product_type", "product", "type"]
)

product_value = find_column(
    product_type,
    ["row_count", "count", "records", "transaction_count"]
)

missing_label = find_column(
    missing,
    ["column", "column_name", "field", "name"]
)

missing_value = find_column(
    missing,
    ["missing_count", "null_count", "missing", "count"]
)

financial_label = find_column(
    financial,
    ["anomaly_type", "issue", "category", "flag"]
)

financial_value = find_column(
    financial,
    ["count", "row_count", "records", "value"]
)


# ============================================================
# YEARLY DATA FOR INLINE CHART
# ============================================================

year_chart = ""

if (
    not yearly.empty
    and year_col
    and year_rows_col
):
    chart_df = yearly.copy()

    chart_df[year_rows_col] = pd.to_numeric(
        chart_df[year_rows_col],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=[year_rows_col]
    )

    chart_df = chart_df.sort_values(
        year_col
    )

    year_chart = bar_chart_svg(
        chart_df,
        year_col,
        year_rows_col,
        "Transactions by Year",
        max_items=10
    )
else:
    year_chart = '<p class="muted">Yearly trend data unavailable.</p>'


# ============================================================
# PRODUCT CHART
# ============================================================

product_chart = ""

if product_label and product_value:
    product_chart = bar_chart_svg(
        product_type,
        product_label,
        product_value,
        "Transactions by Product Type",
        max_items=10
    )
else:
    product_chart = '<p class="muted">Product type chart unavailable.</p>'


# ============================================================
# MISSING DATA CHART
# ============================================================

missing_chart = ""

if missing_label and missing_value:
    missing_chart = bar_chart_svg(
        missing,
        missing_label,
        missing_value,
        "Missing Values by Column",
        max_items=12
    )
else:
    missing_chart = '<p class="muted">Missing-value chart unavailable.</p>'


# ============================================================
# GENERATE HTML
# ============================================================

html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Austin FC Data Audit</title>

<meta
    name="description"
    content="Austin FC sales history data quality and audit project"
/>

<style>

:root {{
    --bg: #f5f7fb;
    --card: #ffffff;
    --text: #172033;
    --muted: #667085;
    --border: #e4e7ec;
    --accent: #087f5b;
    --accent-dark: #056044;
    --accent-light: #e6f6f0;
    --dark: #101828;
}}

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;
    line-height: 1.6;
}}

a {{
    color: var(--accent);
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

.container {{
    width: min(1180px, 92%);
    margin: auto;
}}

header {{
    background: linear-gradient(
        135deg,
        #101828 0%,
        #1d2939 60%,
        #087f5b 100%
    );
    color: white;
    padding: 70px 0 55px;
}}

.badge {{
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,.14);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .04em;
    text-transform: uppercase;
}}

h1 {{
    font-size: clamp(38px, 6vw, 68px);
    line-height: 1.05;
    margin: 18px 0;
}}

.hero-text {{
    max-width: 800px;
    font-size: 19px;
    color: #d0d5dd;
}}

nav {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: rgba(255,255,255,.96);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(10px);
}}

.nav-inner {{
    display: flex;
    gap: 22px;
    overflow-x: auto;
    padding: 14px 0;
    white-space: nowrap;
}}

.nav-inner a {{
    color: var(--text);
    font-size: 14px;
    font-weight: 700;
}}

section {{
    padding: 58px 0;
}}

.section-title {{
    font-size: 30px;
    margin: 0 0 10px;
}}

.section-intro {{
    color: var(--muted);
    max-width: 800px;
    margin-bottom: 28px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(220px, 1fr)
    );
    gap: 18px;
}}

.card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 5px 20px rgba(16,24,40,.04);
}}

.metric {{
    font-size: 31px;
    font-weight: 800;
    color: var(--dark);
}}

.metric-label {{
    color: var(--muted);
    font-size: 14px;
    margin-top: 4px;
}}

.highlight {{
    background: var(--accent-light);
    border: 1px solid #b7ead8;
}}

.chart-card {{
    overflow: hidden;
}}

.chart {{
    overflow-x: auto;
}}

svg {{
    width: 100%;
    min-width: 600px;
    height: auto;
}}

.svg-title {{
    font-size: 17px;
    font-weight: 800;
    fill: var(--dark);
}}

.svg-label {{
    font-size: 12px;
    fill: var(--text);
}}

.svg-value {{
    font-size: 12px;
    fill: var(--muted);
}}

.bar {{
    fill: var(--accent);
}}

.table-wrap {{
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 12px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    font-size: 14px;
}}

th {{
    text-align: left;
    background: #f9fafb;
    color: var(--text);
    font-weight: 800;
}}

th, td {{
    padding: 11px 13px;
    border-bottom: 1px solid var(--border);
}}

tr:last-child td {{
    border-bottom: 0;
}}

.muted {{
    color: var(--muted);
}}

.method {{
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(230px, 1fr)
    );
    gap: 18px;
}}

.method-card {{
    border-left: 4px solid var(--accent);
    padding-left: 18px;
}}

footer {{
    background: var(--dark);
    color: #d0d5dd;
    padding: 45px 0;
    margin-top: 30px;
}}

footer a {{
    color: #8ce0c4;
}}

.warning {{
    border-left: 4px solid #f79009;
}}

.success {{
    border-left: 4px solid var(--accent);
}}

.small {{
    font-size: 13px;
}}

</style>
</head>

<body>

<header id="top">
<div class="container">

<span class="badge">Data Quality & Analytics</span>

<h1>Austin FC<br>Data Audit</h1>

<p class="hero-text">
A reproducible audit of Austin FC sales-history data using
Python, pandas, SQL, PostgreSQL, and statistical data-quality
checks.
</p>

</div>
</header>

<nav>
<div class="container nav-inner">
<a href="#overview">Overview</a>
<a href="#coverage">Coverage</a>
<a href="#quality">Data Quality</a>
<a href="#trends">Trends</a>
<a href="#products">Products</a>
<a href="#anomalies">Anomalies</a>
<a href="#methodology">Methodology</a>
<a href="#downloads">Results</a>
</div>
</nav>


<section id="overview">
<div class="container">

<h2 class="section-title">Dataset Overview</h2>

<p class="section-intro">
This audit analyzes the complete source dataset loaded into
PostgreSQL. The raw transaction-level dataset remains private
and is intentionally not published to GitHub.
</p>

<div class="grid">

<div class="card highlight">
<div class="metric">{integer(ROW_COUNT)}</div>
<div class="metric-label">Transaction records audited</div>
</div>

<div class="card">
<div class="metric">{TOTAL_PAYMENTS}</div>
<div class="metric-label">Total payments</div>
</div>

<div class="card">
<div class="metric">{AVERAGE_PAYMENT}</div>
<div class="metric-label">Average payment</div>
</div>

<div class="card">
<div class="metric">2019–2026</div>
<div class="metric-label">Transaction coverage</div>
</div>

</div>

</div>
</section>


<section id="coverage">
<div class="container">

<h2 class="section-title">Data Coverage</h2>

<p class="section-intro">
The source data covers transactions from August 2019 through
September 2026.
</p>

<div class="grid">

<div class="card">
<strong>Earliest transaction</strong>
<p>{START_DATE}</p>
</div>

<div class="card">
<strong>Latest transaction</strong>
<p>{END_DATE}</p>
</div>

<div class="card">
<strong>Rows independently verified</strong>
<p>{integer(ROW_COUNT)}</p>
</div>

<div class="card">
<strong>Database engine</strong>
<p>PostgreSQL 16</p>
</div>

</div>

<div class="card chart-card" style="margin-top:22px;">
<div class="chart">
{year_chart}
</div>
</div>

</div>
</section>


<section id="quality">
<div class="container">

<h2 class="section-title">Data Quality</h2>

<p class="section-intro">
The audit checks missing values, identifier uniqueness,
duplicates, date consistency, data types, and potential
data-grain issues.
</p>

<div class="card chart-card">
<div class="chart">
{missing_chart}
</div>
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Missing Values by Column</h3>
{table_html(missing, 20)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Identifier Uniqueness</h3>
{table_html(identifier, 20)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Duplicate Summary</h3>
{table_html(duplicate_summary, 20)}
</div>

</div>
</section>


<section id="trends">
<div class="container">

<h2 class="section-title">Sales Trends</h2>

<p class="section-intro">
Yearly and monthly audit outputs are included in the repository.
The yearly view provides a high-level picture of transaction
volume across the complete analysis period.
</p>

<div class="card">
<h3>Yearly Trend</h3>
{table_html(yearly, 20)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Monthly Trend</h3>
{table_html(monthly, 25)}
</div>

</div>
</section>


<section id="products">
<div class="container">

<h2 class="section-title">Products and Sales Channels</h2>

<p class="section-intro">
The audit examines product categories, sale types, application
channels, hospitality status, and other descriptive fields.
</p>

<div class="card chart-card">
<div class="chart">
{product_chart}
</div>
</div>

<div style="height:22px;"></div>

<div class="grid">

<div class="card">
<h3>Product Type</h3>
{table_html(product_type, 12)}
</div>

<div class="card">
<h3>Sale Type</h3>
{table_html(sale_type, 12)}
</div>

<div class="card">
<h3>Application Channel</h3>
{table_html(application_channel, 12)}
</div>

<div class="card">
<h3>Hospitality</h3>
{table_html(hospitality, 12)}
</div>

</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Top Product Descriptions</h3>
{table_html(products, 20)}
</div>

</div>
</section>


<section id="anomalies">
<div class="container">

<h2 class="section-title">Anomaly and Consistency Checks</h2>

<p class="section-intro">
Financial and structural checks identify records that may
require additional investigation. These flags are audit
findings and do not by themselves establish that a transaction
is incorrect.
</p>

<div class="card warning">
<h3>Financial Anomaly Summary</h3>
{table_html(financial, 25)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Date Consistency</h3>
{table_html(date_consistency, 20)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Transfer Status</h3>
{table_html(transfer, 15)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Resale Status</h3>
{table_html(resale, 15)}
</div>

<div style="height:22px;"></div>

<div class="card">
<h3>Potential Data Grain</h3>
{table_html(grain, 20)}
</div>

</div>
</section>


<section id="methodology">
<div class="container">

<h2 class="section-title">Methodology</h2>

<p class="section-intro">
The audit follows a reproducible workflow from the source
dataset through PostgreSQL queries and Python analysis.
</p>

<div class="method">

<div class="card method-card">
<h3>1. Source Validation</h3>
<p>
The source dataset was loaded into PostgreSQL and independently
checked for total row count and date coverage.
</p>
</div>

<div class="card method-card">
<h3>2. Structural Audit</h3>
<p>
Column types, missing values, identifier uniqueness,
duplicates, and potential data grain were evaluated.
</p>
</div>

<div class="card method-card">
<h3>3. Financial Audit</h3>
<p>
Payment values were reviewed for zero values, extreme values,
and other potential financial anomalies.
</p>
</div>

<div class="card method-card">
<h3>4. Trend Analysis</h3>
<p>
Transactions were summarized by year and month to identify
changes in activity over time.
</p>
</div>

<div class="card method-card">
<h3>5. Categorical Analysis</h3>
<p>
Product types, sale types, application channels, hospitality,
transfer, and resale fields were summarized.
</p>
</div>

<div class="card method-card">
<h3>6. Reproducibility</h3>
<p>
The analysis script and Jupyter notebook are included in the
GitHub repository so the workflow can be inspected and rerun.
</p>
</div>

</div>

</div>
</section>


<section id="downloads">
<div class="container">

<h2 class="section-title">Audit Results</h2>

<p class="section-intro">
Safe aggregate audit results are available as CSV files in
the GitHub repository. Raw transaction-level source data,
credentials, and private environment files are excluded.
</p>

<div class="grid">

<div class="card success">
<h3>Repository</h3>
<p>
<a
href="https://github.com/KAVIKU/austin-fc-data-audit"
target="_blank"
rel="noopener"
>
View source on GitHub
</a>
</p>
</div>

<div class="card">
<h3>Notebook</h3>
<p>
<a
href="https://github.com/KAVIKU/austin-fc-data-audit/blob/main/notebooks/01_austin_fc_data_audit.ipynb"
target="_blank"
rel="noopener"
>
View audit notebook
</a>
</p>
</div>

<div class="card">
<h3>Audit Script</h3>
<p>
<a
href="https://github.com/KAVIKU/austin-fc-data-audit/blob/main/scripts/austin_fc_data_audit.py"
target="_blank"
rel="noopener"
>
View Python audit script
</a>
</p>
</div>

<div class="card">
<h3>Documentation</h3>
<p>
<a
href="https://github.com/KAVIKU/austin-fc-data-audit/blob/main/results/austin_fc_data_audit_report.md"
target="_blank"
rel="noopener"
>
Read audit report
</a>
</p>
</div>

</div>

</div>
</section>


<footer>
<div class="container">

<strong>Austin FC Data Audit</strong>

<p class="small">
Reproducible data-quality and analytics project.
The published website contains aggregate audit results only.
The full transaction-level source dataset remains outside
the public repository.
</p>

<p class="small">
<a href="#top">Back to top</a>
</p>

</div>
</footer>

</body>
</html>
"""


# ============================================================
# WRITE SITE
# ============================================================

index_file = DOCS_DIR / "index.html"

index_file.write_text(
    html_page,
    encoding="utf-8"
)

# Tell GitHub Pages to treat this as a plain static site.
(DOCS_DIR / ".nojekyll").write_text(
    "",
    encoding="utf-8"
)

print()
print("==============================================")
print(" Austin FC GitHub Pages site generated")
print("==============================================")
print()
print(f"Website file: {index_file}")
print(f"Website size: {index_file.stat().st_size:,} bytes")
print()
print("Protected source data is NOT copied into docs/.")
print("The website contains aggregate audit information only.")
print()
