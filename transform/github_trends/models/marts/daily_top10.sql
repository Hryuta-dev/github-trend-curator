with base as (
    select * from {{ ref('stg_repositories') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by fetched_date
            order by stargazers_count desc
        ) as rank
    from base
)

select * from ranked
where rank <= 10
