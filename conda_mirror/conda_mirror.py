from __future__ import (unicode_literals, print_function, division,
                        absolute_import)

import argparse
import json
import logging
import os
import pdb
import sys
import tarfile
from glob import fnmatch
from pprint import pformat

import requests
import yaml
from conda_build.config import Config
from conda_build.index import update_index, read_index_tar


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
    key_glob_dict = {key.lower(): glob.lower()
                     for key, glob
                     in key_glob_dict.items()}
    for pkg_name, pkg_info in all_packages.items():
        matched_all = []
        # normalize the strings so that comparisons are easier
        for key, pattern in key_glob_dict.items():
            name = str(pkg_info.get(key, '')).lower()
            if fnmatch.fnmatch(name, pattern):
                matched_all.append(True)
            else:
                matched_all.append(False)
        if all(matched_all):
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
    loglevel = logging.INFO
    global logger
    logger = logging.getLogger('conda_mirror')
    logger.setLevel(loglevel)

    print(sys.argv)
    parser = _make_arg_parser()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)


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
    whitelist = config_dict.get('whitelist')

    main(args.upstream_channel, args.target_directory, args.platform,
         blacklist, whitelist)


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


def main(upstream_channel, target_directory, platform, blacklist=None,
         whitelist=None):
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
        blacklist_packages = {}
        for blist in blacklist:
            matched_packages = match(upstream_packages, blist)
            blacklist_packages.update(matched_packages)
        logger.debug(pformat(list(blacklist_packages)))
    # match whitelist on blacklist
    if whitelist:
        logger.debug("whitelist")
        whitelist_packages = {}
        for wlist in whitelist:
            matched_packages = match(upstream_packages, wlist)
            whitelist_packages.update(matched_packages)
        logger.debug(pformat(list(whitelist_packages)))
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
    logger.info('to_mirror')
    logger.info(pformat(to_mirror))
    # mirror all new packages
    for package_name in sorted(to_mirror):
        url = DOWNLOAD_URL.format(
            channel=upstream_channel,
            name=upstream_packages[package_name]['name'],
            version=upstream_packages[package_name]['version'],
            platform=platform,
            file_name=package_name)
        download(url, os.path.join(local_directory, package_name))

    download(filename=os.path.join(local_directory, 'repodata.json'),
             url=REPODATA.format(channel=upstream_channel,
                                 platform=platform))
    download(filename=os.path.join(local_directory, 'repodata.json.bz2'),
             url=REPODATA.format(channel=upstream_channel,
                                 platform=platform)+".bz2")


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
