from __future__ import (unicode_literals, print_function, division,
                        absolute_import)
import argparse
import logging
import yaml
frin .conda_mirror import main

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(message)s')

DEFAULT_BAD_LICENSES = ['agpl', '']
REPODATA = 'https://conda.anaconda.org/{channel}/{platform}/repodata.json'
DEFAULT_PLATFORMS = ['linux-64',
                     'linux-32',
                     'osx-64',
                     'win-64',
                     'win-32']


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
        nargs="+",
        help=("The OS platform(s) to mirror. one or more of: {'all',"
              " 'linux-64', 'linux-32', 'osx-64', 'win-32', 'win-64'}"),
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
        '--blacklist',
        action="+",
        help="k:v pairs to match against to then blacklist from the mirroirng",
        default=[]
    )
    ap.add_argument(
        '--whitelist',
        action="+",
        help=("k:v pairs to match against to then whitelist from the mirroring."
              "Note that whitelist supercedes blacklist"),
        default=[]
    )
    return ap


def cli():
    """
    Collect arguments from sys.argv and invoke the main() function.
    """
    ap = _make_arg_parser()
    args = ap.parse_args()

    if args.config:
        with open(args.config, 'r') as f:
            config = yaml

    main(args.upstream_channel, args.target_directory, args.platform, args.verbose)

