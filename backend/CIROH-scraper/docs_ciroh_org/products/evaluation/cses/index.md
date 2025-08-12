# CSES

[Skip to main content](https://docs.ciroh.org/docs/products/evaluation/cses/#__docusaurus_skipToContent_fallback)

Community Streamflow Evaluation System (CSES) is a Python-based, user friendly, fast, and model agnostic streamflow evaluator tool. This tool can be used to evaluate any hydrological model that uses NHDPlus dataset. It allows a user to evaluate the performance of a hydrological model at the collocated USGS gauges and NHDPlus stream reaches. This Python-based tool helps visualize the results and investigate the model performance interactively. The current version of the tool is available on GitHub and can be accessed using the following link.

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/Community-Streamflow-Evaluation-System/blob/main/README.md](https://github.com/CIROH-UA/Community-Streamflow-Evaluation-System/blob/main/README.md).

[![Github_top](https://user-images.githubusercontent.com/33735397/206313977-e67ba652-3340-4a1b-b1d1-141d8d5001f2.PNG)](https://user-images.githubusercontent.com/33735397/206313977-e67ba652-3340-4a1b-b1d1-141d8d5001f2.PNG)

# Community Streamflow Evaluation System (CSES)

[![GitHub](https://camo.githubusercontent.com/40d4219549ca27cfaaeb305a1d71502c6a99de211016c535836ea1d63d58cb68/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6963656e73652f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f6c6f676f3d476974487562267374796c653d706c6173746963)](https://camo.githubusercontent.com/40d4219549ca27cfaaeb305a1d71502c6a99de211016c535836ea1d63d58cb68/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6963656e73652f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f6c6f676f3d476974487562267374796c653d706c6173746963)[![GitHub top language](https://camo.githubusercontent.com/02c8977bdb708eb0580786ed92a3b28030e4e1fd640642ce3cdedabade7e9088/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c616e6775616765732f746f702f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/02c8977bdb708eb0580786ed92a3b28030e4e1fd640642ce3cdedabade7e9088/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c616e6775616765732f746f702f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub repo size](https://camo.githubusercontent.com/e8f9a5fc333b2659dc4161da882d904a66c6bcda2d95f9a206ea004be56cd7a7/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f7265706f2d73697a652f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f6c6f676f3d476974687562267374796c653d706c6173746963)](https://camo.githubusercontent.com/e8f9a5fc333b2659dc4161da882d904a66c6bcda2d95f9a206ea004be56cd7a7/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f7265706f2d73697a652f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f6c6f676f3d476974687562267374796c653d706c6173746963)[![GitHub language count](https://camo.githubusercontent.com/c24d311b5c6f3aac014746b13ca15a9d92118153ef3b2013cd69f94a9894844b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c616e6775616765732f636f756e742f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/c24d311b5c6f3aac014746b13ca15a9d92118153ef3b2013cd69f94a9894844b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c616e6775616765732f636f756e742f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub commit activity](https://camo.githubusercontent.com/fbf45c41f1e74e6f16be5d3ec26a3eb447da2a6d1aec9a686f3fe4385193e33e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f636f6d6d69742d61637469766974792f6d2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/fbf45c41f1e74e6f16be5d3ec26a3eb447da2a6d1aec9a686f3fe4385193e33e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f636f6d6d69742d61637469766974792f6d2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub Pipenv locked Python version](https://camo.githubusercontent.com/8e4280f77875898c4ed058e64a290a53b444f2cbfcb02985d06260fb65b78f9e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f706970656e762f6c6f636b65642f707974686f6e2d76657273696f6e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/8e4280f77875898c4ed058e64a290a53b444f2cbfcb02985d06260fb65b78f9e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f706970656e762f6c6f636b65642f707974686f6e2d76657273696f6e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub branch checks state](https://camo.githubusercontent.com/29e1e12d85f418f1279349c84b9d55125875ac395645a3a6f131d6195158ccee/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f636865636b732d7374617475732f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d2f6d61696e3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/29e1e12d85f418f1279349c84b9d55125875ac395645a3a6f131d6195158ccee/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f636865636b732d7374617475732f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d2f6d61696e3f7374796c653d706c6173746963)[![GitHub issues](https://camo.githubusercontent.com/47e1df69ed9cdc180cb2a705afdb93f87d22b18b1099ea77f0aaa1177c0e94a1/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/47e1df69ed9cdc180cb2a705afdb93f87d22b18b1099ea77f0aaa1177c0e94a1/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub milestones](https://camo.githubusercontent.com/fb4aa47d2a564e91584795880ca24d83dde2baccbc143a9b4a8372c1356a89d6/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f636c6f7365642f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/fb4aa47d2a564e91584795880ca24d83dde2baccbc143a9b4a8372c1356a89d6/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f636c6f7365642f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub milestones](https://camo.githubusercontent.com/d007f4662ccb559290101391ba64979855c89b0bb92cdfff6c0807005ebd26a4/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f6f70656e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/d007f4662ccb559290101391ba64979855c89b0bb92cdfff6c0807005ebd26a4/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f6f70656e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)[![GitHub milestones](https://camo.githubusercontent.com/d007f4662ccb559290101391ba64979855c89b0bb92cdfff6c0807005ebd26a4/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f6f70656e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)](https://camo.githubusercontent.com/d007f4662ccb559290101391ba64979855c89b0bb92cdfff6c0807005ebd26a4/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6d696c6573746f6e65732f6f70656e2f77686974656c696768746e696e673435302f436f6d6d756e6974792d53747265616d666c6f772d4576616c756174696f6e2d53797374656d3f7374796c653d706c6173746963)

A Novel Community Streamflow Evaluation System (CSES) to evaluate hydrological model performance using a standardized NHDPlus data model.
CSES evaluates modeled streamflow to a repository of over 5,000 in situ USGS monitoring sites, with interactive visualizations supporting an in-depth analysis.

## Application Overview

National-scale streamflow modeling remains a modern challenge, as changes in the underlying hydrology from land use and land cover (LULC) change, anthropogentic streamflow modification, and general process components (reach length, hydrogeophysical processes, precipitation, temperature, etc) greatly influence hydrological modeling.
In a changing climate, there is a need to anticipate flood intensity, impacts of groundwater depletion on streamflow, western mountain low-flow events, eastern rain-on-snow events, storm-induced flooding, and other severe environmental problems that challenge the management of water resources.
Given the National Water Model (NWM) bridges the gap between the spatially coarse USGS streamflow observations by providing a near-continuous 2.7 million reach predictions of streamflow using the standardized NHDPlus framework, there lies the potential to improve upon the capabilities of the model by characterizing predictive performance across the heterogeneity of processes and land covers present at the national scale.
The python-based Community-Streamflow-Evaluation-System package provides a foundation to evaluate national hydrography dataset (nhd) based model outputs with colocated USGS/NWIS streamflow monitoring stations (parameter: 060) without the need to download in-situ or NWM v2.1 data (NWM v3.0 coming soon!).
The package contains three key methods for evaluation: state-based LULC, HUC level analysis, and USGS station-based analysis.
Below is a description of each method and application.
Designed to assess NWM version 2.1 retrospective performance, by using the exemplified data model the tool can evaluate other model predictions, with the motivation to improve regionally dominant hydrological modeling skill.
By using Community-Streamflow-Evaluation-System, researchers can identify locations where a model may benefit from further training/calibration/parameterization or a need for new model processes/features (e.g., integration of reservoir release operations) to ultimately create new post-processing methods and/or hydrological modeling formulations to improve streamflow prediction capabilities with respect to modeling needs (e.g., stormflow, supply, emergency management, flooding, etc).

### Data Access

Community-Streamflow-Evaluation-System leverages USGS/NWIS observations from 1980-2020 and colocated and while all data is publically available through the respective agencies, we found the download time to be preventative for a timely model evaluation.
The Alabama Water Institute at the University of Alabama hosts NWM v2.1 retrospective for all colocated USGS monitoring stations at a daily temporal resolution and provides the data free of charge via access to Amazon AWS S3 cloud storage.
Community-Streamflow-Evaluation-System can quickly access observed and predicted data supporting a fast and repeatable tool for evaluating modeled streamflow performance.

## Dependencies (versions, environments)

Python: Version 3.9.12.

### Required packages

The included requirements.txt file should set up the correct Community-Streamflow-Evaluation-System environment.
To use Community-Streamflow-Evaluation-System, create a virtual Python environment and run the requirement.txt file to ensure all package versions are correct.
To get started, click the [Here](https://github.com/CIROH-UA/Community-Streamflow-Evaluation-System/blob/main/Getting%20Started.md)

## Streamflow Evaluation Options

Each streamflow evaluation method requires similar inputs, including a start date, end date, and model.
There are currently three different evaluation classes, each providing the user with a unique method for evaluating streamflow modeling performance:

- Class Eval_State(): Modeled Streamflow Evaluation by StreamStats
- Class HUC_Eval(): Modeled Streamflow Evaluation by Hydrologic Unit Code (HUC)
- Class Reach_Eval(): - NHD - USGS Streamflow Evaluation

For all examples, the predictions are from the NWM v2.1 retrospective.
Please see the Examples folder for more information on applying each specific class.

### Modeled Streamflow Evaluation by StreamStats

To determine how LULC affects the predictive performance of streamflow models, Community-Streamflow-Evaluation-System uses StreamStats to categorize the watershed upstream of each USGS monitoring site by watershed characteristics.
Please see the State Land Use - Land Cover Evaluation.md readme to use the tool.

[![LULC_mapping](https://user-images.githubusercontent.com/33735397/205775870-5efab8e2-57ce-4ecb-b6c1-012909ece220.PNG)](https://user-images.githubusercontent.com/33735397/205775870-5efab8e2-57ce-4ecb-b6c1-012909ece220.PNG)

_Running the Community-Streamflow-Evaluation-System LULC_Eval class loads, processes, and visualizes model performance for the state, category, and size of interest_

[![LULC_mapping_highlight](https://user-images.githubusercontent.com/33735397/205776459-355507b4-2036-4eca-8bb3-fc88debbebef.PNG)](https://user-images.githubusercontent.com/33735397/205776459-355507b4-2036-4eca-8bb3-fc88debbebef.PNG)

_By clicking on a marker a popup of the modeled vs. observed performance at the inputted temporal frequency will appear_

[![LULC_holoviews](https://user-images.githubusercontent.com/33735397/205777709-65a8e6d8-0d7a-42e5-81b3-819462cb6e6a.PNG)](https://user-images.githubusercontent.com/33735397/205777709-65a8e6d8-0d7a-42e5-81b3-819462cb6e6a.PNG)

_The Community-Streamflow-Evaluation-System supports an interactive engagement with model results_

### Modeled Streamflow Evaluation by Hydrologic Unit Code (HUC)

The HUC_Eval class allows the user to evaluate modeled streamflow with observed in situ NWIS monitoring sites for watershed(s) of interest.
The user can input multiple watersheds (e.g., Great Salt Lake: ['1601', '1602'])
The user must enter a start date, end date, watersheds, and model to compare (NWM v2.1 is set up).
NWM retrospective data spans from 1980 - 2020, and USGS/NWIS data is location-dependent.

[![LULC_HUC_GSL](https://user-images.githubusercontent.com/33735397/206265320-7c640b40-830e-41ed-8e3f-67a2b20984c5.PNG)](https://user-images.githubusercontent.com/33735397/206265320-7c640b40-830e-41ed-8e3f-67a2b20984c5.PNG)

_The HUC_Eval class loads all USGS and colocated modeled NHD reaches for evaluation._
_Color coding of the markers allows for quick identification of poor and well-performing reaches and clicking on the markers will put up a modeled vs. observed graph at the desired temporal resolution._

[![LULC_holoviews_HUCEval](https://user-images.githubusercontent.com/33735397/206265779-5417343f-ed40-4704-b8bc-12ada2672259.PNG)](https://user-images.githubusercontent.com/33735397/206265779-5417343f-ed40-4704-b8bc-12ada2672259.PNG)

_Similar to the State_Eval class, the HUC_Eval class supports a more in-depth graphical analysis of the modeled vs. observed using the holoviews package_

### Modeled Streamflow Evaluation - NHD - USGS Streamflow Evaluation

The Reach_Eval class allows the user to evaluate modeled streamflow with selected NWIS monitoring sites of interest.
The user can input multiple USGS sites (e.g., ['02378780', '02339495', '02342500'])
Similar to the other classes, enter a start date, end date, and model to compare (NWM v2.1 is set up).
NWM retrospective data spans from 1980 to 2020, and USGS/NWIS data is location-dependent

[![LULC_ReachEval_map](https://user-images.githubusercontent.com/33735397/206266617-f06c9836-0193-4f6f-94f9-11982272d34d.PNG)](https://user-images.githubusercontent.com/33735397/206266617-f06c9836-0193-4f6f-94f9-11982272d34d.PNG)

_The Reach_Eval class quickly loads and maps the selected USGS streamflow monitoring locations, along with the colocated model predictions of NHD reaches._
_The color code of the marker indicates the model performance at the respective USGS monitoring station site, and by clicking on a marker, the interactive map produces a graph at the desired temporal resolution._

[![LULC_holoviews_Reach_Eval](https://user-images.githubusercontent.com/33735397/206267196-749bb94d-aa57-4d24-9b4e-97e7567e1fc0.PNG)](https://user-images.githubusercontent.com/33735397/206267196-749bb94d-aa57-4d24-9b4e-97e7567e1fc0.PNG)

_Similar to the State_Eval and HUC_Eval classes, the Reach_Eval class supports a more in-depth graphical analysis of the modeled vs. observed using the holoviews package_