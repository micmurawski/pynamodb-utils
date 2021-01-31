from freezegun import freeze_time

from .conftest import ExampleEnum


@freeze_time("2019-01-01 00:00:00+00:00")
def test_fm_resource_model_create(resource_model):
    model = resource_model

    obj = model(
        ID='1',
        enum=ExampleEnum.A.value,
        map={
            "key": "value"
        }
    )
    obj.save()
    assert obj.enum == ExampleEnum.A.value
    assert obj.map.key == 'value'
    assert obj.as_dict() == {
        'ID': '1',
        'CreatedAt': '2019-01-01 00:00:00+00:00',
        'DeletedAt': None,
        'UpdatedAt': '2019-01-01 00:00:00+00:00',
        'enum': 'A',
        'map': {
            'key': 'value'
        }
    }
