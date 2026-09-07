select *
from {{ref('daily_top10_by_growth_rate')}}
where 
yesterday_stars < 1000