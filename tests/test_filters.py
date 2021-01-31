def test_filters_dynamic_map(resource_model):
    _filter = resource_model.get_conditions_from_json(query={
        'map.key': 'value',
        'enum__not_equals': 'B'
    })
    assert _filter.__repr__() == "(map.key = {'S': 'value'} AND (NOT enum = {'S': 'B'}))"
