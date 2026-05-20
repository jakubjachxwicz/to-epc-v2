import pytest
from unittest.mock import Mock
from epc.db import EPCRepository
from epc.models import AttachUERequest, AddBearerRequest
from epc import api as api_mod

@pytest.mark.parametrize("ue_id", [1, 42, 100])
def test_attach_request_accepts_valid_range(ue_id):
    model = AttachUERequest(ue_id=ue_id)
    assert model.ue_id == ue_id

@pytest.mark.parametrize("bearer_id", [1, 5, 9])
def test_add_bearer_request_accepts_valid_range(bearer_id):
    model = AddBearerRequest(bearer_id=bearer_id)
    assert model.bearer_id == bearer_id
