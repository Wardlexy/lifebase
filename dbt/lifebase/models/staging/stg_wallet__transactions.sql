with source as (
    select * from {{ source('raw', 'wallet_transactions') }}
),

typed as (
    select
        cast("date" as timestamp)          as occurred_at,
        coalesce(nullif(trim(description), ''), '(no description)')
                                            as description_raw,
        cast(amount as numeric(18, 2))     as amount_abs,
        lower(trim(type))                   as direction,
        nullif(lower(trim(account)), '')    as account,
        lower(trim(currency))               as currency,
        source_file,
        _dlt_load_id                        as load_id
    from source
)

select
    occurred_at,
    description_raw,
    amount_abs,
    direction,
    coalesce(account, 'unknown')            as account,
    coalesce(currency, 'idr')               as currency,
    source_file,
    load_id
from typed
