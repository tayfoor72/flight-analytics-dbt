-- Enrich flights with departure and arrival airport attributes --
select 
    fd.flight_id, 
    fd.flight_date,
    fd.flight_number, 
    fd.flight_status,

    fd.departure_airport_id,
    dep.airport_name as departure_airport_name,
    
    fd.arrival_airport_id, 
    arr.airport_name as arrival_airport_name

from `flight-analytics-dbt`.`staging_models`.`stg_flight_details` fd

left join `flight-analytics-dbt`.`staging_models`.`stg_airports` dep
    on fd.departure_airport_id = dep.airport_id
left join `flight-analytics-dbt`.`staging_models`.`stg_airports` arr
    on fd.arrival_airport_id = arr.airport_id;