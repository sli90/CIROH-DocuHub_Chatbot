# Summary and Schedule

This is a new lesson built with [The Carpentries Workbench](https://carpentries.github.io/sandpaper-docs).

## Workshop Schedule

| Duration | Episode | Questions |
|----------|---------|-----------|
| | Setup Instructions | Download files required for the lesson |
| Duration: 00h 00m | 1. [Introduction](https://docs.ciroh.org/training-NGIAB-101/instructor/introduction.html) | What is the NextGen Framework?<br>What is NextGen in a Box (NGIAB)?<br>What is containerization?<br>Why should I use NGIAB? |
| Duration: 00h 15m | 2. [Installation and Setup](https://docs.ciroh.org/training-NGIAB-101/instructor/installation.html) | How do I install and set up NGIAB?<br>What are the prerequisites for running NGIAB?<br>How do I verify my installation? |
| Duration: 00h 27m | 3. [Data Preparation](https://docs.ciroh.org/training-NGIAB-101/instructor/data-preparation.html) | How should I prepare my run directory?<br>What is the Data Preprocess tool? |
| Duration: 01h 17m | 4. [Model Execution](https://docs.ciroh.org/training-NGIAB-101/instructor/model-execution.html) | How do I execute a NextGen run? |
| Duration: 01h 27m | 5. [Evaluation](https://docs.ciroh.org/training-NGIAB-101/instructor/evaluation.html) | How do I use Tools for Exploratory Evaluation in Hydrologic Research (TEEHR) to evaluate my NextGen models in NGIAB? |
| Duration: 01h 42m | 6. [Visualization](https://docs.ciroh.org/training-NGIAB-101/instructor/visualization.html) | How do I visualize my NextGen runs? |
| Duration: 01h 57m | 7. [Calibration](https://docs.ciroh.org/training-NGIAB-101/instructor/calibration.html) | How do I calibrate parameters for a NextGen run? |
| Duration: 02h 22m | 8. [Advanced Topics](https://docs.ciroh.org/training-NGIAB-101/instructor/advanced-topics.html) | How do I use NGIAB on an high-performance computing (HPC) system?<br>How do I use the Data Visualizer through an SSH connection?<br>How can I contribute to NGIAB? |
| Duration: 03h 27m | Finish | |

The actual schedule may vary slightly depending on the topics and exercises chosen by the instructor.

## Welcome

Welcome to the NextGen In A Box (NGIAB) 101 training module!

### Source Code and Documentation

The source code for NextGen In A Box (NGIAB) is found at [our GitHub repository](https://github.com/CIROH-UA/NGIAB-CloudInfra). The documentation for NGIAB and its extensions are found on the [CIROH docs](https://docs.ciroh.org/docs/products/Community%20Hydrologic%20Modeling%20Framework/).

To dive right into NGIAB as quickly as possible, follow the quick start guide on our [GitHub repository](https://github.com/CIROH-UA/NGIAB-CloudInfra), or head straight to our second episode, Installation. If you are interested in taking your time and learning in-depth about the features of NGIAB, follow the episodes in this module.

For all users, the [Key Points summary page](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/key-points.html) and the [Glossary](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/reference.html) may be useful references. The [Advanced Topics episode](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/advanced-topics.html) is optional, but may contain useful content depending on your specific use case.

Note: This module requires you to use Bash scripting in your command line and Git. All commands will be given in this module. However, if you are interested in learning more, you can refer to this [quick Bash tutorial by Ubuntu](https://ubuntu.com/tutorials/command-line-for-beginners#1-overview), [this basic Git tutorial in the Git documentation](https://git-scm.com/docs/gittutorial), and this [Git workflow tutorial by CIROH](https://github.com/AlabamaWaterInstitute/data_access_examples/blob/main/doc/GIT_USAGE.md).

### DevCon 2025 NGIAB Workshop Attendees

Are you joining us for the DevCon 2025 NGIAB workshop? We have prepared two DevCon-specific documents for you.

- [DevCon 2025 Jetstream Instructions](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/devcon25js.html) will walk you through the specific steps we will take in this hands-on workshop.
- [DevCon 2025 Troubleshooting](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/troubleshooting.html) contains useful reference material if you are stuck during the workshop.

**These documents are key, since we will not be following the default episodes exactly as written.**

After the workshop, feel free to explore the rest of this module to learn more about NGIAB!

### HPC Users

Are you planning on running NGIAB on an HPC? You can follow the episodes in order, but replace Episode 2: Installation and Setup with the HPC-specific instructions in the [Advanced Topics module](https://docs.ciroh.org/training-NGIAB-101/training-NGIAB-101/advanced-topics.html).

## System Requirements

The Installation episode will walk you through the steps to install Windows Subsystem for Linux (WSL), Docker, NGIAB, and retrieve sample data sets. This page summarizes system requirements.

### Windows
- **Software:** Docker, Git, WSL, Astral UV
- **Recommended Minimum RAM:** 8 GB

### MacOS
- **Software:** Docker, Git, Astral UV
- **Recommended Minimum RAM:** 8 GB

### Linux
- **Software:** Docker, Git, Astral UV
- **Recommended Minimum RAM:** 8 GB