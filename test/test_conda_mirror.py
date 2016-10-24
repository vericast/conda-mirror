from conda_mirror import conda_mirror
import pytest
import requests_mock
import os
import subprocess
from contextlib import contextmanager
import sys
import copy

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
                    "regeneration, remove the 'test/local-repo' dir")
    ensure_local_repo(local_repo_root)

@contextmanager
def conda_mock(platforms, repo):
    channel = os.path.basename(repo)
    with requests_mock.mock() as m:
        for platform in platforms:
            repodata = os.path.join(repo, platform, 'repodata.json')
            with open(repodata, 'r') as f:
                json_text = f.read()

            mock_address = conda_mirror.REPODATA.format(
                channel=channel,
                platform=platform
            )
            # mock the info address
            m.get(mock_address, text=json_text)
            # now we need to mock the download addresses
            repo_info, repo_package_data = conda_mirror.get_repodata(channel, platform)
            for pkg_name, pkg_info in repo_package_data.items():
                url = conda_mirror.DOWNLOAD_URL.format(
                    channel=channel,
                    name=pkg_info['name'],
                    version=pkg_info['version'],
                    platform=platform,
                    file_name=pkg_name,
                )
                with open(os.path.join(repo, platform, pkg_name), 'rb') as f:
                    data = f.read()
                m.get(url, content=data)
        yield


@pytest.mark.parametrize('platform', conda_mirror.DEFAULT_PLATFORMS)
def test_mirror_main(local_repo_root, platform, tmpdir):
    with conda_mock([platform], local_repo_root):
        channel = os.path.basename(local_repo_root)
        mirror_test_dir = tmpdir.mkdir('mirror-test')
        platform_dir = os.path.join(str(mirror_test_dir), platform)
        os.mkdir(platform_dir)
        repodata_file = os.path.join(platform_dir, 'repodata.json')
        with open(repodata_file, 'w') as f:
            f.write("{}")
        conda_mirror.main(channel, str(mirror_test_dir), [platform])
        # Make sure we mirror both files
        downloaded_files = os.listdir(platform_dir)
        assert "a-1-0.tar.bz2" in downloaded_files
        assert "b-1-0.tar.bz2" in downloaded_files
        # now lets remove one of them and try and mirror again
        file_to_remove = "a-1-0.tar.bz2"
        os.remove(os.path.join(platform_dir, file_to_remove))
        # need to reindex the directory
        conda_mirror.run_conda_index(platform_dir)

        assert file_to_remove not in os.listdir(platform_dir)

        conda_mirror.main(channel, str(mirror_test_dir), [platform])

        # Make sure we mirror both files
        downloaded_files = os.listdir(platform_dir)
        assert "a-1-0.tar.bz2" in downloaded_files
        assert "b-1-0.tar.bz2" in downloaded_files


def test_cli(local_repo_root, tmpdir):
    with conda_mock(conda_mirror.DEFAULT_PLATFORMS, local_repo_root):
        old_argv = copy.copy(sys.argv)
        local_mirror = tmpdir.mkdir('cli-test')
        for platform in conda_mirror.DEFAULT_PLATFORMS:
            platform_dir = os.path.join(str(local_mirror), platform)
            os.mkdir(platform_dir)
            repodata_file = os.path.join(platform_dir, 'repodata.json')
            with open(repodata_file, 'w') as f:
                f.write("{}")

        channel = os.path.basename(local_repo_root)
        sys.argv = ['conda_mirror.py',
                    '--upstream-channel', channel,
                    '--target-directory', str(local_mirror),
                    '--platform', 'all', 'linux-64']

        conda_mirror.cli()

        for platform in conda_mirror.DEFAULT_PLATFORMS:
            platform_dir = os.path.join(str(local_mirror), platform)
            contents = os.listdir(platform_dir)
            assert "a-1-0.tar.bz2" in contents
            assert "b-1-0.tar.bz2" in contents



