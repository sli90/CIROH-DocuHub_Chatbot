---
title: Prevent Server Timeout
source: https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/server-timeout
scraped_date: 2025-01-31
---

JupyterHub servers typically stop after about an hour of inactivity to help manage computational reosurces. This can be present challenges for users who need to run long-running jobs. You have two options to keep your JupyterHub server active for longer periods:

### 1\. Jupyter Keepalive Extension

The Jupyter Keepalive extension provides an easy way to control your server's active time.

- To install the extension, open a terminal and run:

```codeBlockLines_e6Vv
pip install jupyter-keepalive

```

- Use the JupyterLab Command Palette (Command+Shift+C on Mac or Control+Shift+C on Linux/Windows) to select the "Keep server alive while idle" option.
- Once your task is complete, it's crucial that you then use the Command Palette to select the "Stop keeping server alive" option. This will ensure that the server is no longer being kept active unnecessarily.

![image of jupyterlab command palette](https://docs.ciroh.org/img/server-keepalive.png)

### 2\. Using `time.sleep()` (Alternate Method)

As an alternative, you can create a separate notebook with the following code and run the cell before starting your job.

```codeBlockLines_e6Vv
import time
time.sleep(24 * 60 * 60) # Sleeps for 24 hours

```

- [1\. Jupyter Keepalive Extension](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/server-timeout/#1-jupyter-keepalive-extension)
- [2\. Using `time.sleep()` (Alternate Method)](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/server-timeout/#2-using-timesleep-alternate-method)