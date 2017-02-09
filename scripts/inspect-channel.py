from conda_mirror import conda_mirror as cm
from pprint import pprint
from argparse import ArgumentParser
from os.path import join
import json
import os
from multiprocessing import Pool
import sys
import time

cm._init_logger(3)

METADATA="No metadata found"
PACKAGE_VALIDATION="Validation failed"

def validate(pkg_tuple):
    package_path, package_metadata, idx, total = pkg_tuple
#    print('%s of %s. validating %s' % (idx, total, package_path))
    if package_metadata is None:
        return package_path, METADATA, ""
    ret = cm._validate(package_path,
                       md5=package_metadata.get('md5'),
                       sha256=package_metadata.get('sha256'),
                       size=package_metadata.get('size'))
    if ret is not None:
        return package_path, PACKAGE_VALIDATION, ret


def cli():
    ap = ArgumentParser()
    ap.add_argument(
        'pkgs_dir',
        action='store',
        help="The path to the directory that you are interested in"
    )
    ap.add_argument(
        'num_workers',
        action='store',
        help="The number of parallel processes to spin up"
    )
    ap.add_argument(
        '--cron',
        action="store_true",
        help="Disable print calls that don't do so well in logs",
        default=False
    )
    args = ap.parse_args()

    with open(join(args.pkgs_dir, 'repodata.json'), 'r') as f:
        repodata = json.load(f)

    conda_packages = cm._list_conda_packages(args.pkgs_dir)
    pkg_iter = ((join(args.pkgs_dir, pkg), repodata['packages'].get(pkg), idx, len(conda_packages))
                for idx, pkg in enumerate(conda_packages))
    start = time.time()
    need_attention = []
    print_every = len(conda_packages) / 100
    if print_every < 100:
        print_every = 100
    with Pool(int(args.num_workers)) as p:
        for i, ret in enumerate(p.imap_unordered(validate, pkg_iter)):
            elapsed = int(time.time()) - int(start) or 1
            pkgs_per_sec = int(i / elapsed) or 1
            eta = int((len(conda_packages) - i) / pkgs_per_sec)
            msg = ('{0}/{1}   {2}s elapsed   {3} processed/sec   {4}s remaining'.format(
                i, len(conda_packages), elapsed, pkgs_per_sec, eta))
            if not args.cron:
                sys.stderr.write('\r%s' % msg)
            else:
                if i % print_every  == 0:
                    print('%s\n'% msg)
            if ret is not None:
                need_attention.append(ret)
    print('\n%s packages need attention' % len(need_attention))
    for package_path, problem_type, info in need_attention:
        if problem_type == METADATA:
            print("Removing %s because it is not in the local "
                  "repodata.json" % (package_path), file=sys.stderr)
            os.remove(package_path)
        elif problem_type == PACKAGE_VALIDATION:
            print("Removing %s because it failed package validation with this "
                  "reason: %s" % (package_path, info), file=sys.stderr)
            os.remove(package_path)
            del repodata['packages'][os.path.basename(package_path)]
            # Update the repodata immediately
            cm._write_repodata(os.path.dirname(package_path), repodata)

    print("All packages that require attention")
    pprint(need_attention)


if __name__ == "__main__":
    cli()

