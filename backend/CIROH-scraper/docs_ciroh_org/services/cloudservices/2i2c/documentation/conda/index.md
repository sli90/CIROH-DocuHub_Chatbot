---
title: Persistent Conda Environment
source: https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/conda
scraped_date: 2025-01-31
---

To ensure your Conda environments persist across server restarts on the CIROH 2i2c server, create them in your home directory. Follow these steps:

### 1\. Create a directory for Conda environments:

You can set up a directory within your home folder to store all your Conda environments. This prevents them from being removed when the server is restarted. For example:

```codeBlockLines_e6Vv
mkdir -p ~/conda_envs

```

### 2\. Create a new environment in that directory:

Use the _--prefix_ option with conda create to specify the location where you want to create your environment. For example, to create an environment called _my\_env_ in _~/conda\_envs_:

```codeBlockLines_e6Vv
conda create --prefix ~/conda_envs/my_env python=3.9

```

### 3\. Activate the environment:

You can activate the environment as usual, using the path to where you created it:

```codeBlockLines_e6Vv
conda activate ~/conda_envs/my_env

```

### 4\. Automatically activate the environment on restart:

If you want this environment to be activated every time you log in or the server restarts, you can add the following to your _.bashrc_ or _.bash\_profile_ file:

```codeBlockLines_e6Vv
conda activate ~/conda_envs/my_env

```

By creating your environments in your home folder (e.g., _~/conda\_envs/_), they will persist across server restarts, ensuring that you don't have to recreate them every time.

- [1\. Create a directory for Conda environments:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/conda/#1-create-a-directory-for-conda-environments)
- [2\. Create a new environment in that directory:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/conda/#2-create-a-new-environment-in-that-directory)
- [3\. Activate the environment:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/conda/#3-activate-the-environment)
- [4\. Automatically activate the environment on restart:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/conda/#4-automatically-activate-the-environment-on-restart)