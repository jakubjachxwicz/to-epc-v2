import pytest

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