# Project Title: **tethysportal-ciroh**

## Project Objective  
The **CIROH Tethys Portal** is a web-based platform deployed on an Amazon EKS cluster. It integrates multiple hydrologic and water data applications under a unified interface and provides access to visualization, computation, and data tools. The infrastructure uses Kubernetes and Terraform for deployment and management.

## Core Functionalities  
- Runs on Amazon EKS (`namespace: cirohportal`) with traffic routing via AWS Application Load Balancer.  
- Hosts multiple applications within a Django/Tethys web stack, including THREDDS, PostgreSQL, and Redis services.  
- Supports data access and visualization through built-in and proxied apps.  
- Provides infrastructure-as-code deployment using Terraform modules.  
- Allows Helm-based upgrades for updating Docker images.  
- Includes troubleshooting guidelines for AWS infrastructure and Kubernetes clusters.  
- Offers monitoring and visualization tools for cluster management.  

## Technical Stack  
- **Languages/Frameworks:** Django, Tethys Platform.  
- **Infrastructure:** Amazon EKS, AWS Application Load Balancer, Terraform, Helm, Kubernetes.  
- **Databases/Services:** PostgreSQL, Redis, THREDDS Data Server.  
- **Monitoring Tools:** k9s, eks-node-viewer.  
- **Submodules:** Terraform modules for reproducible infrastructure setup.  

## Setup and Usage  
1. **Prerequisites:**  
   - AWS CLI and configured credentials.  
   - Terraform installed.  
   - Access to AWS EKS cluster.  

2. **Terraform Deployment:**  
   - Configure kubectl for the target cluster.  
   - Run the Terraform workflow:  
     ```bash
     terraform init
     terraform plan
     terraform apply
     ```  
   - Use `terraform destroy` to clean up development environments.  

3. **Helm Upgrade Example:**  
   ```bash
   helm repo add tethysportal-ciroh https://docs.ciroh.org/tethysportal-ciroh
   helm upgrade cirohportal-prod tethysportal-ciroh/ciroh      --install --wait --timeout 3600      -f charts/ciroh/ci/prod_aws_values.yaml      --set storageClass.parameters.fileSystemId=<EFS_ID>      --set image.tag=<newTag>      --namespace cirohportal
   ```  

4. **Troubleshooting:**  
   - Address ALB and VPC deletion issues manually if Terraform fails.  
   - Use Kubernetes and Terraform documentation for resolving cluster access errors.  

## Project Context & Domain  
- **Domain:** Hydrology / Cloud Infrastructure / Web Portals.  
- **Affiliation:** CIROH.  
- **Purpose:** Provide a scalable and modular web-based infrastructure for hosting CIROH applications using Tethys Platform and AWS.  

## Input / Output  
**Input:**  
- Terraform configuration variables (region, cluster name, Helm chart, etc.).  
- Helm values and Docker image tags for deployment.  

**Output:**  
- Deployed Tethys Portal web application with integrated data visualization and analysis tools.  
