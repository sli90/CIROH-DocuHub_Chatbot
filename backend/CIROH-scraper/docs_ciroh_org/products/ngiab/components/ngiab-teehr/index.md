# NGIAB TEEHR Integration

[Skip to main content](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-teehr/#__docusaurus_skipToContent_fallback)

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/ngiab-teehr/blob/main/README.md](https://github.com/CIROH-UA/ngiab-teehr/blob/main/README.md).

A repository for coupling [TEEHR](https://rtiinternational.github.io/teehr/) with [Nextgen-In-A-Box (NGIAB)](https://github.com/jameshalgren/NGIAB-CloudInfra) simulation output.

Warning: This code is experimental!

The `example_guide.sh` script demonstrates running a TEEHR evaluation (see `scripts/teehr_ngen.py`) on NGIAB output.

### To build and push the TEEHR image to the AWI CIROH registry

Customize the metrics calculated by TEEHR or any other code related to the workflow:

1. Create a branch off of main
2. Make your edits to `scripts/teehr_ngen.py` and/or `scripts/utils.py`
3. Update the `Changelog` so that your changes can be associated with a tag
4. Submit and PR and merge
5. Then checkout main and pull the new changes, and push your tag:

```
git checkout main
git pull
git tag -a v0.x.x -m "version 0.x.x"
git push origin v0.x.x
```

This will trigger a `github action` to build and push the image with your tag, and the `latest` tag, to the AWI CIROH registry.

To build and push locally:

```
docker build -t awiciroh/ngiab-teehr:<tag name> .
docker push awiciroh/ngiab-teehr:<tag name>

```

Now you can specify the image tag in the guide.sh script.

|  |  |
| --- | --- |
| [![alt text](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67)](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67) | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003). |