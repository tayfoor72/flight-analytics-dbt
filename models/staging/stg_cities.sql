
with source as (
    select *
    from {{ source('flights', 'cities') }}
),

cleaned as (
    select
        city_id, 
        country_id,

        -- descriptive columns --
        trim(city_name) as city_name,

        -- geographical columns --
        case
            when safe_cast(latitude as float64) = -999.0 then null
            else safe_cast(latitude as float64)
        end as latitude,

        case
            when safe_cast(longitude as float64) = -999.0 then null
            else safe_cast(longitude as float64)
        end as longitude,

        timezone as city_timezone, 
        gmt_offset as city_gmt_offset

    from source

)

select * from cleaned
