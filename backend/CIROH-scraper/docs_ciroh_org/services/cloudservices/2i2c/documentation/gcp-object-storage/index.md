---
title: Manage files in GCP bucket
source: https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage
scraped_date: 2025-01-31
---

This guide is for managing objects in GCP buckets available on 2i2c CIROH JupyterHub. For more detailed explanation, you can visit [2i2c docs site](https://docs.2i2c.org/user/topics/data/object-storage/manage-object-storage-gcp/).

### 1\. Overview

CIROH JupyterHub uses object Google Cloud Storage to store data in buckets (containers for objects). Currently, there are two buckets available to use on CIROH JupyterHub.

- **Scratch Bucket**: It is intended for storing temporary files since any files in scratch bucket get deleted after seven days. Open a terminal in CIROH JupyterHub and run this command to display your scratch bucket name:

```codeBlockLines_e6Vv
echo $SCRATCH_BUCKET
gs://awi-ciroh-scratch/<username>

```

**Note:** In the above command output, the name of the bucket is 'awi-ciroh-scratch' and `<username>` is the folder in the bucket.

- **Persistent Bucket**: It is recommended to use for storing files that you will be using for a longer period of time. Open a terminal in CIROH JupyterHub and run this command to display your persistent bucket name:

```codeBlockLines_e6Vv
echo $PERSISTENT_BUCKET
gs://awi-ciroh-persistent/<username>

```

### 2\. Copying file to a bucket

You can copy files on your CIROH JupyterHub to an available bucket using the following command.

```codeBlockLines_e6Vv
gcloud storage cp <filepath> $PERSISTENT_BUCKET/<filepath>

```

### 3\. Copying file from a bucket to CIROH JupyterHub

You can copy files from an accessible bucket to your CIROH JupyterHub using the following command.

```codeBlockLines_e6Vv
gcloud storage cp $PERSISTENT_BUCKET/<filepath> <destination-filepath>

```

### 4\. Listing files in a bucket

You can list all files/folder in a bucket using the following command.

```codeBlockLines_e6Vv
gcloud storage ls $PERSISTENT_BUCKET

```

**Note:** The above command will list all files/folders in the folder `<username>`. It won't list files in the sub-folders of folder `<username>`. To list all files including the files in the sub-folders of the root folder `<username>`, use the following command.

```codeBlockLines_e6Vv
gcloud storage ls --recursive $PERSISTENT_BUCKET

```

### 5\. Deleting file from a bucket

You can delete a file in a bucket with the following command:

```codeBlockLines_e6Vv
gcloud storage rm $PERSISTENT_BUCKET/<filepath>

```

### 6\. User permssions on buckets

All users have read/write permissions on both the scratch and persistent buckets.

note

Anyone can access each other's files in buckets on the hub. Please be careful not to delete other user's files. Using the enviornment variables ($SCRATCH\_BUCKET & $PERSISTENT\_BUCKET) to access buckets in commands would prevent accidententally deleting any other user's files. Your actions impact the entire organization's storage. If unsure, consult with the team lead or ciroh IT support.

### 7\. Accessing buckets in Python

You can find information on how to access buckets in Python code, [here.](https://docs.2i2c.org/user/topics/data/object-storage/working-with-object-storage/)

## Where to go for help:

- Email [ciroh-it-admin@ua.edu](mailto:ciroh-it-admin@ua.edu) UA CIROH Cloud Team
- CIROH Cloud Slack Channel - #ciroh-ua-it-admin
- CIROH Infrastructure Support Slack Channel - #ciroh-infrastructure-support

- [1\. Overview](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#1-overview)
- [2\. Copying file to a bucket](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#2-copying-file-to-a-bucket)
- [3\. Copying file from a bucket to CIROH JupyterHub](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#3-copying-file-from-a-bucket-to-ciroh-jupyterhub)
- [4\. Listing files in a bucket](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#4-listing-files-in-a-bucket)
- [5\. Deleting file from a bucket](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#5-deleting-file-from-a-bucket)
- [6\. User permssions on buckets](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#6-user-permssions-on-buckets)
- [7\. Accessing buckets in Python](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#7-accessing-buckets-in-python)
- [Where to go for help:](https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/gcp-object-storage/#where-to-go-for-help)