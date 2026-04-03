
select
    c.flight_id,
    fd.airline_id as operating_airline_id,
    op.airline_name as operating_airline_name,
    c.marketing_airline_id  as marketing_airline_id,
    mk.airline_name as marketing_airline_name

from `flight-analytics-dbt`.`staging_models`.`stg_codeshare` c

left join `flight-analytics-dbt`.`staging_models`.`stg_flight_details` fd
    on c.flight_id = fd.flight_id

left join `flight-analytics-dbt`.`staging_models`.`stg_airline` op
    on fd.airline_id = op.airline_id

left join `flight-analytics-dbt`.`staging_models`.`stg_airline` mk
    on c.marketing_airline_id = mk.airline_id ;

