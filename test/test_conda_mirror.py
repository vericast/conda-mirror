import bz2
import copy
import itertools
import json
import os
import sys

import pytest

from conda_mirror import conda_mirror


@pytest.fixture(scope='module')
def repodata():
    repodata = {}
    for channel in ['anaconda', 'conda-forge']:
        repodata[channel] = conda_mirror.get_repodata(channel, 'linux-64')
    return repodata


def test_match(repodata):
    repodata_info, repodata_packages = repodata['anaconda']
    matched = conda_mirror._match(repodata_packages, {'name': 'jupyter'})
    assert set([v['name'] for v in matched.values()]) == set(['jupyter'])

    matched = conda_mirror._match(repodata_packages, {'name': "*"})
    assert len(matched) == len(repodata_packages)

@pytest.mark.parametrize(
    'channel,platform',
    itertools.product(['anaconda', 'conda-forge'], ['linux-64']))
def test_cli(tmpdir, channel, platform, repodata):
    info, packages = repodata[channel]
    smallest_package = sorted(packages, key=lambda x: packages[x]['size'])[0]
    f2 = tmpdir.mkdir(channel)
    f2.mkdir(platform)
    f1 = tmpdir.mkdir('conf').join('conf.yaml')

    f1.write('''
blacklist:
    - name: "*"
whitelist:
    - name: {}
      version: {}'''.format(
            packages[smallest_package]['name'],
            packages[smallest_package]['version']))
    cli_args = ("conda-mirror"
                " --config {config}"
                " --upstream-channel {channel}"
                " --target-directory {target_directory}"
                " --platform {platform}"
                " --pdb"
                " --verbose"
                ).format(config=f1.strpath,
                         channel=channel,
                         target_directory=f2.strpath,
                         platform=platform)
    old_argv = copy.deepcopy(sys.argv)
    sys.argv = cli_args.split(' ')
    conda_mirror.cli()
    sys.argv = old_argv

    for f in ['repodata.json', 'repodata.json.bz2']:
        # make sure the repodata file exists
        assert f in os.listdir(os.path.join(f2.strpath, platform))

    # make sure that the repodata contains less than upstream since we prune it
    with open(os.path.join(f2.strpath, platform, 'repodata.json'), 'r') as f:
        disk_repodata = json.load(f)
    disk_info = disk_repodata.get('info', {})
    assert len(disk_info) == len(info)
    disk_packages = disk_repodata.get('packages', {})
    assert len(disk_packages) < len(packages)
    with bz2.BZ2File(os.path.join(f2.strpath,
                                  platform,
                                  'repodata.json.bz2'), 'r') as f:
        contents = f.read().decode()
        rd = json.loads(contents)
        assert len(rd['info']) == len(disk_info)
        assert len(rd['packages']) == len(disk_packages)



def test_handling_bad_package(tmpdir, repodata):
    # ensure that bad conda packages are actually removed by run_conda_index
    local_repo_root = tmpdir.mkdir('repo').strpath
    bad_pkg_root = os.path.join(local_repo_root, 'linux-64')
    os.makedirs(bad_pkg_root)
    bad_pkg_name = 'bad-1-0.tar.bz2'

    # Test removal functionality of packages that are not in the upstream
    # repodata.json
    conda_mirror.logger.info("Testing %s", bad_pkg_name)
    with bz2.BZ2File(os.path.join(bad_pkg_root, bad_pkg_name), 'wb') as f:
        f.write("This is a fake package".encode())
    assert bad_pkg_name in os.listdir(bad_pkg_root)
    conda_mirror._validate_packages(repodata, bad_pkg_root)
    assert bad_pkg_name not in os.listdir(bad_pkg_root)

    # Test removal of broken packages that do exist in upstream repodata.json
    anaconda_repodata = repodata['anaconda'][1]
    bad_pkg_name = next(iter(anaconda_repodata.keys()))
    conda_mirror.logger.info("Testing %s", bad_pkg_name)
    with bz2.BZ2File(os.path.join(bad_pkg_root, bad_pkg_name), 'wb') as f:
        f.write("This is a fake package".encode())
    assert bad_pkg_name in os.listdir(bad_pkg_root)
    conda_mirror._validate_packages(anaconda_repodata, bad_pkg_root)
    assert bad_pkg_name not in os.listdir(bad_pkg_root)
