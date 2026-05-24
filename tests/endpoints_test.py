import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from epc.api import (
    get_ues_stats, list_ues, attach_ue, get_ue, detach_ue,
    add_bearer, delete_bearer, start_traffic, stop_traffic,
    get_traffic_stats, reset_all,
)
from epc.models import (
    AttachUERequest, AddBearerRequest, StartTrafficRequest,
    UEState, BearerConfig, ThroughputStats,
)


def ue_with_bearers(ue_id=1, bearer_ids=(9,)):
    """Real UEState with the given bearers."""
    state = UEState(ue_id=ue_id)
    for bid in bearer_ids:
        state.bearers[bid] = BearerConfig(bearer_id=bid)
    return state


def stats_1s(ue_id=1, bearer_id=9):
    """Stats engineered so duration == 1.0s -> tx_bps=1_000_000, rx_bps=500_000."""
    return ThroughputStats(
        bearer_id=bearer_id, ue_id=ue_id,
        bytes_tx=125_000, bytes_rx=62_500,
        start_ts=1000.0, last_update_ts=1001.0,
        protocol="tcp", target_bps=1_000_000,
    )


# --- attach_ue ---

def test_attach_ue_success():
    repo = MagicMock()
    result = attach_ue(AttachUERequest(ue_id=1), repo)
    assert result.status == "attached"
    repo.attach_ue.assert_called_once_with(1)


def test_attach_ue_failure_400():
    repo = MagicMock()
    repo.attach_ue.side_effect = ValueError("UE already attached")
    with pytest.raises(HTTPException) as exc:
        attach_ue(AttachUERequest(ue_id=1), repo)
    assert exc.value.status_code == 400


# --- get_ue ---

def test_get_ue_success():
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(5)
    result = get_ue(5, repo)
    assert result.ue_id == 5
    assert 9 in result.bearers


def test_get_ue_failure_400():
    repo = MagicMock()
    repo.get_ue.side_effect = ValueError("UE not found")
    with pytest.raises(HTTPException) as exc:
        get_ue(99, repo)
    assert exc.value.status_code == 400


# --- detach_ue ---

def test_detach_ue_success():
    repo = MagicMock()
    result = detach_ue(7, repo)
    assert result.status == "detached"
    repo.detach_ue.assert_called_once_with(7)


def test_detach_ue_failure_400():
    repo = MagicMock()
    repo.detach_ue.side_effect = ValueError("UE not found")
    with pytest.raises(HTTPException) as exc:
        detach_ue(99, repo)
    assert exc.value.status_code == 400


# --- list_ues (nie ma failure brancha) ---

def test_list_ues_success():
    repo = MagicMock()
    repo.list_ues.return_value = [1, 2, 3]
    result = list_ues(repo)
    assert result.ues == [1, 2, 3]


# --- add_bearer ---

def test_add_bearer_success():
    repo = MagicMock()
    result = add_bearer(1, AddBearerRequest(bearer_id=3), repo)
    assert result.status == "bearer_added"
    repo.add_bearer.assert_called_once_with(1, 3)


def test_add_bearer_failure_400():
    repo = MagicMock()
    repo.add_bearer.side_effect = ValueError("Bearer already exists")
    with pytest.raises(HTTPException) as exc:
        add_bearer(1, AddBearerRequest(bearer_id=3), repo)
    assert exc.value.status_code == 400


# --- delete_bearer ---

@patch("epc.api.get_traffic_manager")
def test_delete_bearer_success(mock_get_tm):
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9, 3))
    mock_tm = MagicMock()
    mock_tm.is_running.return_value = False
    mock_get_tm.return_value = mock_tm
    result = delete_bearer(1, 3, repo)
    assert result.status == "bearer_deleted"
    repo.delete_bearer.assert_called_once_with(1, 3)


def test_delete_bearer_failure_400():
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9,))
    with pytest.raises(HTTPException) as exc:
        delete_bearer(1, 3, repo)  # bearer 3 not present
    assert exc.value.status_code == 400


# --- start_traffic ---

@patch("epc.api.get_traffic_manager")
def test_start_traffic_success(mock_get_tm):
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9,))
    mock_get_tm.return_value = MagicMock()
    body = StartTrafficRequest(protocol="tcp", Mbps=1)
    result = start_traffic(1, 9, body, repo)
    assert result.status == "traffic_started"
    assert result.target_bps == 1_000_000


def test_start_traffic_failure_400():
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9,))
    body = StartTrafficRequest(protocol="tcp", Mbps=1)
    with pytest.raises(HTTPException) as exc:
        start_traffic(1, 5, body, repo)  # bearer 5 nie istnieje
    assert exc.value.status_code == 400


# --- stop_traffic ---

@patch("epc.api.get_traffic_manager")
def test_stop_traffic_success(mock_get_tm):
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9,))
    mock_get_tm.return_value = MagicMock()
    result = stop_traffic(1, 9, repo)
    assert result.status == "traffic_stopped"


def test_stop_traffic_failure_400():
    repo = MagicMock()
    repo.get_ue.return_value = ue_with_bearers(1, bearer_ids=(9,))
    with pytest.raises(HTTPException) as exc:
        stop_traffic(1, 5, repo)  # bearer 5 nie istnieje
    assert exc.value.status_code == 400


# --- get_traffic_stats ---

@patch("epc.api.get_traffic_manager")
def test_get_traffic_stats_success(mock_get_tm):
    repo = MagicMock()
    state = ue_with_bearers(1, bearer_ids=(9,))
    state.stats[9] = stats_1s()
    repo.get_ue.return_value = state
    mock_tm = MagicMock()
    mock_tm.is_running.return_value = False
    mock_get_tm.return_value = mock_tm
    result = get_traffic_stats(1, 9, repo)
    assert result.tx_bps == 1_000_000
    assert result.rx_bps == 500_000


def test_get_traffic_stats_failure_400():
    repo = MagicMock()
    repo.get_ue.side_effect = ValueError("UE not found")
    with pytest.raises(HTTPException) as exc:
        get_traffic_stats(99, 9, repo)
    assert exc.value.status_code == 400


# --- get_ues_stats ---

@patch("epc.api.get_traffic_manager")
def test_get_ues_stats_success(mock_get_tm):
    repo = MagicMock()
    state = ue_with_bearers(1, bearer_ids=(9,))
    state.stats[9] = stats_1s()
    repo.list_ues.return_value = [1]
    repo.get_ue.return_value = state
    mock_tm = MagicMock()
    mock_tm.is_running.return_value = False
    mock_get_tm.return_value = mock_tm
    result = get_ues_stats(repo)
    assert result.total_tx_bps == 1_000_000
    assert result.bearer_count == 1


def test_get_ues_stats_failure_400():
    repo = MagicMock()
    repo.ue_exists.return_value = False
    with pytest.raises(HTTPException) as exc:
        get_ues_stats(repo, ue_id=42)
    assert exc.value.status_code == 400


# --- reset_all (nie ma failure brancha) ---

@patch("epc.api.get_traffic_manager")
def test_reset_all_success(mock_get_tm):
    repo = MagicMock()
    mock_tm = MagicMock()
    mock_get_tm.return_value = mock_tm
    result = reset_all(repo)
    mock_tm.stop_all.assert_called_once()
    repo.reset_all.assert_called_once()
    assert result.status == "reset"
