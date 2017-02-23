import bz2
import copy
import itertools
import json
import os
import sys

import pytest

from conda_mirror import conda_mirror

anaconda_channel = 'https://repo.continuum.io/pkgs/free'


@pytest.fixture(scope='module')
def repodata():
    repodata = {}
    repodata['conda-forge'] = conda_mirror.get_repodata('conda-forge',
                                                        'linux-64')
    repodata[anaconda_channel] = conda_mirror.get_repodata(anaconda_channel,
                                                           'linux-64')
    return repodata


def test_match(repodata):
    repodata_info, repodata_packages = repodata[anaconda_channel]
    matched = conda_mirror._match(repodata_packages, {'name': 'jupyter'})
    assert set([v['name'] for v in matched.values()]) == set(['jupyter'])

    matched = conda_mirror._match(repodata_packages, {'name': "*"})
    assert len(matched) == len(repodata_packages)


def test_version():
    old_args = copy.copy(sys.argv)
    sys.argv = ['conda-mirror', '--version']
    conda_mirror.cli()
    sys.argv = old_args


@pytest.mark.parametrize(
    'channel,platform',
    itertools.product([anaconda_channel, 'conda-forge'], ['linux-64']))
def test_cli(tmpdir, channel, platform, repodata):
    info, packages = repodata[channel]
    smallest_package = sorted(packages, key=lambda x: packages[x]['size'])[0]
    # drop the html stuff. get just the channel

    f2 = tmpdir.mkdir(channel.rsplit('/', 1)[-1])
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
    # Write a package that does not exist in the upstream repodata into the mirror path
    # to make sure we exercise a broken code path
    # https://github.com/maxpoint/conda-mirror/issues/29
    _write_bad_package(channel_dir=f2.strpath, platform_name=platform,
                       pkg_name='bad-1-0.tar.bz2')
    # Write a bad package that does exist in the upstream repodata into the mirror path
    # to make sure we can handle that case too
    upstream_pkg_name = next(iter(repodata.keys()))
    _write_bad_package(channel_dir=f2.strpath, platform_name=platform,
                       pkg_name=upstream_pkg_name)
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

def _write_bad_package(channel_dir, platform_name, pkg_name):
    target_dir = os.path.join(channel_dir, platform_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    with bz2.BZ2File(os.path.join(target_dir, pkg_name), 'wb') as f:
        f.write("This is a fake package".encode())

