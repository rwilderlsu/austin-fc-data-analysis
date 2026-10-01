import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# Load database settings from .env
load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# Make sure all required settings exist
required = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
}

missing = [name for name, value in required.items() if not value]

if missing:
    raise RuntimeError(
        "Missing database settings: "
        + ", ".join(missing)
    )


# Create PostgreSQL connection
engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# Test connection
with engine.connect() as connection:
    result = connection.execute(
        text("SELECT current_database(), current_user;")
    )

    database, user = result.fetchone()

    print("PostgreSQL connection successful.")
    print(f"Database: {database}")
    print(f"User: {user}")


# Query PostgreSQL
query = """
SELECT
    EXTRACT(YEAR FROM transaction_date)::integer AS year,
    COUNT(*) AS transactions,
    SUM(total_payment) AS total_payment
FROM austin_fc_sales_history
GROUP BY year
ORDER BY year;
"""


df = pd.read_sql(query, engine)


print()
print("===== YEARLY SALES SUMMARY =====")
print(df.to_string(index=False))


# Close connection
engine.dispose()
