import conda_mirror
import pytest

def test_get_repodata():
    conda_mirror.get_repodata('anaconda', 'linux-64')

