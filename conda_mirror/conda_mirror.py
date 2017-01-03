from __future__ import (unicode_literals, print_function, division,
                        absolute_import)

import argparse
import logging
import os
import pdb
import shutil
import subprocess
import sys
import json
import tarfile
import tempfile
import traceback
from glob import fnmatch
from pprint import pformat
import bz2
import requests
import yaml


logger = None


DEFAULT_BAD_LICENSES = ['agpl', '']

DOWNLOAD_URL="https://anaconda.org/{channel}/{name}/{version}/download/{platform}/{file_name}"
REPODATA = 'https://conda.anaconda.org/{channel}/{platform}/repodata.json'
DEFAULT_PLATFORMS = ['linux-64',
                     'linux-32',
                     'osx-64',
                     'win-64',
                     'win-32']


def _match(all_packages, key_glob_dict):
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
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.setLevel(loglevel)
    format_string = '%(levelname)s: %(message)s'
    formatter = logging.Formatter(fmt=format_string)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(loglevel)
    stream_handler.setFormatter(fmt=formatter)

    logger.addHandler(stream_handler)


    print(sys.argv)
    parser = _make_arg_parser()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.DEBUG)


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


def _validate(filename, md5=None, sha256=None, size=None):
    try:
        t = tarfile.open(filename)
        index_json = t.extractfile('info/index.json').read().decode('utf-8')
    except tarfile.TarError:
        logger.debug("tarfile error encountered. Original error below.")
        logger.debug(pformat(traceback.format_exc()))
        logger.warning("Removing package: %s", filename)
        _remove_package(filename)
        return

    def _get_output(cmd):
        try:
            return subprocess.check_output(cmd).decode().strip().split()[0]
        except subprocess.CalledProcessError as cpe:
            logger.error(cpe.output.decode())
            return ""

    def _assert_or_remove(left, right, assertion_test):
        try:
            assert left == right
        except AssertionError:
            logger.error("Package validation failed for %s", assertion_test)
            logger.error("%s != %s", left, right)
            logger.error(pformat(traceback.format_exc()))
            logger.error("Removing package %s", filename)
            _remove_package(filename)
            return True
        else:
            logger.debug('%s check passed', assertion_test)

    checks = [
        (size, lambda: os.stat(filename).st_size, 'size'),
        (md5, lambda: _get_output(['md5sum', filename]), 'md5'),
        (sha256, lambda: _get_output(['sha256sum', filename]), 'sha256'),
    ]
    for target, function, description in checks:
        if target is not None:
            if _assert_or_remove(target, function(), description):
                return


def _download(url, target_directory, package_metadata=None, validate=True,
              chunk_size=None):
    if chunk_size is None:
        chunk_size = 1024  # 1KB chunks
    logger.info("download_url=%s", url)
    # create a temporary file
    target_filename = url.split('/')[-1]
    download_filename = os.path.join(target_directory, target_filename)
    logger.debug('downloading to %s', download_filename)
    with open(download_filename, 'w+b') as tf:
        ret = requests.get(url, stream=True)
        for data in ret.iter_content(chunk_size):
            tf.write(data)
    # do some validations
    if validate and package_metadata:
        _validate(download_filename,
                  md5=package_metadata.get('md5'),
                  sha256=package_metadata.get('sha256'),
                  size=package_metadata.get('size'))
    else:
        logger.info("Not validating %s because validate is %s and "
                     "package_metadata is %s", download_filename, validate,
                     package_metadata)


def _list_conda_packages(local_dir):
    contents = os.listdir(local_dir)
    return fnmatch.filter(contents, "*.tar.bz2")


def _validate_packages(repodata, package_directory):
    # validate local conda packages
    local_packages = _list_conda_packages(package_directory)
    for package in local_packages:
        # ensure the packages in this directory are in the upstream
        # repodata.json
        try:
            info = repodata[package]
        except KeyError:
            logger.warning("%s is not in the upstream index. Removing...",
                            package)
            _remove_package(os.path.join(package_directory, package))
        else:
            # validate the integrity of the package, the size of the package and
            # its hashes
            logger.info('Validating %s', package)
            _validate(os.path.join(package_directory, package),
                      md5=info.get('md5'), sha256=info.get('sha256'),
                      size=info.get('size'))


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
    # Steps:
    # 1. figure out blacklisted packages
    # 2. un-blacklist packages that are actually whitelisted
    # 3. remove blacklisted packages
    # 4. figure out final list of packages to mirror
    # 5. mirror new packages to temp dir
    # 6. validate new packages
    # 7. copy new packages to repo directory
    # 8. download repodata.json and repodata.json.bz2
    # 9. copy new repodata.json and repodata.json.bz2 into the repo

    # Implementation:
    if not os.path.exists(os.path.join(target_directory, platform)):
        os.makedirs(os.path.join(target_directory, platform))
    info, repodata = get_repodata(upstream_channel, platform)
    local_directory = os.path.join(target_directory, platform)

    # 1. validate local repo
    # validating all packages is taking many hours.
    # _validate_packages(repodata=repodata,
    #                    package_directory=local_directory)

    # 2. figure out blacklisted packages
    blacklist_packages = {}
    whitelist_packages = {}
    # match blacklist conditions
    if blacklist:
        logger.debug("blacklist")
        blacklist_packages = {}
        for blist in blacklist:
            matched_packages = _match(repodata, blist)
            blacklist_packages.update(matched_packages)
        logger.debug(pformat(sorted(blacklist_packages)))

    # 3. un-blacklist packages that are actually whitelisted
    # match whitelist on blacklist
    if whitelist:
        logger.debug("whitelist")
        whitelist_packages = {}
        for wlist in whitelist:
            matched_packages = _match(repodata, wlist)
            whitelist_packages.update(matched_packages)
        logger.debug(pformat(sorted(whitelist_packages)))
    # make final mirror list of not-blacklist + whitelist
    true_blacklist = set(blacklist_packages.keys()) - set(
        whitelist_packages.keys())
    logger.debug('true blacklist')
    logger.debug(pformat(sorted(whitelist_packages)))
    possible_packages_to_mirror = set(repodata.keys()) - true_blacklist
    logger.debug('possible_packages_to_mirror')
    logger.debug(pformat(sorted(possible_packages_to_mirror)))

    # 4. remove blacklisted packages
    # get list of current packages in folder
    local_packages = _list_conda_packages(local_directory)
    # if any are not in the final mirror list, remove them
    for package_name in local_packages:
        if package_name in true_blacklist:
            _remove_package(os.path.join(local_directory, package_name))
    # 5. figure out final list of packages to mirror
    # do the set difference of what is local and what is in the final
    # mirror list
    local_packages = _list_conda_packages(local_directory)
    to_mirror = possible_packages_to_mirror - set(local_packages)
    logger.info('to_mirror')
    logger.info(pformat(sorted(to_mirror)))

    # 6. for each download:
    # a. download to temp file
    # b. validate contents of temp file
    # c. move to local repo
    # mirror all new packages
    with tempfile.TemporaryDirectory() as download_dir:
        logger.info('downloading to the tempdir %s', download_dir)
        for package_name in sorted(to_mirror):
            url = DOWNLOAD_URL.format(
                channel=upstream_channel,
                name=repodata[package_name]['name'],
                version=repodata[package_name]['version'],
                platform=platform,
                file_name=package_name)
            _download(url, download_dir, repodata)

        # validate all packages in the download directory
        _validate_packages(repodata, download_dir)
        logger.debug('contents of %s are %s',
                      download_dir,
                      pformat(os.listdir(download_dir)))

        # 8. download repodata.json and repodata.json.bz2
        url = REPODATA.format(channel=upstream_channel, platform=platform)
        _download(url, download_dir, validate=False)

        # prune the repodata.json file of packages we don't want
        repodata_path = os.path.join(download_dir, 'repodata.json')

        # load the json into a python dictionary
        with open(repodata_path, 'r') as f:
            rd = json.load(f)
        # compute the packages that we have locally
        packages_we_have = set(local_packages +
                               _list_conda_packages(download_dir))
        # remake the packages dictionary with only the packages we have
        # locally
        rd['packages'] = {name: info for name, info in
                          rd['packages'].items()
                          if name in packages_we_have}
        # move new conda packages
        for f in _list_conda_packages(download_dir):
            old_path = os.path.join(download_dir, f)
            new_path = os.path.join(local_directory, f)
            logger.info("moving %s to %s", old_path, new_path)
            shutil.move(old_path, new_path)

        data = json.dumps(rd, indent=2, sort_keys=True)
        # strip trailing whitespace
        data = '\n'.join(line.rstrip() for line in data.splitlines())
        # make sure we have newline at the end
        if not data.endswith('\n'):
            data += '\n'

        with open(os.path.join(download_dir,
                               'repodata.json'), 'w') as fo:
            fo.write(data)
        with open(os.path.join(download_dir,
                               'repodata.json.bz2'), 'wb') as fo:
            fo.write(bz2.compress(data.encode('utf-8')))
        
        for f in ('repodata.json', 'repodata.json.bz2'):
            download_path = os.path.join(download_dir, f)
            move_path = os.path.join(local_directory, f)
            shutil.move(download_path, move_path)



if __name__ == "__main__":
    cli()
