"""Relevant code for figuring out which packages need to be mirrored"""

from glob import fnmatch

def match(all_packages, target_packages):
    """

    Parameters
    ----------
    all_packages : iterable
        Iterable of package metadata dicts from repodata.json
    target_packages : iterable of tuples
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
            if fnmatch.fnmatch(str(pkg_info.get(key, '')), glob):
                matched.update({pkg_name: pkg_info})
    return matched


if __name__ == "__main__":
    from conda_mirror import get_repodata
    repodata_info, repodata_packages = get_repodata('anaconda', 'linux-64')
    matched = match(repodata_packages, {'name': 'jupyter'})
    assert len(set([v['name'] for v in matched.values()])) == 1
    print(matched)