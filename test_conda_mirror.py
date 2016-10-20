import conda_mirror
import pytest
import requests_mock
import os
import subprocess
from contextlib import contextmanager

@pytest.fixture(scope='session')
def local_repo_root():
    return os.path.join('test/local-repo')


def ensure_local_repo(repo):
    print("Regenerating local repo")
    subprocess.check_call(('python regenerate-repodata.py %s' % repo).split())


@pytest.mark.first
def test_ensure_local_repo(local_repo_root):
    if os.path.exists(local_repo_root):
        pytest.skip("Don't need to regenerate repo. If you want to force "
                    "regeneration, remove the 'local-repo' dir")
    ensure_local_repo(local_repo_root)

@contextmanager
def conda_mock(platform, repo):
    channel = os.path.basename(repo)
    with requests_mock.mock() as m:
        repodata = os.path.join(repo, platform, 'repodata.json')
        with open(repodata, 'r') as f:
            mock_address = conda_mirror.REPODATA.format(
                channel=channel,
                platform=platform
            )
            print('mock_address=%s' % mock_address)
            m.get(mock_address, text=f.read())
        yield


@pytest.mark.parametrize('platform', conda_mirror.DEFAULT_PLATFORMS)
def test_get_repodata(local_repo_root, platform):
    with conda_mock(platform, local_repo_root):
        channel = os.path.basename(local_repo_root)
        ret = conda_mirror.get_repodata(channel, platform)
        assert ret


