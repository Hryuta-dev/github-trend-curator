with base as (
    select * from {{ ref('stg_repositories') }}
),

aggregated as (
    select
        language,
        count(*)                    as repo_count,
        sum(stargazers_count)       as total_stars,
        avg(stargazers_count)       as avg_stars,
        max(stargazers_count)       as max_stars,
        fetched_date
    from base
    group by language, fetched_date
)

select * from aggregated
order by total_stars desc
