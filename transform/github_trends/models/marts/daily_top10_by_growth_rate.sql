with ranked_pairs as (
    select
        today.id,
        today.name,
        today.stargazers_count as today_stars,
        today.fetched_date as today_date,
        yesterday.stargazers_count as yesterday_stars,
        yesterday.fetched_date as yesterday_date,
        row_number() over (
            partition by today.id, today.fetched_date
            order by yesterday.fetched_date desc
        ) as recency_rank
    from {{ ref('stg_repositories') }} as today
    left join {{ ref('stg_repositories') }} as yesterday
        on today.id = yesterday.id
        and yesterday.fetched_date < today.fetched_date
),

with_zouka_rate as (
    select
        *,
        (today_stars - yesterday_stars) / nullif(yesterday_stars,0) as zouka_rate
    from ranked_pairs
    where recency_rank = 1
    and yesterday_stars >= 1000
),

trending as (
    select
        *,
        row_number() over (
            partition by today_date
            order by zouka_rate desc
        ) as trend_rank
    from with_zouka_rate
)

select *
from trending
where trend_rank <= 10