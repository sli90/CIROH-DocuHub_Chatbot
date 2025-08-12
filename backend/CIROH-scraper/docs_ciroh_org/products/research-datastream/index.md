# Research DataStream

[Skip to main content](https://docs.ciroh.org/docs/products/research-datastream/#__docusaurus_skipToContent_fallback)

info

The Research DataStream forcing files and associated metadata are available through our AWS S3 Explorer. You can browse and access these regularly updated resources at [datastream.ciroh.org/index.html](http://datastream.ciroh.org/index.html). In addition to NextGen forcings, daily NextGen simulation outputs via Datastream will soon be available.

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/ngen-datastream/blob/main/README.md](https://github.com/CIROH-UA/ngen-datastream/blob/main/README.md).

The Research DataStream is an array of daily [NextGen](https://github.com/NOAA-OWP/ngen)-based hydrolgic simulations in the AWS cloud. An exciting aspect of the Research DataStream is the NextGen configuration is [open-sourced](https://github.com/CIROH-UA/ngen-datastream/tree/main/research_datastream/configuration) and [community editable](https://github.com/CIROH-UA/ngen-datastream/blob/main/research_datastream/CONTRIBUTE.md), which allows any member of the hydrologic community to contribute to improving streamflow predictions. By making the NextGen forcings, outputs, and configuration publicly available, it is now possible to leverage regional expertise and incrementally improve streamflow predictions configured with the NextGen Framework.
See the Research DataStream related documentation:

- **Find daily output data at:** [https://datastream.ciroh.org/index.html](https://datastream.ciroh.org/index.html)
- **Make improvements to NextGen configuration:**
Find out how you can contribute [here](https://github.com/CIROH-UA/ngen-datastream/blob/main/research_datastream/CONTRIBUTE.md)!
- **Current status and configuration:** Read [here](https://github.com/CIROH-UA/ngen-datastream/blob/main/research_datastream/STATUS_AND_METADATA.md)!
- **Infrastructure as Code:** See the template AWS architecture [here](https://github.com/CIROH-UA/ngen-datastream/blob/main/research_datastream/terraform/ARCHITECTURE.md), which users can deploy within their own AWS account to issue and manage AWS server-based jobs.

  - The actual research datastream deployment, which builds upon the template AWS infra, exists [here](https://github.com/CIROH-UA/ngen-datastream/tree/main/research_datastream/terraform_community) and is available for reference only.

# DataStreamCLI

The software backend of the Research DataStream is DataStreamCLI, which is a stand alone tool that automates the process of collecting and formatting input data for NextGen, orchestrating the NextGen run through NextGen In a Box (NGIAB), and handling outputs. This software allows users to run NextGen in an efficient, _relatively_ painless, and reproducible fashion while providing flexibility and integrations like hfsubset, NextGen In A Box, and TEEHR.

[![datastream](https://github.com/CIROH-UA/ngen-datastream/raw/main/docs/images/datastreamcli.jpg)](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/images/datastreamcli.jpg)

## Getting Started

- **Installation:** Follow the [Installation Guide](https://github.com/CIROH-UA/ngen-datastream/blob/main/INSTALL.md) to prepare your environment for `DataStreamCLI`.
- **Guide:** Start by running the [DataStreamCLI guide](https://github.com/CIROH-UA/ngen-datastream/blob/main/scripts/datastream_guide)! It is an interactive script that will provide a tour of the repo as well as help you form a command with `DataStreamCLI`.
- **Status:** Check the [status page](https://github.com/CIROH-UA/ngen-datastream/blob/main/STATUS.md) for availability of tooling/integrations.
- **Docs**: Make sure to review the [documentation](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/) for

  - Available [NextGen models](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/NGEN_MODELS.md) and automated BMI configuration generation
  - [Datastream options](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/DATASTREAM_OPTIONS.md)
  - Input and output [directory structure](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/STANDARD_DIRECTORIES.md)
  - A [usage guide](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/USAGE.md) for executing `DataStreamCLI` effectively
  - A step-by-step [breakdown](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/BREAKDOWN.md) of `DataStreamCLI`'s internal workflow
  - An explanation of the [Research DataStream](https://github.com/CIROH-UA/ngen-datastream/blob/main/research_datastream/README.md)

## Run DataStreamCLI

This example will execute a 24 hour NextGen simulation over the Palisade, Colorado watershed with CFE, SLOTH, PET, NOM, and t-route configuration distributed over 4 processes. The forcings used are the National Water Model v3 Retrospective.

First, obtain a hydrofabric file for the gage you wish to model. There are several tooling options to use to obtain a geopackage. One of which, [hfsubset](https://github.com/lynker-spatial/hfsubsetCLI), is maintained by Lynker and is integrated in DataStreamCLI.

For Palisade, Colorado:

```
hfsubset -w medium_range \
          -s nextgen \
          -v 2.1.1 \
          -l divides,flowlines,network,nexus,forcing-weights,flowpath-attributes,model-attributes \
          -o palisade.gpkg \
          -t hl "Gages-09106150"

```

Then feed the hydrofabric file to DataStreamCLI along with a few cli args to define the time domain and NextGen configuration

```
./scripts/datastream -s 202006200100 \
                    -e 202006210000 \
                    -C NWM_RETRO_V3 \
                    -d $(pwd)/data/datastream_test \
                    -g $(pwd)/palisade.gpkg \
                    -R $(pwd)/configs/ngen/realization_sloth_nom_cfe_pet_troute.json \
                    -n 4

```

And that's it! Outputs will exist at `$(pwd)/data/datastream_test/ngen-run/outputs`

## License

The entirety of `ngen-datastream` is distributed under [GNU General Public License v3.0 or later](https://github.com/CIROH-UA/ngen-datastream/blob/main/LICENSE.md)