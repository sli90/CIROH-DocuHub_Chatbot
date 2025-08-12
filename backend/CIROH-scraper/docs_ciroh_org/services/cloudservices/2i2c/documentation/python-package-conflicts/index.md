---
title: Python Package Version Conflicts
source: https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/python-package-conflicts
scraped_date: 2025-01-31
---

### Overview:

When different versions of Python packages are installed in your user home directory than the version that was already installed in the JupyterHub image, these local installations take precedence, potentially causing version mismatches and unexpected behavior.

### Troubleshooting guide:

#### Step 1: Identify Package Conflicts

```codeBlockLines_e6Vv
ls ~/.local/lib/pythonX.Y/site-packages/

```

**Note**: Replace X.Y with your Python version (e.g., 3.10). Find your version with `python --version`.

#### Step 2: Remove conflicting packages from user home directory

Clear all locally installed Python packages:

```codeBlockLines_e6Vv
rm -rf ~/.local/lib/pythonX.Y

```

**Note**: This will remove **ALL** Python packages installed in your home directory and ensure that only system or environment packages are used.

#### Step 3: Verify Your Environment

- Verify that you are using the correct JupyterHub image by checking the JUPYTER\_IMAGE environment variable:

```codeBlockLines_e6Vv
echo $JUPYTER_IMAGE

```

- Reinstall needed packages properly

```codeBlockLines_e6Vv
pip install <package-name>

```

- [Overview:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/python-package-conflicts/#overview)
- [Troubleshooting guide:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/python-package-conflicts/#troubleshooting-guide)