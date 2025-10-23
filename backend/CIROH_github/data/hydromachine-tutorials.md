# Project Title: **hydromachine-tutorials**

## Project Objective  
**hydromachine-tutorials** is an educational repository designed to teach the application of **Machine Learning (ML)** techniques for **hydrological modeling**. It demonstrates two complementary ML approaches for post-processing **National Water Model (NWM)** streamflow predictions — one using **LSTM neural networks** deployed on AWS SageMaker, and the other using **XGBoost decision trees** for local experimentation. The tutorials enable learners to explore the full ML workflow from data preprocessing to model evaluation and deployment.

## Core Functionalities  
- Provides **two educational tracks** with parallel ML methodologies:
  - **LSTM Neural Networks (AWS SageMaker Track):**  
    - Cloud-native ML pipeline using PyTorch and AWS SageMaker.  
    - Demonstrates endpoint deployment, remote training, and resource cleanup.  
    - Produces station-specific `MinMaxScaler` artifacts for multiple USGS monitoring sites.  
  - **XGBoost Decision Trees (Local Track):**  
    - Local ML workflow using scikit-learn, XGBoost, and Optuna.  
    - Teaches manual and automated hyperparameter tuning, model serialization, and evaluation.  
    - Generates `.pkl` model files and `.joblib` scaler files.  
- Unified data source from **AWS S3 (`streamflow-app-data/final_input.parquet`)** containing 18 meteorological and hydrological input features.  
- Provides a shared **Conda environment (`devcon_xgboost.yaml`)** with 200+ dependencies for reproducibility.  
- Includes **Jupyter notebooks** for each tutorial step, facilitating hands-on learning.  

## Technical Stack  
- **Languages/Frameworks:** Python (PyTorch, XGBoost, scikit-learn).  
- **Tools/Dependencies:** Optuna, SHAP, pandas, GeoPandas, GDAL, boto3, AWS SageMaker SDK.  
- **Environments:**  
  - Cloud: AWS SageMaker (LSTM track).  
  - Local: Conda/Jupyter environment (XGBoost track).  
- **Data Storage:** AWS S3 (Parquet format).  

## Project Context & Domain
- **Domain:** Hydrology / Machine Learning / Streamflow Modeling  
- **Affiliation:** CIROH (Cooperative Institute for Research to Operations in Hydrology), University of Alabama  
- **Purpose:** To provide accessible, reproducible, and scalable ML tutorials that teach hydrologists how to post-process and improve streamflow predictions from physics-based models like the NWM.

---

## Intended Audiences

| Audience          | Primary Interest                              | Recommended Track          |
|--------------------|-----------------------------------------------|-----------------------------|
| Students/Learners  | Foundational ML + hydrology skills             | XGBoost (progressive learning) |
| Researchers        | Comparative model evaluation                   | Both tracks                 |
| Practitioners      | Cloud deployment and endpoint management       | LSTM (AWS SageMaker)        |

---

## Learning Objectives
- Apply ML for bias correction in physical hydrologic model outputs.  
- Conduct manual and automated hyperparameter optimization.  
- Deploy cloud-native ML models to AWS SageMaker endpoints.  
- Compare LSTM vs. XGBoost methods for regression accuracy.  
- Manage multi-station preprocessing and scaling workflows.

---

## Input / Output

### Input
- Streamflow data from `s3://streamflow-app-data/final_input.parquet`  
- 18 hydrometeorological features per sample from 9 USGS stations  
- Conda environment configuration and AWS credentials (for LSTM track)

### Output
- Trained models (`.pkl`), scaling artifacts (`.joblib`), and performance plots  
- Evaluation notebooks summarizing model accuracy and trade-offs

---

## License
- Licensed under the **Apache License 2.0**  
- Permits use, modification, distribution, and commercial application  
- Requires attribution and inclusion of the license notice  
- © 2025 CIROH – The University of Alabama
