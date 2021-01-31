import pytest
from moto import mock_dynamodb2


@pytest.fixture
def dynamodb():
    with mock_dynamodb2():
        yield
