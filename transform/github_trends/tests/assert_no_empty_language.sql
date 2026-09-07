select *
from {{ ref('stg_repositories') }}
where language = ''