# Installing NGIAB

[Skip to main content](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/install/#__docusaurus_skipToContent_fallback)

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/NGIAB-CloudInfra/blob/main/docs/02\_INSTALL.md](https://github.com/CIROH-UA/NGIAB-CloudInfra/blob/main/docs/02_INSTALL.md).

NGIAB is designed to run on Unix systems, which means that it's a bit easier to run on Mac and Linux computers.

Windows users can still make full use of NGIAB using Windows Subsystem for Linux (WSL); however, this may impact performance.

## Prerequisites

To get started with NGIAB-CloudInfra, you'll need to have Docker installed (and WSL, if appropriate).

### Windows

1. **Install WSL:** Head over to Microsoft's official documentation and follow their comprehensive guide on installing WSL: [https://learn.microsoft.com/en-us/windows/wsl/install](https://learn.microsoft.com/en-us/windows/wsl/install)
2. **Install Docker Desktop:** Begin by downloading and installing Docker Desktop from the official website: [https://docs.docker.com/desktop/install/windows-install/#install-docker-desktop-on-windows](https://docs.docker.com/desktop/install/windows-install/#install-docker-desktop-on-windows)
3. **Start Docker Desktop:** After installation, launch the Docker Desktop application.
4. **Open WSL as Admin:** Right-click on the WSL icon and select "Run as Administrator".
5. **Verify Installation:** In the WSL window, type the command docker ps -a to check if Docker is running correctly. This command should display a list of Docker containers.

> **Warning**: If you've installed WSL before as a part of Docker, be sure to create a second WSL distribution that isn't tied to Docker.
> NextGen In A Box shell commands can't be run from within Docker's dedicated WSL environment.

> Note that the absolute best Windows performance can be achieved by installing Docker Engine within a WSL environment and working strictly from there, using the same steps as a typical Linux installation.
>
> However, since the overhead from WSL will apply either way, it's often not worth the hassle. A purely Linux-based environment is strongly recommended for performance-sensitive and operational applications.

### Mac

1. **Install Docker Desktop:** Download and install Docker Desktop for Mac from: [https://docs.docker.com/desktop/install/mac-install/](https://docs.docker.com/desktop/install/mac-install/)
2. **Start Docker Desktop:** Launch the Docker Desktop application once the installation is complete.
3. **Open Terminal:** Open the Terminal application on your Mac.
4. **Verify Installation:** Similar to Windows, use the command docker ps -a in the Terminal to verify Docker is functioning as expected.

> Note that the Docker VMM offers the best performance on Macs. For more information, see Docker's documentation on [Virtual Machine Managers](https://docs.docker.com/desktop/features/vmm/).

### Linux

1. **Install Docker:** The installation process for Linux varies depending on your distribution. Refer to the official documentation for detailed instructions: [https://docs.docker.com/desktop/install/linux-install/](https://docs.docker.com/desktop/install/linux-install/)
2. **Start Docker and Verify:** Follow the same steps as described for Mac to start Docker and verify its installation using the docker ps -a command in the terminal.

> Note that Linux-based Docker performance will be significantly improved when installing Docker Engine rather than Docker Desktop.

## Installing and Testing

At a bare minimum, installing NGIAB is as simple as downloading this repository.
However, this guide also includes steps to download sample data and start up your first NGIAB run, which will help you get started right away.

### Step 1: Create Project Directory

- **Windows users: WSL (Right click and run as Admin):** For ease of access, you may want to store NGIAB's files in your Windows directories. To move there, run the following in your WSL CLI:

```
cd /mnt/c/Users/<Folder>
```

- From there, navigate to the directory where you'd like to store NGIAB and its associated data.

```
mkdir -p NextGen
cd NextGen
```

### Step 2: Download Sample Data

> While this step isn't strictly necessary, it'll be useful for verifying that NGIAB is working properly on your system.

- Within your project directory, create the `ngen-data` folder to hold the sample data.

```
mkdir -p ngen-data
cd ngen-data
```

- Use wget to download the compressed data file. Then, extract it.

```
wget https://ciroh-ua-ngen-data.s3.us-east-2.amazonaws.com/AWI-009/AWI_16_10154200_009.tar.gz
tar -xf AWI_16_10154200_009.tar.gz
```

- Then, return to the root of the project directory.

```
cd ..
```

### Step 3: Clone and Run NGIAB

> **For WSL users:** Before pulling NGIAB, ensure that Git is configured to pull with LF line breaks instead of CRLF line breaks. Failing to do so will prevent NGIAB's shell scripts from correctly running.
>
> Information on triaging this issue is available in the [NGIAB 101 training module](https://docs.ciroh.org/training-NGIAB-101/installation.html).

- Clone the NGIAB-CloudInfra repository.

```
git clone https://github.com/CIROH-UA/NGIAB-CloudInfra.git
cd NGIAB-CloudInfra
```

- At this point, everything you need to install NGIAB has been installed!
- To test your installation, try running the interactive guide script, which will help you navigate your first model run:

```
./guide.sh
```

> For a broader introduction to using the NGIAB ecosystem, including how to preprocess your own data, please see the [NGIAB 101 training module](https://docs.ciroh.org/training-NGIAB-101/).