{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="longitude", max_value=180, min_value=-180, model=get_where_subquery(ref('int_airport_geography'))) }}