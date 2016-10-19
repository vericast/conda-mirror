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