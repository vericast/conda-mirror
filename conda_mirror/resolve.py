"""Relevant code for figuring out which packages need to be mirrored"""
from __future__ import (unicode_literals, print_function, division,
                        absolute_import)

from glob import fnmatch

def match(all_packages, kv_iter):
    """

    Parameters
    ----------
    all_packages : iterable
        Iterable of package metadata dicts from repodata.json
    kv_iter : iterable of kv pairs
        Iterable of (key, glob_value)

    Returns
    -------
    matched : dict
        Iterable of package metadata dicts which match the `target_packages`
        (key, glob_value) tuples
    """
    matched = dict()
    for pkg_name, pkg_info in all_packages.items():
        for key, glob in target_packages.items():
            # normalize the strings so that comparisons are easier
            name = str(pkg_info.get(key, '')).lower()
            pattern = glob.lower()
            if fnmatch.fnmatch(name, pattern):
                matched.update({pkg_name: pkg_info})
    return matched
