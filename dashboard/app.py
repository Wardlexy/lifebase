"""LifeBase - personal life exploration dashboard (local only)."""

import os

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="LifeBase", page_icon="🔭", layout="wide")

load_dotenv()


@st.cache_data(ttl=60)
def load_fact_table() -> pd.DataFrame:
    uri = os.environ["LIFEBASE_DB_URI"]
    with psycopg.connect(uri) as conn:
        return pd.read_sql(
            "select * from marts.fact_financial_transactions order by occurred_at desc",
            conn,
        )


def main() -> None:
    st.title("🔭 LifeBase")
    st.caption("Local-only personal data warehouse - nothing leaves this machine.")

    try:
        df = load_fact_table()
    except Exception as exc:  # noqa: BLE001 - show friendly startup error
        st.error(f"Could not reach the warehouse: {exc}")
        st.info("Run `docker compose up -d`, then `dbt build` first.")
        st.stop()

    if df.empty:
        st.warning("No financial data yet. Run `python ingest/wallet_pipeline.py` first.")
        st.stop()

    outflows = df[df["direction"] == "out"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions", len(df))
    col2.metric("Total spent", f"{outflows['gross_amount'].sum():,.0f}")
    col3.metric("Net balance", f"{df['signed_amount'].sum():,.0f}")

    monthly = (
        df.groupby(["year", "month"], as_index=False)["signed_amount"].sum()
        .sort_values(["year", "month"])
    )
    monthly["period"] = (
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    )
    st.subheader("Monthly net flow")
    st.bar_chart(monthly, x="period", y="signed_amount")

    st.subheader("Recent transactions")
    st.dataframe(df.head(100), use_container_width=True)


if __name__ == "__main__":
    main()
