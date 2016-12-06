# conda-mirror
[![Build Status](https://travis-ci.org/ericdill/conda-mirror.svg?branch=master)](https://travis-ci.org/ericdill/conda-mirror)
[![codecov](https://codecov.io/gh/ericdill/conda-mirror/branch/master/graph/badge.svg)](https://codecov.io/gh/ericdill/conda-mirror)


## Example Usage

WARNING: Invoking this command will pull ~10GB and take at least an hour
```bash
$ conda-mirror --upstream-channel conda-forge --target-directory local_mirror --platform linux-64
```

## CLI
```
$ conda-mirror -h
['/home/edill/miniconda/bin/conda-mirror', '-h']
usage: conda-mirror [-h] --upstream-channel UPSTREAM_CHANNEL
                    --target-directory TARGET_DIRECTORY --platform PLATFORM
                    [-v] [--config CONFIG] [--pdb]

CLI interface for conda-mirror.py

optional arguments:
  -h, --help            show this help message and exit
  --upstream-channel UPSTREAM_CHANNEL
                        The anaconda channel to mirror
  --target-directory TARGET_DIRECTORY
                        The place where packages should be mirrored to
  --platform PLATFORM   The OS platform(s) to mirror. one of: {'linux-64',
                        'linux-32','osx-64', 'win-32', 'win-64'}
  -v, --verbose         This basically turns on tqdm progress bars for
                        downloads
  --config CONFIG       Path to the yaml config file
  --pdb                 Enable PDB debugging on exception
```

## Testing

Note: Will install packages from pip

```
$ pip install -r test-requirements.txt
Requirement already satisfied: pytest in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 1))
Requirement already satisfied: coverage in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 2))
Requirement already satisfied: pytest-ordering in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 3))
Requirement already satisfied: py>=1.4.29 in /home/edill/miniconda/lib/python3.5/site-packages (from pytest->-r test-requirements.txt (line 1))

$ coverage run run_tests.py -x
sys.argv=['run_tests.py', '-x']
================================================================================== test session starts ===================================================================================
platform linux -- Python 3.5.2, pytest-3.0.4, py-1.4.31, pluggy-0.4.0 -- /home/edill/miniconda/bin/python
cachedir: .cache
rootdir: /home/edill/dev/maxpoint/conda-mirror, inifile:
plugins: xonsh-0.4.7, ordering-0.4
collected 4 items

test/test_conda_mirror.py::test_match PASSED
test/test_conda_mirror.py::test_cli[anaconda-linux-64] PASSED
test/test_conda_mirror.py::test_cli[conda-forge-linux-64] PASSED
test/test_conda_mirror.py::test_handling_bad_package PASSED

=============================================================================== 4 passed in 15.66 seconds ================================================================================

$ coverage report -m
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
conda_mirror/__init__.py           3      0   100%
conda_mirror/conda_mirror.py     169     15    91%   154, 160, 289-290, 333-342, 370-371, 401
------------------------------------------------------------
TOTAL                            172     15    91%
```
