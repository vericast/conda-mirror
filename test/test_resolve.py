import pytest

from conda_mirror.conda_mirror import match
from conda_mirror.conda_mirror import get_repodata


@pytest.fixture(scope='module')
def repodata():
    return get_repodata('anaconda', 'linux-64')


def test_match(repodata):
    repodata_info, repodata_packages = repodata
    matched = match(repodata_packages, {'jupyter': 'name'})
    assert set([v['name'] for v in matched.values()]) == set(['jupyter'])
