# conda-mirror

## Usage

WARNING: Invoking this command will pull ~10GB and take at least an hour
```bash
$ python conda_mirror.py --upstream-channel conda-forge --target-directory local_mirror --platform linux-64
```

```
$ python conda_mirror.py  -h
usage: conda_mirror.py [-h] [--upstream-channel UPSTREAM_CHANNEL]
                       [--target-directory TARGET_DIRECTORY]
                       [--platform PLATFORM [PLATFORM ...]]

CLI interface for conda-mirror.py

optional arguments:
  -h, --help            show this help message and exit
  --upstream-channel UPSTREAM_CHANNEL
                        The anaconda channel to mirror
  --target-directory TARGET_DIRECTORY
                        The place where packages should be mirrored to
  --platform PLATFORM [PLATFORM ...]
                        The OS platform(s) to mirror. one or more of: {'all',
                        'linux-64', 'linux-32', 'osx-64', 'win-32', 'win-64'}

```

## Testing

Note: Will install packages from pip

```
$ ./run_tests
Requirement already satisfied (use --upgrade to upgrade): pytest in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 1))
Requirement already satisfied (use --upgrade to upgrade): requests in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 2))
Requirement already satisfied (use --upgrade to upgrade): requests-mock in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 3))
Requirement already satisfied (use --upgrade to upgrade): tqdm in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 4))
Requirement already satisfied (use --upgrade to upgrade): coverage in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 5))
Requirement already satisfied (use --upgrade to upgrade): pytest-ordering in /home/eric/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 6))
Requirement already satisfied (use --upgrade to upgrade): py>=1.4.29 in /home/eric/miniconda/lib/python3.5/site-packages (from pytest->-r test-requirements.txt (line 1))
Requirement already satisfied (use --upgrade to upgrade): six in /home/eric/miniconda/lib/python3.5/site-packages (from requests-mock->-r test-requirements.txt (line 3))
================================================================================================================================== test session starts ===================================================================================================================================
platform linux -- Python 3.5.2, pytest-3.0.3, py-1.4.31, pluggy-0.4.0 -- /home/eric/miniconda/bin/python
cachedir: .cache
rootdir: /home/eric/dev/maxpoint/maxforge/conda-mirror, inifile:
plugins: ordering-0.4, xonsh-0.4.7
collected 6 items

test_conda_mirror.py::test_ensure_local_repo SKIPPED
test_conda_mirror.py::test_get_repodata[linux-64] PASSED
test_conda_mirror.py::test_get_repodata[linux-32] PASSED
test_conda_mirror.py::test_get_repodata[osx-64] PASSED
test_conda_mirror.py::test_get_repodata[win-64] PASSED
test_conda_mirror.py::test_get_repodata[win-32] PASSED
================================================================================================================================ short test summary info =================================================================================================================================
SKIP [1] /home/eric/dev/maxpoint/maxforge/conda-mirror/test_conda_mirror.py:21: Don't need to regenerate repo. If you want to force regeneration, remove the 'local-repo' dir

========================================================================================================================== 5 passed, 1 skipped in 0.26 seconds ===========================================================================================================================
Name              Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------
conda_mirror.py      67     48     20      1    23%   42-60, 64-69, 89, 93-141, 145-149, 144->145

```
