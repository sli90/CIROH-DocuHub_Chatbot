# Project Title: **api-nwm-gcp**

## Project Objective  
The **api-nwm-gcp** repository provides a REST API backed by National Water Model (NWM) data, developed on Google Cloud Platform (GCP). It enables users to access hydrologic and geospatial data through cloud-based infrastructure and deployment.

## Core Functionalities  
- REST API for accessing National Water Model (NWM) data.  
- Cloud infrastructure setup using Terraform and Google Cloud SDK.  
- Automated deployment using Cloud Build and Cloud Run.  
- API management with Google API Gateway.  
- Example API endpoints for geometry, analysis-assimilation data, and forecast data.  
- Includes infrastructure configuration for service accounts, permissions, and Docker image storage in Artifact Registry.  

## Technical Stack  
- **Cloud Services:** Google Cloud Platform (Cloud Run, API Gateway, Cloud Build, Artifact Registry).  
- **Infrastructure Management:** Terraform.  
- **Languages/Tools:** Docker, gcloud CLI, terraform CLI.  
- **Deployment Configuration:** cloudbuild.yaml, deployment.tfvars.  

## Setup and Usage  
### Infrastructure Setup  
1. Authenticate with gcloud:  
   ```bash
   gcloud auth application-default login
   ```  
2. Update variables in `deployment.tfvars` with project-specific details.  
3. Initialize Terraform:  
   ```bash
   terraform init
   ```  
4. (Optional) Preview deployment plan:  
   ```bash
   terraform plan -var-file="deployment.tfvars"
   ```  
5. Deploy infrastructure:  
   ```bash
   terraform apply -var-file="deployment.tfvars"
   ```  
6. (Optional) Destroy infrastructure:  
   ```bash
   terraform destroy -var-file="deployment.tfvars"
   ```  

### Deployment  
#### Initial Docker Build and Cloud Run Deploy  
1. Ensure Cloud Build service account has **Cloud Run Admin** and **Service Account User** roles enabled.  
2. Submit a Cloud Build job:  
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```  
3. Modify Cloud Run parameters in `cloudbuild.yaml` if necessary.  

#### Deploy API Gateway  
1. Create the API:  
   ```bash
   gcloud api-gateway apis create API_ID --project=PROJECT_ID
   ```  
2. Create the API config:  
   ```bash
   gcloud api-gateway api-configs create CONFIG_ID      --api=API_ID --openapi-spec=API_DEFINITION      --project=PROJECT_ID --backend-auth-service-account=SERVICE_ACCOUNT_EMAIL
   ```  
3. Deploy an API config to a gateway:  
   ```bash
   gcloud api-gateway gateways create GATEWAY_ID      --api=API_ID --api-config=CONFIG_ID      --location=GCP_REGION --project=PROJECT_ID
   ```  

### Example Use  
#### Geometry  
```bash
curl -H "x-api-key: ${API_KEY}" "${NWM_API}/geometry?lon=-121.76&lat=37.70"
```  

#### Analysis Assimilation Data  
```bash
curl -H "x-api-key: ${API_KEY}"   "${NWM_API}/analysis-assim?start_time=2018-09-17&end_time=2023-05-01&comids=15059811&output_format=csv"
```  

#### Forecast Data  
```bash
curl -H "x-api-key: ${API_KEY}"   "${NWM_API}/forecast?forecast_type=long_range&reference_time=2023-05-01&ensemble=0&comids=15059811&output_format=csv"
```  

## Project Context & Domain  
- **Domain:** Hydrology / Cloud Infrastructure / API Development.  
- **Affiliation:** Not specified.  
- **Purpose:** Provide cloud-based access to National Water Model data through a REST API deployed on Google Cloud Platform.  

## Input / Output  
**Input:**  
- API parameters such as longitude/latitude, forecast type, time range, ensemble ID, and COMIDs.  

**Output:**  
- JSON or CSV-formatted responses containing geometry, analysis-assimilation, or forecast data from the National Water Model.  
