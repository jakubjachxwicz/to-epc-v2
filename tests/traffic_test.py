import pytest
from unittest.mock import MagicMock

from epc.models import BearerConfig, UEState
from epc.traffic import TrafficGeneratorManager


def make_bearer(bearer_id=1, protocol="tcp", target_bps=1_000_000, active=True):
    return BearerConfig(
        bearer_id=bearer_id,
        protocol=protocol,
        target_bps=target_bps,
        active=active,
    )

def make_ue_state(ue_id=1, bearers=None, stats=None):
    return UEState(
        ue_id=ue_id,
        bearers=bearers or {},
        stats=stats or {},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_ue.return_value = make_ue_state()
    return repo

@pytest.fixture
def manager(mock_repo):
    return TrafficGeneratorManager(mock_repo)

@pytest.fixture
def configured_bearer():
    return make_bearer()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestStart:

    def test_start_adds_task(self, manager, configured_bearer):
        manager.start(ue_id=1, bearer=configured_bearer)
        assert (1, 1) in manager.tasks

    def test_start_raises_when_already_running(self, manager, configured_bearer):
        manager.start(ue_id=1, bearer=configured_bearer)
        with pytest.raises(ValueError, match="Traffic already running"):
            manager.start(ue_id=1, bearer=configured_bearer)

    def test_start_raises_when_no_protocol(self, manager):
        bearer = BearerConfig(bearer_id=2, target_bps=1_000_000, protocol=None)
        with pytest.raises(ValueError, match="Bearer not configured"):
            manager.start(ue_id=1, bearer=bearer)

    def test_start_raises_when_no_target_bps(self, manager):
        bearer = BearerConfig(bearer_id=3, protocol="udp", target_bps=None)
        with pytest.raises(ValueError, match="Bearer not configured"):
            manager.start(ue_id=1, bearer=bearer)

    def test_start_different_bearers_independently(self, manager):
        manager.start(ue_id=1, bearer=make_bearer(bearer_id=1))
        manager.start(ue_id=1, bearer=make_bearer(bearer_id=2))
        assert (1, 1) in manager.tasks
        assert (1, 2) in manager.tasks


class TestStop:

    def test_stop_removes_task(self, manager, configured_bearer):
        manager.start(ue_id=1, bearer=configured_bearer)
        manager.stop(ue_id=1, bearer_id=1)
        assert (1, 1) not in manager.tasks

    def test_stop_nonexistent_task_does_not_raise(self, manager):
        manager.stop(ue_id=99, bearer_id=99)  # brak wyjątku = sukces


class TestStopAll:

    def test_stop_all_clears_all_tasks(self, manager):
        manager.start(ue_id=1, bearer=make_bearer(bearer_id=1))
        manager.start(ue_id=1, bearer=make_bearer(bearer_id=2))
        manager.stop_all()
        assert len(manager.tasks) == 0

    def test_stop_all_on_empty_manager_does_not_raise(self, manager):
        manager.stop_all()  # brak wyjątku = sukces


class TestIsRunning:

    def test_is_running_returns_true_after_start(self, manager, configured_bearer):
        manager.start(ue_id=1, bearer=configured_bearer)
        assert manager.is_running(ue_id=1, bearer_id=1) is True

    def test_is_running_returns_false_before_start(self, manager):
        assert manager.is_running(ue_id=1, bearer_id=1) is False

    def test_is_running_returns_false_after_stop(self, manager, configured_bearer):
        manager.start(ue_id=1, bearer=configured_bearer)
        manager.stop(ue_id=1, bearer_id=1)
        assert manager.is_running(ue_id=1, bearer_id=1) is False