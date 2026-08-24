"""LifeBase MCP server.

Exposes curated, read-only warehouse tools to AI agents (Claude etc.).
The agent NEVER gets raw SQL access - governance by construction:
it can only ask questions the exposed tools can answer.
"""

import os

import psycopg
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("lifebase")


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a read-only query and return rows as dicts."""
    with psycopg.connect(os.environ["LIFEBASE_DB_URI"], readonly=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description or []]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


@mcp.tool()
def monthly_net_flow() -> list[dict]:
    """Total net money flow per month per currency, across all accounts. Negative = spending month."""
    return _query(
        """
        select year, month, currency, sum(signed_amount) as net_flow
        from marts.fact_financial_transactions
        group by year, month, currency
        order by year desc, month desc, currency
        """
    )


@mcp.tool()
def top_spending_categories(limit: int = 10) -> list[dict]:
    """Top merchant descriptions by total outflow. Raw strings - categorization comes later."""
    return _query(
        """
        select description_raw as merchant,
               sum(gross_amount) as total_out,
               count(*) as transactions
        from marts.fact_financial_transactions
        where direction = 'out'
        group by description_raw
        order by total_out desc
        limit %s
        """,
        (max(1, min(limit, 50)),),
    )


@mcp.tool()
def account_balances() -> list[dict]:
    """Current cumulative balance per account (sum of all signed flows)."""
    return _query(
        """
        select account, currency, sum(signed_amount) as balance
        from marts.fact_financial_transactions
        group by account, currency
        order by balance desc
        """
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
