import requests
import argparse
import logging
import json
import os
import copy
from pprint import pformat
import requests
import tqdm
from collections import deque
from conda_build.config import Config
from conda_build.index import update_index


logging.basicConfig(level=logging.INFO)
DEFAULT_BAD_LICENSES = ['agpl', '']

DOWNLOAD_URL="https://anaconda.org/{channel}/{name}/{version}/download/{platform}/{file_name}"
REPODATA = 'https://conda.anaconda.org/{channel}/{platform}/repodata.json'
DEFAULT_PLATFORMS = ['linux-64',
                     'linux-32',
                     'osx-64',
                     'win-64',
                     'win-32']


def get_repodata(channel, platform):
    """Get the repodata.json file for a channel/platform combo on anaconda.org

    Parameters
    ----------
    channel : str
        anaconda.org/CHANNEL
    platform : {'linux-64', 'linux-32', 'osx-64', 'win-32', 'win-64'}
        The platform of interest

    Returns
    -------
    info : dict
    packages : dict
        keyed on package name (e.g., twisted-16.0.0-py35_0.tar.bz2)
    """
    url = REPODATA.format(channel=channel, platform=platform)
    json = requests.get(url).json()
    return json.get('info', {}), json.get('packages', {})


def _make_arg_parser():
    ap = argparse.ArgumentParser(description="CLI interface for conda-mirror.py")

    ap.add_argument(
        '--upstream-channel',
        help='The anaconda channel to mirror'
    )
    ap.add_argument(
        '--target-directory',
        help='The place where packages should be mirrored to'
    )
    ap.add_argument(
        '--platform',
        nargs="+",
        help=("The OS platform(s) to mirror. one or more of: {'all',"
              " 'linux-64', 'linux-32', 'osx-64', 'win-32', 'win-64'}"),
        default=[],
    )

    return ap


def cli():
    ap = _make_arg_parser()
    args = ap.parse_args()
    if 'all' in args.platform and len(args.platform) != 1:
        logging.warning("If you pass 'all' as a platform option, all other "
                        "options will be ignored")
    main(args.upstream_channel, args.target_directory, args.platform)


def not_in_upstream(local_repo_metadata, upstream_repo_metadata):
    upstream_package_names = set(upstream_repo_metadata.keys())
    local_package_names = set(local_repo_metadata.keys())
    for pkg in upstream_package_names.difference(local_package_names):
        yield pkg


def not_blacklisted_license(package_names_to_mirror, upstream_repo_metadata,
                            bad_licenses=None):
    if bad_licenses is None:
        bad_licenses = DEFAULT_BAD_LICENSES

    upstream_package_names = list(upstream_repo_metadata.keys())

    for pkg in package_names_to_mirror:
        logging.info('checking if {} has a bad license'.format(pkg))
        pkg_info = upstream_repo_metadata[pkg]
        if not pkg_info.get('license', ''):
            logging.error("No license in {}. Will not mirror internally"
                          "".format(pkg))
        for license in bad_licenses:
            if pkg_info.get('license', '').lower() == license:
                logging.error("Not going to mirror {} because it's license is "
                              "not friendly: {}".format(pkg, license))
                break
        else:
            yield pkg


def main(upstream_channel, target_directory, platform):
    full_platform_list = copy.copy(platform)
    if 'all' in full_platform_list:
        full_platform_list.remove('all')
        full_platform_list = sorted(set(full_platform_list + DEFAULT_PLATFORMS))

    # make sure the target directory structure is in place
    if not os.path.exists(target_directory):
        logging.info("Making directory: {}".format(target_directory))
        os.makedirs(target_directory)
    for platform in full_platform_list:
        dir = os.path.join(target_directory, platform)
        if not os.path.exists(dir):
            logging.info("Making directory: {}".format(target_directory))
            os.makedirs(dir)

    logging.info("Going to look on {} for the following platforms: {}"
                 "".format(upstream_channel, full_platform_list))

    mirrored_packages = deque()
    # iterate over each platform in the upstream channel
    for platform in full_platform_list:
        upstream_repo_info, upstream_repo_packages = get_repodata(upstream_channel, platform)
        platform_dir = os.path.join(target_directory, platform)
        repodata_file = os.path.join(platform_dir, 'repodata.json')
        if not os.path.exists(repodata_file):
            run_conda_index(platform_dir)
        with open(repodata_file, 'r') as f:
            j = json.load(f)
            local_repo_info = j.get('info', {})
            local_repo_packages = j.get('packages', {})

        packages_to_mirror = not_in_upstream(local_repo_packages,
                                             upstream_repo_packages)
        packages_to_mirror = not_blacklisted_license(packages_to_mirror,
                                                     upstream_repo_packages)

        for idx, package in enumerate(packages_to_mirror):
            mirrored_packages.append((platform, package))
            info = upstream_repo_packages[package]
            url = DOWNLOAD_URL.format(
                channel=upstream_channel,
                name=info['name'],
                version=info['version'],
                platform=platform,
                file_name=package,
            )
            print(url)
            expected_size = info['size']
            chunk_size = 1024  # 1KB chunks
            expected_iterations = expected_size // chunk_size + 1
            with open(os.path.join(target_directory, platform, package), 'wb') as f:
                logging.info("Downloading {}".format(package))
                ret = requests.get(url, stream=True)
                for data in tqdm.tqdm(ret.iter_content(chunk_size),
                                      desc=package,
                                      unit="KB",
                                      total=expected_iterations):
                    f.write(data)
            if idx % 5 == 0:
                # intermittently run conda index so that, in case of failure,
                # not all downloads need to be repeated
                run_conda_index(os.path.join(target_directory, platform))

        # also run conda index at the end of the job
        run_conda_index(os.path.join(target_directory, platform))
    logging.info("Done mirroring.")
    logging.info("The packages that were mirrored are:")
    logging.info(pformat(mirrored_packages))

def run_conda_index(target_directory):
    logging.info("Indexing {}".format(target_directory))
    config = Config()
    config.timeout=1
    update_index(target_directory, config, could_be_mirror=False)


if __name__ == "__main__":
    cli()
