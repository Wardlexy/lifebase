{{ config(materialized='table') }}

-- Kimball-style fact: one row per financial event, sign-normalized so that
-- net flow queries are a simple SUM(signed_amount) grouped by any dimension.

select
    occurred_at,
    extract(year from occurred_at)::int   as year,
    extract(month from occurred_at)::int  as month,
    account,
    currency,
    direction,
    case
        when direction = 'out' then -amount_abs
        else amount_abs
    end                                    as signed_amount,
    amount_abs                             as gross_amount,
    description_raw,
    source_file
from {{ ref('stg_wallet__transactions') }}
