# Change Log

## [0.7.4](https://github.com/maxpoint/conda-mirror/tree/0.7.4)

[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.7.3...0.7.4)

**Implemented enhancements:**

- Add a --dry-run mode [\#39](https://github.com/maxpoint/conda-mirror/issues/39)

**Merged pull requests:**

- ENH: First pass at dry-run [\#59](https://github.com/maxpoint/conda-mirror/pull/59) ([ericdill](https://github.com/ericdill))

## [0.7.3](https://github.com/maxpoint/conda-mirror/tree/0.7.3) (2017-08-07)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.7.2...0.7.3)

**Fixed bugs:**

- keep old packages [\#56](https://github.com/maxpoint/conda-mirror/issues/56)

**Closed issues:**

- Validation errors caused by incomplete tar file [\#57](https://github.com/maxpoint/conda-mirror/issues/57)

**Merged pull requests:**

- Handle EOFError when reading tar files. [\#58](https://github.com/maxpoint/conda-mirror/pull/58) ([dmkent](https://github.com/dmkent))
- Add release script that edits the output of github\_changelog\_generator [\#55](https://github.com/maxpoint/conda-mirror/pull/55) ([ericdill](https://github.com/ericdill))
- DOC: Rerun changelog generator [\#54](https://github.com/maxpoint/conda-mirror/pull/54) ([ericdill](https://github.com/ericdill))

## [0.7.2](https://github.com/maxpoint/conda-mirror/tree/0.7.2) (2017-05-23)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.7.1...0.7.2)

**Merged pull requests:**

- Modify run summary. Configure flake8 on travis [\#53](https://github.com/maxpoint/conda-mirror/pull/53) ([ericdill](https://github.com/ericdill))
- MNT: Template out the message [\#52](https://github.com/maxpoint/conda-mirror/pull/52) ([ericdill](https://github.com/ericdill))
- Raise don't exit when required args aren't present [\#51](https://github.com/maxpoint/conda-mirror/pull/51) ([ericdill](https://github.com/ericdill))

## [0.7.1](https://github.com/maxpoint/conda-mirror/tree/0.7.1) (2017-05-18)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.7.0...0.7.1)

**Merged pull requests:**

- Capture information on downloaded and removed packages [\#50](https://github.com/maxpoint/conda-mirror/pull/50) ([ericdill](https://github.com/ericdill))

## [0.7.0](https://github.com/maxpoint/conda-mirror/tree/0.7.0) (2017-05-11)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.6...0.7.0)

**Closed issues:**

- concurrent package validation [\#43](https://github.com/maxpoint/conda-mirror/issues/43)

**Merged pull requests:**

- Add concurrent package validation [\#48](https://github.com/maxpoint/conda-mirror/pull/48) ([willirath](https://github.com/willirath))
- TST: Fix broken test [\#46](https://github.com/maxpoint/conda-mirror/pull/46) ([ericdill](https://github.com/ericdill))

## [0.6.6](https://github.com/maxpoint/conda-mirror/tree/0.6.6) (2017-03-28)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.5...0.6.6)

**Implemented enhancements:**

- Sort packages for validation [\#34](https://github.com/maxpoint/conda-mirror/issues/34)

**Closed issues:**

- Does not run under py 2.7 [\#42](https://github.com/maxpoint/conda-mirror/issues/42)
- Package license [\#36](https://github.com/maxpoint/conda-mirror/issues/36)
- setup.py home [\#35](https://github.com/maxpoint/conda-mirror/issues/35)

**Merged pull requests:**

- MNT/DOC: Make it clear this is py3 only [\#44](https://github.com/maxpoint/conda-mirror/pull/44) ([ericdill](https://github.com/ericdill))
- Add syntax highlight to the repodata example in README [\#41](https://github.com/maxpoint/conda-mirror/pull/41) ([nicoddemus](https://github.com/nicoddemus))
- Sort the validation output [\#40](https://github.com/maxpoint/conda-mirror/pull/40) ([ericdill](https://github.com/ericdill))
- Fix home to point to MaxPoint org [\#38](https://github.com/maxpoint/conda-mirror/pull/38) ([jakirkham](https://github.com/jakirkham))
- Package standard docs [\#37](https://github.com/maxpoint/conda-mirror/pull/37) ([jakirkham](https://github.com/jakirkham))

## [0.6.5](https://github.com/maxpoint/conda-mirror/tree/0.6.5) (2017-02-23)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.4...0.6.5)

**Closed issues:**

- FileNotFoundError after package is removed for failing size validation [\#31](https://github.com/maxpoint/conda-mirror/issues/31)

**Merged pull requests:**

- Return after removing the package [\#32](https://github.com/maxpoint/conda-mirror/pull/32) ([ericdill](https://github.com/ericdill))

## [0.6.4](https://github.com/maxpoint/conda-mirror/tree/0.6.4) (2017-02-23)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.3...0.6.4)

**Closed issues:**

- TypeError: 'set' object is not subscriptable [\#29](https://github.com/maxpoint/conda-mirror/issues/29)

**Merged pull requests:**

- Fix Type Error [\#30](https://github.com/maxpoint/conda-mirror/pull/30) ([ericdill](https://github.com/ericdill))

## [0.6.3](https://github.com/maxpoint/conda-mirror/tree/0.6.3) (2017-02-15)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.2...0.6.3)

**Closed issues:**

- Mirror pro repo [\#24](https://github.com/maxpoint/conda-mirror/issues/24)

**Merged pull requests:**

- Validate local repo every time you run conda-mirror [\#28](https://github.com/maxpoint/conda-mirror/pull/28) ([ericdill](https://github.com/ericdill))
- Updates to README, Travis, test coverage [\#27](https://github.com/maxpoint/conda-mirror/pull/27) ([opiethehokie](https://github.com/opiethehokie))

## [0.6.2](https://github.com/maxpoint/conda-mirror/tree/0.6.2) (2017-02-07)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.1...0.6.2)

**Merged pull requests:**

- Handle fully qualified channels [\#25](https://github.com/maxpoint/conda-mirror/pull/25) ([ericdill](https://github.com/ericdill))

## [0.6.1](https://github.com/maxpoint/conda-mirror/tree/0.6.1) (2017-01-18)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.6.0...0.6.1)

**Closed issues:**

- Validate that there is enough space to actually perform the mirror [\#19](https://github.com/maxpoint/conda-mirror/issues/19)

**Merged pull requests:**

- MNT: Fix the download url for anaconda/defaults [\#23](https://github.com/maxpoint/conda-mirror/pull/23) ([ericdill](https://github.com/ericdill))
- DOC/MNT: Remove dead code. Update readme. Update changelog [\#22](https://github.com/maxpoint/conda-mirror/pull/22) ([ericdill](https://github.com/ericdill))

## [0.6.0](https://github.com/maxpoint/conda-mirror/tree/0.6.0) (2017-01-10)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.5.1...0.6.0)

**Merged pull requests:**

- Update conda\_mirror.py [\#21](https://github.com/maxpoint/conda-mirror/pull/21) ([jneines](https://github.com/jneines))

## [0.5.1](https://github.com/maxpoint/conda-mirror/tree/0.5.1) (2017-01-03)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.5.0...0.5.1)

**Merged pull requests:**

- download repodata to temp dir first, then move it [\#20](https://github.com/maxpoint/conda-mirror/pull/20) ([ericdill](https://github.com/ericdill))

## [0.5.0](https://github.com/maxpoint/conda-mirror/tree/0.5.0) (2016-12-19)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.6...0.5.0)

**Closed issues:**

- Remove conda\_build as a dependency [\#13](https://github.com/maxpoint/conda-mirror/issues/13)

**Merged pull requests:**

- Write repodata.json.bz2. libconda needs it. [\#18](https://github.com/maxpoint/conda-mirror/pull/18) ([ericdill](https://github.com/ericdill))
- Updated badges to point to new org. [\#17](https://github.com/maxpoint/conda-mirror/pull/17) ([mariusvniekerk](https://github.com/mariusvniekerk))

## [0.4.6](https://github.com/maxpoint/conda-mirror/tree/0.4.6) (2016-12-15)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.5...0.4.6)

## [0.4.5](https://github.com/maxpoint/conda-mirror/tree/0.4.5) (2016-12-15)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.4...0.4.5)

## [0.4.4](https://github.com/maxpoint/conda-mirror/tree/0.4.4) (2016-12-15)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.3...0.4.4)

## [0.4.3](https://github.com/maxpoint/conda-mirror/tree/0.4.3) (2016-12-15)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.2...0.4.3)

## [0.4.2](https://github.com/maxpoint/conda-mirror/tree/0.4.2) (2016-12-13)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.1...0.4.2)

**Merged pull requests:**

- Remove packages that fail their assertion [\#16](https://github.com/maxpoint/conda-mirror/pull/16) ([ericdill](https://github.com/ericdill))

## [0.4.1](https://github.com/maxpoint/conda-mirror/tree/0.4.1) (2016-12-13)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.4.0...0.4.1)

## [0.4.0](https://github.com/maxpoint/conda-mirror/tree/0.4.0) (2016-12-12)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.3.0...0.4.0)

**Merged pull requests:**

- ENH: Rework conda mirror to not use conda-index [\#14](https://github.com/maxpoint/conda-mirror/pull/14) ([ericdill](https://github.com/ericdill))

## [0.3.0](https://github.com/maxpoint/conda-mirror/tree/0.3.0) (2016-12-07)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.2.3...0.3.0)

**Merged pull requests:**

- ENH: Copy index from anaconda [\#12](https://github.com/maxpoint/conda-mirror/pull/12) ([ericdill](https://github.com/ericdill))

## [0.2.3](https://github.com/maxpoint/conda-mirror/tree/0.2.3) (2016-11-09)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.2.2...0.2.3)

**Merged pull requests:**

- Disable tqdm by default [\#11](https://github.com/maxpoint/conda-mirror/pull/11) ([ericdill](https://github.com/ericdill))

## [0.2.2](https://github.com/maxpoint/conda-mirror/tree/0.2.2) (2016-11-09)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.2.1...0.2.2)

**Merged pull requests:**

- Handle when the license is a literal value of None [\#10](https://github.com/maxpoint/conda-mirror/pull/10) ([ericdill](https://github.com/ericdill))

## [0.2.1](https://github.com/maxpoint/conda-mirror/tree/0.2.1) (2016-11-08)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.2.0...0.2.1)

**Merged pull requests:**

- Remove bad packages instead of failing [\#9](https://github.com/maxpoint/conda-mirror/pull/9) ([ericdill](https://github.com/ericdill))

## [0.2.0](https://github.com/maxpoint/conda-mirror/tree/0.2.0) (2016-11-04)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.1.0...0.2.0)

**Merged pull requests:**

- Call conda mirror directly [\#8](https://github.com/maxpoint/conda-mirror/pull/8) ([ericdill](https://github.com/ericdill))

## [0.1.0](https://github.com/maxpoint/conda-mirror/tree/0.1.0) (2016-11-02)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.8...0.1.0)

**Merged pull requests:**

- ENH: Add license checks [\#7](https://github.com/maxpoint/conda-mirror/pull/7) ([ericdill](https://github.com/ericdill))

## [0.0.8](https://github.com/maxpoint/conda-mirror/tree/0.0.8) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.7...0.0.8)

**Merged pull requests:**

- WIP: Intermittently run conda index when mirroring lots of packages [\#6](https://github.com/maxpoint/conda-mirror/pull/6) ([ericdill](https://github.com/ericdill))

## [0.0.7](https://github.com/maxpoint/conda-mirror/tree/0.0.7) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.6...0.0.7)

**Merged pull requests:**

- WIP: entry\_points... [\#5](https://github.com/maxpoint/conda-mirror/pull/5) ([ericdill](https://github.com/ericdill))

## [0.0.6](https://github.com/maxpoint/conda-mirror/tree/0.0.6) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.4...0.0.6)

**Merged pull requests:**

- WIP: add setup.py directive to make conda\_mirror.py a script [\#4](https://github.com/maxpoint/conda-mirror/pull/4) ([ericdill](https://github.com/ericdill))

## [0.0.4](https://github.com/maxpoint/conda-mirror/tree/0.0.4) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.3...0.0.4)

**Merged pull requests:**

- WIP: Update travis yaml [\#3](https://github.com/maxpoint/conda-mirror/pull/3) ([ericdill](https://github.com/ericdill))

## [0.0.3](https://github.com/maxpoint/conda-mirror/tree/0.0.3) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.2...0.0.3)

## [0.0.2](https://github.com/maxpoint/conda-mirror/tree/0.0.2) (2016-10-24)
[Full Changelog](https://github.com/maxpoint/conda-mirror/compare/0.0.1...0.0.2)

## [0.0.1](https://github.com/maxpoint/conda-mirror/tree/0.0.1) (2016-10-20)
**Merged pull requests:**

- test the cli too [\#2](https://github.com/maxpoint/conda-mirror/pull/2) ([ericdill](https://github.com/ericdill))
- Remove unused validator [\#1](https://github.com/maxpoint/conda-mirror/pull/1) ([ericdill](https://github.com/ericdill))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
