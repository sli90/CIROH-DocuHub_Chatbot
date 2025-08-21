# Installation

> **NOTE**
>
> Below content is rendered from [https://github.com/CIROH-UA/ngen-datastream/blob/main/INSTALL.md](https://github.com/CIROH-UA/ngen-datastream/blob/main/INSTALL.md).

To run ngen-datastream, clone this repository onto a linux machine and make sure the packages below are installed.

## Required Packages

- docker
- git
- pigz
- tar
- awscli (if using S3* options)
- [hfsubset](https://github.com/lynker-spatial/hfsubsetCLI)
  - If using SUBSET options, make sure to move the hfsubset binary into /usr/bin