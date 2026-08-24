# LifeBase - Wallet Transactions Pipeline

Normalizes manual digital wallet / m-banking exports into `raw.wallet_transactions`.

## Why CSV first?

Open Banking APIs in Indonesia are still fragmented, so LifeBase starts from
the lowest common denominator every bank supports: a CSV export you trigger
yourself. The pipeline is source-agnostic — each export just needs to be
mapped into the standard format below.

## Standard format

Save exports into `data/raw/wallet/*.csv` with exactly these columns:

| column      | type   | notes                                        |
|-------------|--------|----------------------------------------------|
| date        | text   | ISO format preferred (`YYYY-MM-DD HH:MM:SS`) |
| description | text   | raw merchant/description string              |
| amount      | number | always positive; direction goes in `type`    |
| type        | text   | `in` or `out`                                |
| account     | text   | e.g. `gopay`, `ovo`, `bca`                   |
| currency    | text   | e.g. `IDR`                                   |

Extra columns are ignored. Column names are case-insensitive.

## Mapping examples (add yours here)

- **GoPay (app export)**: map `Tanggal` -> `date`, `Keterangan` -> `description`,
  `Jumlah` -> `amount`, `Tipe` -> `type`
- **BCA (e-banking statement)**: map `Tanggal Transaksi` -> `date`,
  `Keterangan` -> `description`; split Mutasi `KR`/`DB` into `type`

## Run

```bash
python ingest/wallet_pipeline.py
```

Incremental by file: rows already loaded from a given `source_file` are not
re-ingested on re-runs.
