# changes in conda-mirror

## 0.4.2
- Remove packages that fail their validation checks

## 0.4.1
- Removed conda-build as a dependency in setup.py

## 0.4.0
- Removed use of conda_index to find bad packages
- New workflow:
    - Download packages to temp directory
    - Validate packages in the temp directory
    - Remove packages that fail validation
    - Move all packages from temp dir to the local mirror
    - move repodata.json and repodata.json.bz2 after moving in new packages
