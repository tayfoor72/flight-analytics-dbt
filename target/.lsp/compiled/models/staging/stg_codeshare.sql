with source as (
    select
        *
    from `workspace`.`flight_analytics`.`codeshare`
),

cleaned as (
    select
        codeshare_id,
        flight_id,
        flight_number as codeshare_flight_number,
        airline_id as marketing_airline_id,
        airline_name as marketing_airline_name

    from source

)

select
    *
from cleaned