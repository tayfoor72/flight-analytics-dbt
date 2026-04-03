{{ config({"severity":"Warn","tags":[]}) }}
{{ dbt_utils.test_accepted_range(column_name="latitude", max_value=90, min_value=-90, model=get_where_subquery(ref('int_airport_geography'))) }}