import pytest
from fastapi.testclient import TestClient

from epc import api as api_mod
from epc import traffic as traffic_mod
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
	db_path = tmp_path / "epc_test.db"
	monkeypatch.setenv("EPC_DB_PATH", str(db_path))
	api_mod._repo_singleton = None
	if traffic_mod.traffic_manager is not None:
		traffic_mod.traffic_manager.stop_all()
	traffic_mod.traffic_manager = None
	with TestClient(app) as test_client:
		yield test_client


def test_root_returns_status_message(client):
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"message": "EPC Simulator running"}


def test_list_ues_empty(client):
	response = client.get("/ues")
	assert response.status_code == 200
	assert response.json() == {"ues": []}


def test_attach_ue_success(client):
	response = client.post("/ues", json={"ue_id": 1})
	assert response.status_code == 200
	assert response.json() == {"status": "attached", "ue_id": 1}


def test_attach_ue_duplicate_returns_400(client):
	client.post("/ues", json={"ue_id": 1})
	response = client.post("/ues", json={"ue_id": 1})
	assert response.status_code == 400
	assert response.json()["detail"] == "UE already attached"


def test_get_ue_includes_default_bearer(client):
	client.post("/ues", json={"ue_id": 1})
	response = client.get("/ues/1")
	assert response.status_code == 200
	payload = response.json()
	assert payload["ue_id"] == 1
	assert "9" in payload["bearers"]


def test_detach_ue_success(client):
	client.post("/ues", json={"ue_id": 1})
	response = client.delete("/ues/1")
	assert response.status_code == 200
	assert response.json() == {"status": "detached", "ue_id": 1}


def test_add_bearer_success(client):
	client.post("/ues", json={"ue_id": 1})
	response = client.post("/ues/1/bearers", json={"bearer_id": 3})
	assert response.status_code == 200
	assert response.json() == {"status": "bearer_added", "ue_id": 1, "bearer_id": 3}


def test_delete_bearer_success(client):
	client.post("/ues", json={"ue_id": 1})
	client.post("/ues/1/bearers", json={"bearer_id": 3})
	response = client.delete("/ues/1/bearers/3")
	assert response.status_code == 200
	assert response.json() == {"status": "bearer_deleted", "ue_id": 1, "bearer_id": 3}


def test_delete_default_bearer_returns_400(client):
	client.post("/ues", json={"ue_id": 1})
	response = client.delete("/ues/1/bearers/9")
	assert response.status_code == 400
	assert response.json()["detail"] == "Cannot remove default bearer"


def test_start_and_stop_traffic_success(client):
	client.post("/ues", json={"ue_id": 1})
	client.post("/ues/1/bearers", json={"bearer_id": 3})
	start_response = client.post(
		"/ues/1/bearers/3/traffic",
		json={"protocol": "udp", "bps": 1000},
	)
	assert start_response.status_code == 200
	assert start_response.json() == {
		"status": "traffic_started",
		"ue_id": 1,
		"bearer_id": 3,
		"target_bps": 1000,
	}
	stop_response = client.delete("/ues/1/bearers/3/traffic")
	assert stop_response.status_code == 200
	assert stop_response.json() == {
		"status": "traffic_stopped",
		"ue_id": 1,
		"bearer_id": 3,
	}
