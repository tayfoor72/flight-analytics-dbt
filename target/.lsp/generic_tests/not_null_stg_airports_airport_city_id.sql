{{ config({"severity":"Warn","tags":[]}) }}
{{ test_not_null(column_name="airport_city_id", model=get_where_subquery(ref('stg_airports'))) }}