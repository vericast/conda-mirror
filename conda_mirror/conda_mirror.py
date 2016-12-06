from __future__ import (unicode_literals, print_function, division,
                        absolute_import)

import argparse
import copy
import json
import logging
import os
import pdb
import sys
import tarfile
from collections import deque
from glob import fnmatch
from pprint import pformat

import requests
import tqdm
import yaml
from conda_build.config import Config
from conda_build.index import update_index,read_index_tar


logger = None


DEFAULT_BAD_LICENSES = ['agpl', '']

DOWNLOAD_URL="https://anaconda.org/{channel}/{name}/{version}/download/{platform}/{file_name}"
REPODATA = 'https://conda.anaconda.org/{channel}/{platform}/repodata.json'
DEFAULT_PLATFORMS = ['linux-64',
                     'linux-32',
                     'osx-64',
                     'win-64',
                     'win-32']


def match(all_packages, key_glob_dict):
    """

    Parameters
    ----------
    all_packages : iterable
        Iterable of package metadata dicts from repodata.json
    key_glob_dict : iterable of kv pairs
        Iterable of (key, glob_value) dicts

    Returns
    -------
    matched : dict
        Iterable of package metadata dicts which match the `target_packages`
        (key, glob_value) tuples
    """
    matched = dict()
    for pkg_name, pkg_info in all_packages.items():
        for glob, key in key_glob_dict.items():
            # normalize the strings so that comparisons are easier
            name = str(pkg_info.get(key, '')).lower()
            pattern = glob.lower()
            if fnmatch.fnmatch(name, pattern):
                matched.update({pkg_name: pkg_info})

    return matched


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
    """
    Localize the ArgumentParser logic

    Returns
    -------
    argument_parser : argparse.ArgumentParser
        The instantiated argument parser for this CLI
    """
    ap = argparse.ArgumentParser(description="CLI interface for conda-mirror.py")

    ap.add_argument(
        '--upstream-channel',
        help='The anaconda channel to mirror',
        required=True
    )
    ap.add_argument(
        '--target-directory',
        help='The place where packages should be mirrored to',
        required=True
    )
    ap.add_argument(
        '--platform',
        help=("The OS platform(s) to mirror. one of: {'linux-64', 'linux-32',"
              "'osx-64', 'win-32', 'win-64'}"),
        required=True
    )
    ap.add_argument(
        '-v', '--verbose',
        action="store_true",
        help="This basically turns on tqdm progress bars for downloads",
        default=False,
    )
    ap.add_argument(
        '--config',
        action="store",
        help="Path to the yaml config file",
    )
    ap.add_argument(
        '--pdb',
        action="store_true",
        help="Enable PDB debugging on exception",
        default=False,
    )
    return ap


def cli():
    """
    Collect arguments from sys.argv and invoke the main() function.
    """
    parser = _make_arg_parser()
    args = parser.parse_args()

    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG

    global logger
    logger = logging.getLogger('conda_mirror')
    logger.setLevel(loglevel)

    if args.pdb:
        # set the pdb_hook as the except hook for all exceptions
        def pdb_hook(exctype, value, traceback):
            pdb.post_mortem(traceback)
        sys.excepthook = pdb_hook

    config_dict = {}
    if args.config:
        logger.info("Loading config from %s", args.config)
        with open(args.config, 'r') as f:
            config_dict = yaml.load(f)
        logger.info("config: %s", config_dict)
    blacklist = config_dict.get('blacklist')
    whitelist = config_dict.get('whitelit')

    pseudocode(args.upstream_channel, args.target_directory, args.platform,
               blacklist, whitelist, args.verbose)

def not_in_upstream(local_repo_metadata, upstream_repo_metadata):
    """
    Produce a stream of packages that exist on the upstream channel but
    not the local mirror

    Parameters
    ----------
    local_repo_metadata : dict
        This is the 'packages' key from the repodata.json file
        from the local channel
    upstream_repo_metadata : dict
        This is the 'packages' key from the repodata.json file
        from the upstream channel

    Yields
    ------
    package_name : str
        A continuous stream of package names that exist on the upstream channel
        but not the local one
    """
    upstream_package_names = set(upstream_repo_metadata.keys())
    local_package_names = set(local_repo_metadata.keys())
    for pkg in upstream_package_names.difference(local_package_names):
        yield pkg


def not_blacklisted_license(package_names_to_mirror, upstream_repo_metadata,
                            bad_licenses=None):
    """
    Trim list of packages to mirror based on their listed licenses

    Parameters
    ----------
    package_names_to_mirror : iterable
        An iterable of package names to check and see if they have unfriendly
        licenses. These package names should be keys in the
        `upstream_repo_metadata` dict
    upstream_repo_metadata : dict
        The 'packages' value of the repodata.json dict for the upstream channel
        that we are mirroring locally
    bad_licenses: iterable, optional
        All licenses that are considered "bad".  Packages whose licenses are
        in `bad_licenses` will not be mirrored locally.
        Defaults to module level `DEFAULT_BAD_LICENSES`

    Yields
    ------
    package_name : str
        A continuous stream of package names whose licenses do not match those
        in `bad_licenses`
    """
    if bad_licenses is None:
        bad_licenses = DEFAULT_BAD_LICENSES
    none_is_bad = False
    if None in bad_licenses:
        none_is_bad = True
        bad_licenses.remove(None)

    upstream_package_names = list(upstream_repo_metadata.keys())

    for pkg in package_names_to_mirror:
        logger.info('checking if {} has a bad license'.format(pkg))
        pkg_info = upstream_repo_metadata[pkg]
        pkg_license = pkg_info.get('license') or ''
        if none_is_bad and not pkg_license:
            logger.error("Will not mirror {} because it has no license listed")
            continue
        for license in bad_licenses:
            if pkg_license.lower() == license:
                logger.error("Not going to mirror {} because it's license is "
                              "not friendly: {}".format(pkg, license))
                break
        else:
            yield pkg


def download(url, filename, chunk_size=None):
    if chunk_size is None:
        chunk_size = 1024  # 1KB chunks
    logger.info("download_url=%s", url)
    with open(filename, 'wb') as f:
        logger.info("Downloading to %s", filename)
        ret = requests.get(url, stream=True)
        iterator = ret.iter_content(chunk_size)
        for data in iterator:
            f.write(data)


def pseudocode(upstream_channel, target_directory, platform, blacklist=None,
               whitelist=None, verbose=False):
    """

    Parameters
    ----------
    upstream_channel : str
        The anaconda.org channel that you want to mirror locally
        e.g., "anaconda" or "conda-forge"
    target_directory : str
        The path on disk to produce a local mirror of the upstream channel.
        Note that this is the directory that contains the platform
        subdirectories.
    platform : str
        The platform that you want to mirror from
        anaconda.org/<upstream_channel>
        The options are listed in the module level global "DEFAULT_PLATFORMS"
    blacklist : iterable of tuples
        The values of blacklist should be (key, glob) where key is one of the
        keys in the repodata['packages'] dicts and glob is a thing to match
        on.  Note that all comparisons will be laundered through lowercasing.
    whitelist : iterable of tuples
        The values of blacklist should be (key, glob) where key is one of the
        keys in the repodata['packages'] dicts and glob is a thing to match
        on.  Note that all comparisons will be laundered through lowercasing.
    verbose : bool
        Increase chattiness of conda-mirror

    Notes
    -----
    the repodata['packages'] dictionary is formatted like this:

    keys are filenames, e.g.:
    tk-8.5.18-0.tar.bz2

    values are dictionaries, e.g.:
    {'arch': 'x86_64',
     'binstar': {'channel': 'main',
                 'owner_id': '55fc8527d3234d09d4951c71',
                 'package_id': '56380a159c73330b8ae858b8'},
     'build': '0',
     'build_number': 0,
     'date': '2015-03-16',
     # depends is the legacy key for old versions of conda
     'depends': [],
     'license': 'BSD-like',
     'license_family': 'BSD',
     'md5': '902f0fd689a01a835c9e69aefbe58fdd',
     'name': 'tk',
     'platform': 'linux',
     # requires is the new key that specifies the package requirements
     old versions of conda
     'requires': [],
     'size': 1960193,
     'version': '8.5.18'}
    """
    blacklist_packages = {}
    whitelist_packages = {}
    # get repodata from upstream channel
    info, upstream_packages = get_repodata(upstream_channel, platform)
    # match blacklist conditions
    if blacklist:
        logger.debug("blacklist")
        blacklist_packages = match(upstream_packages, blacklist)
        logger.info(pformat(list(blacklist_packages)))
    # match whitelist on blacklist
    if whitelist:
        logger.debug("whitelist")
        whitelist_packages = match(upstream_packages, whitelist)
        logger.info(pformat(list(whitelist_packages)))
    # make final mirror list of not-blacklist + whitelist
    true_blacklist = set(blacklist_packages.keys()) - set(
        whitelist_packages.keys())
    logger.debug('true blacklist')
    logger.debug(pformat(whitelist_packages))
    possible_packages_to_mirror = set(upstream_packages.keys()) - true_blacklist
    logger.debug('possible_packages_to_mirror')
    logger.debug(pformat(possible_packages_to_mirror))

    def list_dir(local_dir):
        contents = os.listdir(local_dir)
        return fnmatch.filter(contents, "*.tar.bz2")

    local_directory = os.path.join(target_directory, platform)
    # validate all packages in directory
    run_conda_index(local_directory)
    logger.debug('removing repodata.json from %s' % local_directory)
    os.remove(os.path.join(local_directory, 'repodata.json'))
    logger.debug('removing repodata.json from %s' % local_directory)
    os.remove(os.path.join(local_directory, 'repodata.json.bz2'))

    # get list of current packages in folder
    local_packages = list_dir(local_directory)
    # if any are not in the final mirror list, remove them
    for package_name in local_packages:
        if package_name in true_blacklist:
            _remove_package(os.path.join(local_directory, package_name))
    # do the set difference of what is local and what is in the final
    # mirror list
    local_packages = list_dir(local_directory)
    to_mirror = possible_packages_to_mirror - set(local_packages)
    logger.debug(to_mirror)
    logger.debug(pformat(to_mirror))
    # mirror all new packages
    for package_name in sorted(to_mirror):
        url = DOWNLOAD_URL.format(
            channel=upstream_channel,
            name=upstream_packages[package_name]['name'],
            version=upstream_packages[package_name]['version'],
            platform=platform,
            file_name=package_name)
        download(url, os.path.join(local_directory, package_name))

    download(REPODATA.format(channel=upstream_channel, platform=platform))
    download(REPODATA.format(channel=upstream_channel, platform=platform) +
             ".bz2")



def main2(upstream_channel, target_directory, platform, blacklist=None, whitelist=None, verbose=False):
    """
    The business logic of conda_mirror.

    Parameters
    ----------
    upstream_channel : str
        The anaconda.org channel that you want to mirror locally
        e.g., "anaconda" or "conda-forge"
    target_directory : str
        The path on disk to produce a local mirror of the upstream channel
    platform : iterable
        The platforms that you want to mirror from anaconda.org/<upstream_channel>
        The defaults are listed in the module level global "DEFAULT_PLATFORMS"
    verbose : bool
        Increase chattiness of conda-mirror
    """
    full_platform_list = copy.copy(platform)
    if 'all' in full_platform_list:
        full_platform_list.remove('all')
        full_platform_list = sorted(set(full_platform_list + DEFAULT_PLATFORMS))

    # make sure the target directory structure is in place
    if not os.path.exists(target_directory):
        logger.info("Making directory: %s", target_directory)
        os.makedirs(target_directory)
    for platform in full_platform_list:
        platform_directory = os.path.join(target_directory, platform)
        if not os.path.exists(platform_directory):
            logger.info("Making directory: %s", target_directory)
            os.makedirs(platform_directory)

    logger.info("Going to look on %s for the following platforms: %s"
                 "", upstream_channel, full_platform_list)


    mirrored_packages = deque()
    # iterate over each platform in the upstream channel
    for platform in full_platform_list:
        upstream_repo_info, upstream_repo_packages = get_repodata(upstream_channel, platform)
        platform_directory = os.path.join(target_directory, platform)
        repodata_file = os.path.join(platform_directory, 'repodata.json')
        if not os.path.exists(repodata_file):
            run_conda_index(platform_directory)
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
            if idx % 5 == 0:
                # intermittently run conda index so that, in case of failure,
                # not all downloads need to be repeated
                run_conda_index(os.path.join(target_directory, platform))

        # also run conda index at the end of the job
        run_conda_index(os.path.join(target_directory, platform))
    logger.info("Done mirroring.")
    logger.info("The packages that were mirrored are:")
    logger.info(pformat(mirrored_packages))

def main(upstream_channel, target_directory, platform, verbose=False):
    """
    The business logic of conda_mirror.

    Parameters
    ----------
    upstream_channel : str
        The anaconda.org channel that you want to mirror locally
        e.g., "anaconda" or "conda-forge"
    target_directory : str
        The path on disk to produce a local mirror of the upstream channel
    platform : iterable
        The platforms that you want to mirror from anaconda.org/<upstream_channel>
        The defaults are listed in the module level global "DEFAULT_PLATFORMS"
    verbose : bool
        Increase chattiness of conda-mirror
    """
    full_platform_list = copy.copy(platform)
    if 'all' in full_platform_list:
        full_platform_list.remove('all')
        full_platform_list = sorted(set(full_platform_list + DEFAULT_PLATFORMS))

    # make sure the target directory structure is in place
    if not os.path.exists(target_directory):
        logger.info("Making directory: {}".format(target_directory))
        os.makedirs(target_directory)
    for platform in full_platform_list:
        dir = os.path.join(target_directory, platform)
        if not os.path.exists(dir):
            logger.info("Making directory: {}".format(target_directory))
            os.makedirs(dir)

    logger.info("Going to look on {} for the following platforms: {}"
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
            logger.info("download_url={}".format(url))
            expected_size = info['size']
            chunk_size = 1024  # 1KB chunks
            expected_iterations = expected_size // chunk_size + 1
            with open(os.path.join(target_directory, platform, package), 'wb') as f:
                logger.info("Downloading {}".format(package))
                ret = requests.get(url, stream=True)
                iterator = ret.iter_content(chunk_size)
                if verbose:
                    iterator = tqdm.tqdm(iterator,
                                         desc=package,
                                         unit="KB",
                                         total=expected_iterations)
                for data in iterator:
                    f.write(data)
            if idx % 5 == 0:
                # intermittently run conda index so that, in case of failure,
                # not all downloads need to be repeated
                run_conda_index(os.path.join(target_directory, platform))

        # also run conda index at the end of the job
        run_conda_index(os.path.join(target_directory, platform))
    logger.info("Done mirroring.")
    logger.info("The packages that were mirrored are:")
    logger.info(pformat(mirrored_packages))


def run_conda_index(target_directory):
    """
    Call out to conda_build.index:update_index

    Parameters
    ----------
    target_directory : str
        The full path to the platform subdirectory inside of the local conda
        channel. The directory at this path should contain a "repodata.json" file
        e.g., /path/to/local/repo/linux-64
    """
    logger.info("Indexing {}".format(target_directory))
    config = Config()
    config.timeout = 1
    try:
        update_index(target_directory, config, could_be_mirror=False)
    except RuntimeError as re:
        # ['Could', 'not', 'extract', 'upstream-mirror/linux-64/numpy-1.7.1-py27_p0.tar.bz2.', 'File', 'probably', 'corrupt.']
        err_msg = str(re).split()
        # find the one that looks like a filename
        fname, = fnmatch.filter(err_msg, "*.tar.bz2*")
        # and drop the trailing '.'
        if fname.endswith('.'):
            fname = fname[:-1]
        logger.info("Caught an exception while trying to index: {}".format(re))
        logger.info("Removing: {}".format(fname))
        _remove_package(fname)
        run_conda_index(target_directory)
    except tarfile.ReadError as re:
        # Find the new packages that don't exist in the repodata
        bad_package, = _find_bad_package(target_directory)
        _remove_package(bad_package)
        run_conda_index(target_directory)


def _find_bad_package(local_platform_directory):
    """
    Find the exact package that is causing a `tarfile.ReadError`

    Parameters
    ----------
    local_platform_directory : str
        Path to one of the platform subdirectories of a local conda channel
        e.g., this is the folder that should contain all of the conda packages
        and a "repodata.json"

    Yields
    ------
    full_pkg_path : str
        The full path to a package that results in `conda_build.index:read_index_tar()`
        raising a tarfile.ReadError
    """
    repodata_fname = os.path.join(local_platform_directory, 'repodata.json')
    repodata = {'info': {}, 'packages': {}}
    if os.path.exists(repodata_fname):
        with open(repodata_fname, 'r') as f:
            repodata = json.load(f)
    repodata_info, repodata_packages = repodata.get('info', {}), repodata.get('packages', {})
    indexed_packages = list(repodata_packages.keys())
    all_packages = fnmatch.filter(os.listdir(local_platform_directory), "*.tar.bz2")
    potentially_bad = set(all_packages).difference(indexed_packages)
    for pkg in potentially_bad:
        full_pkg_path = os.path.join(local_platform_directory, pkg)
        try:
            read_index_tar(full_pkg_path, Config())
        except tarfile.ReadError as re:
            msg = "tarfile.ReadError encountered. Original error: {}".format(re)
            msg += "\nRemoving bad package: {}".format(full_pkg_path)
            logger.error(msg)
            yield full_pkg_path


def _remove_package(pkg_path):
    """
    Log and remove a package.

    Parameters
    ----------
    pkg_path : str
        Path to a conda package that should be removed
    """
    logger.info("Removing: {}".format(pkg_path))
    os.remove(pkg_path)


if __name__ == "__main__":
    cli()
