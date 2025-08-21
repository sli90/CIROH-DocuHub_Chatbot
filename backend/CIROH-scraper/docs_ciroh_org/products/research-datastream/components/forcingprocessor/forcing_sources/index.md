# Forcing Sources

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/ngen-datastream/blob/main/forcingprocessor/FORCING_SOURCES.md](https://github.com/CIROH-UA/ngen-datastream/blob/main/forcingprocessor/FORCING_SOURCES.md).

This forcings processor uses [nwmurl](https://github.com/CIROH-UA/nwmurl) to generate forcings file names from different data sources (accessed via `urlbaseinput`). Which means this processor must handle files stored in both the National Water Model v3 operational forcings in amazon Google cloud storage and v2 retrospective forcings in amazon s3 object storage, just to name a couple data sources. Not all of these data sources have been implemented as of summer 2024. A check below indicates that this forcings processor knows how to read in data from the source.

Operational forcings sources

- 1: "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/" ✅
- 2: "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/post-processed/WMS/"
- 3: "https://storage.googleapis.com/national-water-model/" ✅
- 4: "https://storage.cloud.google.com/national-water-model/" ✅
- 5: "gs://national-water-model/" ✅
- 6: "gcs://national-water-model/" ✅
- 7: "https://noaa-nwm-pds.s3.amazonaws.com/" ✅
- 8: "s3://noaa-nwm-pds/" ✅
- 9: "https://ciroh-nwm-zarr-copy.s3.amazonaws.com/national-water-model/"

Retrospective forcings sources

- 1: "https://noaa-nwm-retrospective-2-1-pds.s3.amazonaws.com/" ✅
- 2: "s3://noaa-nwm-retrospective-2-1-pds/model_output/" ✅
- 3: "https://ciroh-nwm-zarr-retrospective-data-copy.s3.amazonaws.com/noaa-nwm-retrospective-2-1-zarr-pds/"
- 4: "https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/CONUS/netcdf/" (✅, [issue 52](https://github.com/CIROH-UA/nwmurl/issues/52))