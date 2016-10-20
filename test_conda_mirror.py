import conda_mirror
import pytest
import requests_mock
import os
import subprocess


@pytest.fixture(scope='session')
def repo():
    return os.path.join('test/local-repo')


def ensure_local_repo(repo):
    print("Regenerating local repo")
    subprocess.check_call(('python regenerate-repodata.py %s' % repo).split())


@pytest.mark.first
def test_ensure_local_repo(repo):
    if os.path.exists(repo):
        pytest.skip("Don't need to regenerate repo. If you want to force "
                    "regeneration, remove the 'local-repo' dir")
    ensure_local_repo(repo)


@pytest.mark.parametrize('platform', conda_mirror.DEFAULT_PLATFORMS)
def test_get_repodata(repo, platform):
    channel = "test"
    with requests_mock.mock() as m:
        repodata = os.path.join(repo, platform, 'repodata.json')
        with open(repodata, 'r') as f:
            mock_address = conda_mirror.REPODATA.format(
                channel=channel,
                platform=platform
            )
            print('mock_address=%s' % mock_address)
            m.get(mock_address, text=f.read())

        ret = conda_mirror.get_repodata(channel, platform)
        assert ret


