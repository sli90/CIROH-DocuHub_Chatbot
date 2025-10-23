# Project Title: **bmi-burn-lstm**

## Project Objective  
**bmi-burn-lstm** is a Rust implementation of a **Basic Model Interface (BMI)** adapter for LSTM-based streamflow prediction.  
It provides a drop-in replacement for Python BMI LSTM implementations found in repositories such as [CIROH-UA/lstm](https://github.com/CIROH-UA/lstm), [NOAA-OWP/lstm](https://github.com/NOAA-OWP/lstm), and [jmframe/lstm](https://github.com/jmframe/lstm).

## Core Functionalities  
- Native Rust implementation using the [Burn](https://burn.dev/) deep learning framework.  
- Compatible with existing PyTorch model weights from `jmframe/lstm` and **NextGen-In-A-Box**.  
- Drop-in replacement for Python BMI LSTM adapter.  
- Supports ensemble model configurations.  
- Built on [bmi-rs](https://github.com/aaraney/bmi-rs) Rust BMI bindings.  
- Outputs match those of the Python BMI LSTM implementation.  

## Technical Stack  
- **Language:** Rust (2024 edition).  
- **Deep Learning Framework:** Burn.  
- **Bindings:** bmi-rs (Rust BMI bindings).  
- **Dependencies:**  
  - Rust 2024 edition.  
  - Local clone of [bmi-rs](https://github.com/aaraney/bmi-rs).  
  - [Astral UV](https://docs.astral.sh/uv/) installed and available on system path.  
- **Development Status:** Active development.  

## Setup and Usage  
1. **Install Dependencies:**  
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   curl https://sh.rustup.rs -sSf | bash -s -- -y && . "$HOME/.cargo/env"
   ```  
2. **Clone Required Repositories:**  
   ```bash
   git clone https://github.com/aaraney/bmi-rs
   git clone https://github.com/ciroh-ua/bmi-burn-lstm
   ```  
3. **Build Project:**  
   ```bash
   cd bmi-burn-lstm
   cargo build --release
   ```  
   The compiled shared object is located at:  
   `target/release/libbmi_burn_lstm.so`  

## Model Compatibility  
- Trained models from `jmframe/lstm`.  
- Models included in **NextGen-In-A-Box**.  
- Any PyTorch LSTM model following the **neuralhydrology** architecture (`1 layer LSTM + 1 linear layer`).  
- Automatic weight conversion from PyTorch to Burn format on first run.  

## NextGen Realization Example  
Example configuration for integrating this model with NextGen:  
```json
{
  "global": {
    "formulations": [
      {
        "name": "bmi_multi",
        "params": {
          "name": "bmi_multi",
          "model_type_name": "lstm",
          "forcing_file": "",
          "init_config": "",
          "allow_exceed_end_time": true,
          "main_output_variable": "land_surface_water__runoff_depth",
          "modules": [
            {
              "name": "bmi_c",
              "params": {
                "name": "bmi_c",
                "model_type_name": "bmi_rust",
                "init_config": "./config/cat_config/lstm/{{id}}.yml",
                "allow_exceed_end_time": true,
                "main_output_variable": "land_surface_water__runoff_depth",
                "uses_forcing_file": false,
                "registration_function": "register_bmi_lstm",
                "library_file": "/dmod/shared_libs/libbmi_burn_lstm.so"
              }
            }
          ]
        }
      }
    ],
    "forcing": {
      "path": "./forcings/forcings.nc",
      "provider": "NetCDF",
      "enable_cache": false
    }
  },
  "time": {
    "start_time": "2010-01-01 00:00:00",
    "end_time": "2011-01-01 00:00:00",
    "output_interval": 3600
  },
  "routing": {
    "t_route_config_file_with_path": "./config/troute.yaml"
  },
  "remotes_enabled": false,
  "output_root": "./outputs/ngen"
}
```

## NGIAB Patch Example  
Example Dockerfile for integrating the adapter into NextGen-In-A-Box:  
```Dockerfile
FROM awiciroh/ciroh-ngen-image AS build
RUN dnf install -y gcc clang git
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
RUN echo 'source $HOME/.cargo/env' >> $HOME/.bashrc
WORKDIR /build
RUN git clone https://github.com/aaraney/bmi-rs
RUN git clone https://github.com/ciroh-ua/bmi-burn-lstm
WORKDIR /build/bmi-burn-lstm
RUN cargo build --release

FROM awiciroh/ciroh-ngen-image AS final
COPY --from=build /build/bmi-burn-lstm/target/release/libbmi_burn_lstm.so /dmod/shared_libs/libbmi_burn_lstm.so
```
Build command:  
```bash
docker build -t ngiab -f Dockerfile .
```

## Project Context & Domain  
- **Domain:** Hydrology / Streamflow prediction / Model integration.  
- **Affiliation:** Not specified.  
- **Purpose:** Provide a faster Rust-based BMI adapter for LSTM hydrologic models.  

## Input / Output  
**Input:**  
- Trained PyTorch LSTM model weights.  
- NextGen configuration files for model integration.  
- Forcing and initialization data defined in configuration.  

**Output:**  
- Rust-based shared object file (`libbmi_burn_lstm.so`).  
- Model outputs consistent with the Python BMI LSTM implementation.  

## License  
License information: Not specified.  
