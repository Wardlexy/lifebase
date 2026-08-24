"""LifeBase - wallet transactions ingestion (source #1).

Reads normalized CSV exports from data/raw/wallet/ into raw.wallet_transactions.
File-level incrementality: each file's fingerprint (name+size+mtime) is stored
in dlt state, so re-runs skip already-loaded exports.

Format contract: see docs/wallet-csv-format.md
"""

import os
from pathlib import Path

import dlt

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "wallet"

REQUIRED_COLUMNS = {"date", "description", "amount", "type", "account", "currency"}


def _read_csv(csv_path: Path):
    import csv as csv_module

    import pandas as pd

    # Indonesian bank/e-wallet & Excel exports commonly use ';' delimiters
    # and UTF-8 BOM - detect instead of assuming comma.
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
    try:
        delimiter = csv_module.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv_module.Error:
        delimiter = ","

    df = pd.read_csv(csv_path, sep=delimiter, encoding="utf-8-sig")
    df.columns = [c.strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path.name}: missing required columns {sorted(missing)}")

    # Contract enforcement before anything touches the warehouse
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["type"] = df["type"].str.strip().str.lower()
    unknown_types = set(df["type"].unique()) - {"in", "out"}
    if unknown_types:
        raise ValueError(f"{csv_path.name}: 'type' must be in/out, found {unknown_types}")

    df["source_file"] = csv_path.name
    yield from df.to_dict(orient="records")


@dlt.resource(name="wallet_transactions", write_disposition="append")
def wallet_transactions():
    state = dlt.current.state()
    processed_files = state.setdefault("processed_files", {})

    csv_paths = sorted(DATA_DIR.glob("*.csv"))
    if not csv_paths:
        print(f"[wallet] no CSV files found in {DATA_DIR} - drop exports there first")
        return

    for csv_path in csv_paths:
        fingerprint = (
            f"{csv_path.name}:{csv_path.stat().st_size}:{int(csv_path.stat().st_mtime)}"
        )
        if processed_files.get(csv_path.name) == fingerprint:
            print(f"[wallet] skipping {csv_path.name} (already loaded)")
            continue

        rows = list(_read_csv(csv_path))
        print(f"[wallet] loading {len(rows)} rows from {csv_path.name}")
        yield from rows
        processed_files[csv_path.name] = fingerprint


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    pipeline = dlt.pipeline(
        pipeline_name="wallet",
        destination=dlt.destinations.postgres(
            credentials=os.environ["LIFEBASE_DB_URI"],
        ),
        dataset_name="raw",
    )
    info = pipeline.run(wallet_transactions())
    print(info)


if __name__ == "__main__":
    main()
