# Changelog

## 0.1.3 - 2024-11-27

### Added
* ARM build and `latest` tag in `docker_publish.yaml`

### Changed
* Checks if USGS are returned from the hydrofabric and raises an error if not.


## 0.1.2 - 2024-11-14

### Added
* None

### Changed
* Installs TEEHR from main instead of v0.4-beta

* Updated requirements.txt


## 0.1.1 - 2024-11-13

### Added
* Added a check for a table only present in version 2.2 of the hydrofabric

* Fetch the gages from the hf depending on the version

* Added a check for the troute output format

* Renamed the netcdf time variable to match the field mappings used by the csv output

* Also added UV to the build dockerfile to speed it up a bit (unrelated to other changes and can be removed if needed)

* Added Root Mean Standard Deviation Ratio metric (RSR)

### Changed
* None


## 0.1.0 - 2024-10-15

### Added
* Initial testing of coupling NGIAB with TEEHR

### Changed
* None