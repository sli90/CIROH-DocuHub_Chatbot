---
title: Accessing the System
source: https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access
scraped_date: 2025-01-31
---

Pantarhei curretly only supports the Secure Shell (SSH) mechanisms for logging in. The Secure Shell mechanism uses SSH keys. If you need help creating or uploading your SSH keys, please see the Managing SSH Public Keys page for that information.

### General overview

To connect to Pantarhei using SSH, you must follow two high-level steps:

- [Connect to the University of Alabama (UA) Network](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access/#connect-to-the-network)
- [Connect to the Secure Shell (SSH)](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access/#connect-to-the-ssh)

Obtain Pantarhei Access

In the case that access to the Pantarhei system is unavailable to you, please follow the instructions on [Obtaining an Account](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/obtain).

### Connect to the Network

University of Alabama (UA) requires users to use the Virtual private network (VPN) to connect to the UA campus network in order to connect to the Pantarhei cluster.

tip

For more information on setting up a VPN, please visit the [Office of Information Technology (OIT) website](https://oit.ua.edu/services/internet-networking/vpn/).

### Connect to the SSH

- MacOS and Linux
- Windows

Once you are connected to the VPN, follow these steps to access Pantarhei:

1. **Open a Terminal:** Find `Terminal` in your local machine and open it.



tip





In MacOS, use Spotlight search ( **Command** \+ **Spacebar**) and type `Terminal` to open a new terminal window.

2. **Connect via SSH:** In the terminal,
   - Use the SSH command to connect to Pantarhei.





     ```codeBlockLines_e6Vv
     ssh <USERNAME>@pantarhei.ua.edu

     ```











     note





     Replace `<USERNAME>` with your actual Pantarhei username.

   - Enter your Pantarhei password

We hope this guide helps you efficiently utilize the Pantarhei HPC system for your research needs. Happy computing!

- [General overview](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access/#general-overview)
- [Connect to the Network](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access/#connect-to-the-network)
- [Connect to the SSH](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access/#connect-to-the-ssh)