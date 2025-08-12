---
title: JupyterHub User Directory
source: https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/directory
scraped_date: 2025-01-31
---

This is a guide for understanding the File System in CIROH JupyterHub. You can find detailed explanation on [2i2c docs site](https://docs.2i2c.org/user/topics/data/filesystem/).

### 1\. `/home/jovyan`

This is your home directory and is same for all JupyterHub users. **Only you can access files in your home directory.** Any files you place in your home directory persists between sessions. It is recommended to use only for notebooks and code since it is not suitable for large datasets.

### 2\. `/home/jovyan/shared`

This is the shared **readonly** directory. All users can access and read from the shared directory. Only the hub admins can add and delete data from this directory.

### 3\. `/tmp`

This is a non persistient directory. This means any files you add under /tmp direcotry will be deleted once you log out. This directory can be used to store data temporary data.

- [1\. `/home/jovyan`](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/directory/#1-homejovyan)
- [2\. `/home/jovyan/shared`](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/directory/#2-homejovyanshared)
- [3\. `/tmp`](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/directory/#3-tmp)