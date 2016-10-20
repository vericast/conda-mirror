import conda_mirror
import pytest
import requests_mock
import os
import subprocess
import sys


def test_regenerate_local_repo():
    if os.path.exists('local-repo'):
        raise pytest.skip("Don't need to regenerate repo. If you want to force "
                          "regeneration, remove the 'local-repo' dir")
    print("Regenerating local repo")
    subprocess.check_call('python regenerate-repodata.py'.split())


@pytest.mark.parametrize('platform', conda_mirror.DEFAULT_PLATFORMS)
def test_get_repodata(platform):
    channel = "test"
    with requests_mock.mock() as m:
        repodata = os.path.join('local-repo', platform, 'repodata.json')
        with open(repodata, 'r') as f:
            mock_address = conda_mirror.REPODATA.format(
                channel=channel,
                platform=platform
            )
            print('mock_address=%s' % mock_address)
            m.get(mock_address, text=f.read())

        ret = conda_mirror.get_repodata(channel, platform)
        assert ret

