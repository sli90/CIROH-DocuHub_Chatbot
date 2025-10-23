# Project Title: **LSTM-Tutorials**

## Project Objective  
The **LSTM-Tutorials** repository is an educational framework for learning and applying Long Short-Term Memory (LSTM) deep learning models to hydrological time series forecasting. It progresses from simple univariate streamflow prediction to advanced multivariate post-processing of National Water Model (NWM) outputs, leveraging PyTorch with GPU acceleration. The repository emphasizes hands-on learning through modular, production-oriented workflows for hydrologists and environmental data scientists.  

---

## Learning Objectives  
Participants learn to:
1. Build single-layer univariate LSTM architectures.  
2. Incorporate multiple hydrometeorological features into multivariate LSTMs.  
3. Master PyTorch fundamentals (tensor operations, training loops, model definition).  
4. Configure and utilize GPU environments with CUDA for efficient training.  
5. Access and process AWS S3 data (`streamflow-app-data` bucket).  
6. Develop reusable scripts for data loading, training, and evaluation.  

---


The tutorial notebooks progressively import and build upon reusable infrastructure from the `scripts/` directory, which provides environment-independent functions for data processing, model definition, and evaluation.  

---

## Core Infrastructure Components  

| Module | File | Primary Functions | Purpose |
|--------|------|------------------|----------|
| **Data Processing** | `dataprocessing.py` | `readdata()`, `df_combine()`, `create_lookback_univariate()`, `create_lookback_multivariate()`, `Multivariate_DataProcessing()` | AWS S3 integration, feature scaling, sequence creation |
| **Model Definition** | `LSTM.py` | `Simple_LSTM`, `weight_init()`, `train_LSTM()`, `load_existing_LSTM()` | Model definition, training, and persistence |
| **Evaluation** | `evaluation.py` | `calculation()`, `plot()`, `nse()` | Hydrological metrics (NSE, KGE, RMSE, MAPE, MaxError), inverse scaling, visualization |

---

## Learning Progression  

| Level | Notebook | Focus | Key Concepts |
|--------|-----------|--------|---------------|
| **1: Fundamentals** | `Simple_TS_Streamflow_LSTM.ipynb` | Single-layer LSTM for univariate streamflow | PyTorch basics, CPU/GPU configuration |
| **2: Architecture Exploration** | `Bidirectional_LSTM.ipynb`, `Stacked_LSTM.ipynb`, `Feature_LSTM.ipynb` | Model variants and multivariate inputs | Bidirectional layers, stacked architectures, feature engineering |
| **3: Production Workflows** | `MultiVariate_NWM_PostProcessing_LSTM.ipynb` | Full multivariate workflow using AWS S3 data | Data integration, model training, performance evaluation |

Each stage builds toward a complete, production-ready hydrological modeling pipeline.

---

## Technology Stack  

| Category | Tools / Libraries | Purpose |
|-----------|-------------------|----------|
| **Deep Learning** | PyTorch 2.1.2, CUDA 12.1, cuDNN, cuBLAS, cuFFT | GPU-accelerated training and inference |
| **Data Science** | pandas 2.1.4, NumPy 1.26.3, scikit-learn 1.3.2 | Data manipulation, feature scaling, and preprocessing |
| **Hydrology Domain** | hydroeval 0.1.0, hydrotools-nwis-client 3.3.1, hydrotools-nwm-client 5.0.3 | Domain-specific data access and evaluation |
| **Cloud Integration** | boto3 1.34.18, fsspec, s3fs | AWS S3 authentication and data retrieval |
| **Visualization** | matplotlib 3.8.3, seaborn 0.13.2 | Performance metrics visualization |
| **Serialization** | h5py, PyTables, joblib | Model checkpoints and scaler persistence |

---

## Key Concepts  

### LSTM Architecture  
Defined in `LSTM.py`, the **Simple_LSTM** class supports configurable hidden units, stacking, bidirectionality, and feature input handling. Initialization uses `weight_init()` to improve training stability.

### Data Processing Pipeline  
Implemented in `dataprocessing.py`, this module:
- Retrieves data from AWS S3 using `boto3.Session`.  
- Applies feature scaling via `StandardScaler`.  
- Generates temporal sequences for univariate and multivariate time series.  
- Maintains chronological integrity during train/test splitting.  

### Hydrological Evaluation  
`evaluation.py` implements core performance metrics used in hydrology:
- **NSE (Nash–Sutcliffe Efficiency)** – predictive skill vs. mean baseline.  
- **KGE (Kling–Gupta Efficiency)** – correlation, bias, and variability combined.  
- **RMSE / MAPE / MaxError** – magnitude and relative error indicators.  

---

## Getting Started  

```bash
# 1. Clone the repository
git clone https://github.com/CIROH-UA/LSTM-Tutorials.git
cd LSTM-Tutorials

# 2. Create the environment
conda env create -f pytorch.yml
conda activate lstm-tutorials

# 3. (Optional) Configure AWS S3 access for cloud-hosted data
