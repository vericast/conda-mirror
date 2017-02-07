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

DEFAULT_PLATFORMS = ['linux-64',
                     'linux-32',
                     'osx-64',
                     'win-64',
                     'win-32']


def _maybe_split_channel(channel):
    """Split channel if it is fully qualified. Otherwise default to
    conda.anaconda.org

    Parameters
    ----------
    channel : str
        channel on anaconda, like "conda-forge" or fully qualified channel like
        "https://conda.anacocnda.org/conda-forge"

    Returns
    -------
    download_template : str
        defaults to "https://conda.anaconda.org/{channel}/{platform}/{file_name}"
        The base url will be modified if the `channel` input parameter is
        fully qualified
    channel : str
        The name-only channel. If the channel input param is something like
        "conda-forge", then "conda-forge" will be returned. If the channel
        input param is something like "https://repo.continuum.io/pkgs/free/"
    """
    # strip trailing slashes
    channel = channel.strip('/')

    default_url_base = "https://conda.anaconda.org/"
    url_suffix = "/{channel}/{platform}/{file_name}"
    if '://' not in channel:
        # assume we are being given a channel for anaconda.org
        logger.debug("Assuming %s is an anaconda.org channel", channel)
        url = default_url_base + url_suffix
        return url, channel
    # looks like we are being given a fully qualified channel
    download_base, channel = channel.rsplit('/', 1)
    download_template = download_base + url_suffix
    logger.debug('download_template=%s. channel=%s', download_template, channel)
    return download_template, channel


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
        help=('The target channel to mirror. Can be a channel on anaconda.org '
              'like "conda-forge" or a full qualified channel like '
              '"https://repo.continuum.io/pkgs/free/"'),
    )
    ap.add_argument(
        '--target-directory',
        help='The place where packages should be mirrored to',
    )
    ap.add_argument(
        '--temp-directory',
        help=('Temporary download location for the packages. Defaults to a '
              'randomly selected temporary directory. Note that you might need '
              'to specify a different location if your default temp directory '
              'has less available space than your mirroring target'),
        default=tempfile.gettempdir()
    )
    ap.add_argument(
        '--platform',
        help=("The OS platform(s) to mirror. one of: {'linux-64', 'linux-32',"
              "'osx-64', 'win-32', 'win-64'}"),
    )
    ap.add_argument(
        '-v', '--verbose',
        action="count",
        help=("logging defaults to error/exception only. Takes up to three "
              "'-v' flags. '-v': warning. '-vv': info. '-vvv': debug."),
        default=0,
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
    ap.add_argument(
        '--version',
        action="store_true",
        help="Print version and quit",
        default=False,
    )
    return ap


def _init_logger(verbosity):
    # set up the logger
    global logger
    logger = logging.getLogger('conda_mirror')
    logmap = {0: logging.ERROR,
              1: logging.WARNING,
              2: logging.INFO,
              3: logging.DEBUG}
    loglevel = logmap.get(verbosity, '3')

    # clear all handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.setLevel(loglevel)
    format_string = '%(levelname)s: %(message)s'
    formatter = logging.Formatter(fmt=format_string)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(loglevel)
    stream_handler.setFormatter(fmt=formatter)

    logger.addHandler(stream_handler)

    print("Log level set to %s" % logging.getLevelName(logmap[verbosity]),
          file=sys.stdout)


def cli():
    """
    Collect arguments from sys.argv and invoke the main() function.
    """
    parser = _make_arg_parser()
    args = parser.parse_args()

    _init_logger(args.verbose)
    logger.debug('sys.argv: %s', sys.argv)

    if args.version:
        from . import __version__
        print(__version__)
        return

    for required in ('target_directory', 'platform', 'upstream_channel'):
        if not getattr(args, required):
            logger.error("Missing required argument: %s", required)
            return
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

    main(args.upstream_channel, args.target_directory, args.temp_directory,
         args.platform, blacklist, whitelist)


def _remove_package(pkg_path, reason=None):
    """
    Log and remove a package.

    Parameters
    ----------
    pkg_path : str
        Path to a conda package that should be removed
    """
    if reason is None:
        reason = "No reason given"
    msg = "Removing: %s. Reason: %s"
    logger.warning(msg, pkg_path, reason)
    os.remove(pkg_path)


def _assert_or_remove(left, right, assertion_test, filename):
    try:
        assert left == right
    except AssertionError:
        logger.info("Package validation failed for %s: %s != %s",
                    assertion_test, left, right,
                    exc_info=True)
        _remove_package(filename, reason="Failed %s test" % assertion_test)
        return True
    else:
        logger.debug('%s check passed', assertion_test)


def _get_output(cmd):
    try:
        return subprocess.check_output(cmd).decode().strip().split()[0]
    except subprocess.CalledProcessError as cpe:
        logger.exception(cpe.output.decode())
        return ""
    except Exception:
        msg = "Error in subprocess.check_output. cmd: '%s'"
        logger.exception(msg, ' '.join(cmd))
        return ""


def _validate(filename, md5=None, sha256=None, size=None):
    """Validate the conda package tarfile located at `filename` with any of the
    passed in options `md5`, `sha256` or `size. Also implicitly validate that
    the conda package is a valid tarfile.

    NOTE: Removes packages that fail validation

    Parameters
    ----------
    filename : str
        The path to the file you wish to validate
    md5 : str, optional
        If provided, perform an `md5sum` on `filename` and compare to `md5`
    sha256 : str, optional
        If provided, perform a `sha256sum` on `filename` and compare to `sha256`
    size : int, optional
        if provided, stat the file at `filename` and make sure its size
        matches `size`
    """
    try:
        t = tarfile.open(filename)
        t.extractfile('info/index.json').read().decode('utf-8')
    except tarfile.TarError:
        logger.debug("tarfile error encountered. Original error below.")
        logger.debug(pformat(traceback.format_exc()))
        _remove_package(filename, reason="Tarfile read failure")
        return
    checks = [
        (size, lambda: os.stat(filename).st_size, 'size'),
        (md5, lambda: _get_output(['md5sum', filename]), 'md5'),
        (sha256, lambda: _get_output(['sha256sum', filename]), 'sha256'),
    ]
    for target, validate_function, description in checks:
        if target is not None:
            if _assert_or_remove(target, validate_function(), description,
                                 filename):
                return


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
    url_template, channel = _maybe_split_channel(channel)
    url = url_template.format(channel=channel, platform=platform,
                              file_name='repodata.json')
    json = requests.get(url).json()
    return json.get('info', {}), json.get('packages', {})


def _download(url, target_directory, package_metadata=None, validate=True,
              chunk_size=None):
    """Download `url` to `target_directory`

    Parameters
    ----------
    url : str
        The url to download
    target_directory : str
        The path to a directory where `url` should be downloaded
    package_metadata : dict, optional
        package metadata from repodata.json. Will be used for validation of
        the downloaded package. If None, then validation is skipped
    validate : bool, optional
        True: Perform package validation if `package_metadata` is provided.
        Defaults to True.
    chunk_size : int, optional
        The size in Bytes to chunk the download iterator. Defaults to 1024 (1KB)
    """
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
    """List the conda packages (*.tar.bz2 files) in `local_dir`

    Parameters
    ----------
    local_dir : str
        Some local directory with (hopefully) some conda packages in it

    Returns
    -------
    list
        List of conda packages in `local_dir`
    """
    contents = os.listdir(local_dir)
    return fnmatch.filter(contents, "*.tar.bz2")


def _validate_packages(package_repodata, package_directory):
    """Validate local conda packages.

    NOTE: This is slow.
    NOTE2: This will remove any packages that are in `package_directory` that
           are not in `repodata` and also any packages that fail the package
           validation

    Parameters
    ----------
    package_repodata : dict
        The contents of repodata.json
    package_directory : str
        Path to the local repo that contains conda packages
    """
    # validate local conda packages
    local_packages = _list_conda_packages(package_directory)
    for idx, package in enumerate(local_packages):
        # ensure the packages in this directory are in the upstream
        # repodata.json
        try:
            package_metadata = package_repodata[package]
        except KeyError:
            logger.warning("%s is not in the upstream index. Removing...",
                           package)
            _remove_package(os.path.join(package_directory, package),
                            reason="Package is not in the repodata index")
        else:
            # validate the integrity of the package, the size of the package and
            # its hashes
            logger.info('Validating %s. %s of %s', package, idx,
                        len(local_packages))
            _validate(os.path.join(package_directory, package),
                      md5=package_metadata.get('md5'),
                      sha256=package_metadata.get('sha256'),
                      size=package_metadata.get('size'))


def main(upstream_channel, target_directory, temp_directory, platform,
         blacklist=None, whitelist=None):
    """

    Parameters
    ----------
    upstream_channel : str
        The anaconda.org channel that you want to mirror locally
        e.g., "conda-forge" or
        the defaults channel at "https://repo.continuum.io/pkgs/free"
    target_directory : str
        The path on disk to produce a local mirror of the upstream channel.
        Note that this is the directory that contains the platform
        subdirectories.
    temp_directory : str
        The path on disk to an existing and writable directory to temporarily
        store the packages before moving them to the target_directory to
        apply checks
    platform : str
        The platform that you wish to mirror for. Common options are
        'linux-64', 'osx-64', 'win-64' and 'win-32'. Any platform is valid as
        long as the url resolves.
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

    info, packages = get_repodata(upstream_channel, platform)
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
            matched_packages = _match(packages, blist)
            blacklist_packages.update(matched_packages)
        logger.debug(pformat(sorted(blacklist_packages)))

    # 3. un-blacklist packages that are actually whitelisted
    # match whitelist on blacklist
    if whitelist:
        logger.debug("whitelist")
        whitelist_packages = {}
        for wlist in whitelist:
            matched_packages = _match(packages, wlist)
            whitelist_packages.update(matched_packages)
        logger.debug(pformat(sorted(whitelist_packages)))
    # make final mirror list of not-blacklist + whitelist
    true_blacklist = set(blacklist_packages.keys()) - set(
        whitelist_packages.keys())
    logger.debug('true blacklist')
    logger.debug(pformat(sorted(whitelist_packages)))
    possible_packages_to_mirror = set(packages.keys()) - true_blacklist
    logger.debug('possible_packages_to_mirror')
    logger.debug(pformat(sorted(possible_packages_to_mirror)))

    # 4. remove blacklisted packages
    # get list of current packages in folder
    local_packages = _list_conda_packages(local_directory)
    # if any are not in the final mirror list, remove them
    for package_name in local_packages:
        if package_name in true_blacklist:
            _remove_package(os.path.join(local_directory, package_name),
                            reason="Package is blacklisted")
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
    download_url, channel = _maybe_split_channel(upstream_channel)
    with tempfile.TemporaryDirectory(dir=temp_directory) as download_dir:
        logger.info('downloading to the tempdir %s', download_dir)
        for package_name in sorted(to_mirror):
            url = download_url.format(
                channel=channel,
                platform=platform,
                file_name=package_name)
            _download(url, download_dir, packages)

        # validate all packages in the download directory
        _validate_packages(packages, download_dir)
        logger.debug('contents of %s are %s',
                     download_dir,
                     pformat(os.listdir(download_dir)))

        # 8. Use already downloaded repodata.json contents but prune it of
        # packages we don't want
        repodata_path = os.path.join(download_dir, 'repodata.json')

        repodata = {'info': info, 'packages': packages}
        # compute the packages that we have locally
        packages_we_have = set(local_packages +
                               _list_conda_packages(download_dir))
        # remake the packages dictionary with only the packages we have
        # locally
        repodata['packages'] = {
            name: info for name, info in repodata['packages'].items()
            if name in packages_we_have}
        _write_repodata(download_dir, repodata)

        # move new conda packages
        for f in _list_conda_packages(download_dir):
            old_path = os.path.join(download_dir, f)
            new_path = os.path.join(local_directory, f)
            logger.info("moving %s to %s", old_path, new_path)
            shutil.move(old_path, new_path)

        for f in ('repodata.json', 'repodata.json.bz2'):
            download_path = os.path.join(download_dir, f)
            move_path = os.path.join(local_directory, f)
            shutil.move(download_path, move_path)

    # Also need to make a "noarch" channel or conda gets mad
    noarch_path = os.path.join(target_directory, 'noarch')
    if not os.path.exists(noarch_path):
        os.makedirs(noarch_path, exist_ok=True)
        noarch_repodata = {'info': {}, 'packages': {}}
        _write_repodata(noarch_path, noarch_repodata)


def _write_repodata(package_dir, repodata_dict):
    data = json.dumps(repodata_dict, indent=2, sort_keys=True)
    # strip trailing whitespace
    data = '\n'.join(line.rstrip() for line in data.splitlines())
    # make sure we have newline at the end
    if not data.endswith('\n'):
        data += '\n'

    with open(os.path.join(package_dir,
                           'repodata.json'), 'w') as fo:
        fo.write(data)

    # compress repodata.json into the bz2 format. some conda commands still
    # need it
    bz2_path = os.path.join(package_dir, 'repodata.json.bz2')
    with open(bz2_path, 'wb') as fo:
        fo.write(bz2.compress(data.encode('utf-8')))


if __name__ == "__main__":
    cli()
