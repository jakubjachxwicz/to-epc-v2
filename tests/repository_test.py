import pytest
from epc.db import EPCRepository

@pytest.fixture
def repo(tmp_path):
    return EPCRepository(db_path=str(tmp_path / "test.db"))

def test_repository_ue_exists(repo):
    assert repo.ue_exists(9) is False
    repo.attach_ue(9)
    assert repo.ue_exists(9) is True

def test_repository_attach_creates_default_bearer(repo):
    repo.attach_ue(1)
    ue = repo.get_ue(1)
    assert 9 in ue.bearers

def test_repository_detach_removes_ue(repo):
    repo.attach_ue(1)
    repo.detach_ue(1)
    assert repo.ue_exists(1) is False

def test_repository_delete_default_bearer_raises(repo):
    repo.attach_ue(1)
    with pytest.raises(ValueError, match="Cannot remove default bearer"):
        repo.delete_bearer(1, bearer_id=9)

def test_repository_add_and_delete_bearer(repo):
    repo.attach_ue(1)
    repo.add_bearer(1, bearer_id=3)
    assert 3 in repo.get_ue(1).bearers
    repo.delete_bearer(1, bearer_id=3)
    assert 3 not in repo.get_ue(1).bearers

def test_list_ues_returns_attached_ids(repo):
    repo.attach_ue(1)
    repo.attach_ue(2)
    assert list(repo.list_ues()) == [1, 2]


def test_attach_duplicate_ue_raises(repo):
    repo.attach_ue(1)
    with pytest.raises(ValueError, match="already attached"):
        repo.attach_ue(1)


def test_detach_nonexistent_ue_raises(repo):
    with pytest.raises(ValueError, match="not found"):
        repo.detach_ue(99)


def test_get_ue_returns_state(repo):
    repo.attach_ue(1)
    ue = repo.get_ue(1)
    assert ue.ue_id == 1


def test_get_ue_nonexistent_raises(repo):
    with pytest.raises(ValueError, match="not found"):
        repo.get_ue(99)


def test_save_ue_persists_changes(repo):
    from epc.models import UEState, BearerConfig
    repo.attach_ue(1)
    state = repo.get_ue(1)
    state.bearers[5] = BearerConfig(bearer_id=5)
    repo.save_ue(state)
    assert 5 in repo.get_ue(1).bearers


def test_add_bearer_duplicate_raises(repo):
    repo.attach_ue(1)
    repo.add_bearer(1, bearer_id=3)
    with pytest.raises(ValueError, match="Bearer already exists"):
        repo.add_bearer(1, bearer_id=3)


def test_update_bearer_persists(repo):
    from epc.models import BearerConfig
    repo.attach_ue(1)
    bearer = BearerConfig(bearer_id=9, protocol="tcp", target_bps=1000)
    repo.update_bearer(1, bearer)
    assert repo.get_ue(1).bearers[9].target_bps == 1000


def test_update_stats_persists(repo):
    from epc.models import ThroughputStats
    import time
    repo.attach_ue(1)
    stats = ThroughputStats(bearer_id=9, ue_id=1, start_ts=time.time(), bytes_tx=500)
    repo.update_stats(1, stats)
    assert repo.get_ue(1).stats[9].bytes_tx == 500


def test_delete_bearer_nonexistent_raises(repo):
    repo.attach_ue(1)
    with pytest.raises(ValueError, match="Bearer not found"):
        repo.delete_bearer(1, bearer_id=5)


def test_reset_all_removes_all_ues(repo):
    repo.attach_ue(1)
    repo.attach_ue(2)
    repo.reset_all()
    assert list(repo.list_ues()) == []