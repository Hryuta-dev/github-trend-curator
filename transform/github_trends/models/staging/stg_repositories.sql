with source as (
    select * from raw_repositories
),

cleaned as (
    select
        id,
        name,
        full_name,
        description,
        language,
        stargazers_count,
        forks_count,
        html_url,
        fetched_date
    from source
    where name is not null
      and language is not null
)

select * from cleaned
