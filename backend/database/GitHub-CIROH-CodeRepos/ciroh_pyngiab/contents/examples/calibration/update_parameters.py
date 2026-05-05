import os



def update_cfe_parameters(directory, parameters):
    """
    Updates specific parameters in all files within a directory.

    Parameters:
    - directory (str): Path to the directory containing the files to update.
    - parameters (dict): Dictionary of parameters and their new values.
    
    Example:
    parameters = {
        "max_gw_storage": "0.1[m]",
        "Cgw": "0.0018[m h-1]",
        "expon": "1.0[]",
        "gw_storage": "0.1[m/m]",
        "alpha_fc": "0.33",
        "soil_storage": "0.1[m/m]",
        "K_nash": "0.03[]",
        "K_lf": "0.01[]"
    }
    """
    # Ensure the directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    # Loop through all files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories
        if not os.path.isfile(file_path):
            continue

        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Update the parameters
        updated_lines = []
        for line in lines:
            for key, new_value in parameters.items():
                if line.startswith(key + "="):
                    line = f"{key}={new_value}\n"
            updated_lines.append(line)

        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.writelines(updated_lines)

    print(f"Parameters updated in all files within '{directory}'.")



def update_noah_parameters(file_path, param_updates):
    """
    Update selected NOAH LSM parameters in the MPTABLE.TBL file.
    
    Parameters:
        directory_path (str): Path to the 'noah_om/parameters' directory.
        param_updates (dict): Keys are parameter names (e.g., 'MFSNO'), values are strings to insert.
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"MPTABLE.TBL not found at {file_path}")
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        print(f"Updating parameters in {file_path}...")
    
    is27 = True
    for key, value in param_updates.items():
        if key == 'MFSNO': 
            MFSNO27_str      = ', '.join([f'{value}'] * 27)
            MFSNO20_str      = ',   '.join([f'{value}'] * 19)
            lines[220] = f" {key} =  {value},   {MFSNO20_str},\n"
            
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}"):
                if key== 'MFSNO' and is27:
                    lines[i] = f" {key} =  {MFSNO27_str},\n"
                    is27 = False
                else:
                    lines[i] = f"  {key} = {value}\n"
                break
    
    with open(file_path, 'w') as file:
        file.writelines(lines)




if __name__ == "__main__":
    # Example usage
    default_parameters = {
        "soil_params.depth": "2.0[m]",
        "refkdt": "3.0[]",
        "max_gw_storage": "0.1[m]",
        "Cgw": "0.0010[m h-1]", # 0.0018
        "expon": "1.1[]", #6
        "gw_storage": "0.1[m/m]",
        "alpha_fc": "0.33[]",
        "soil_storage": "0.2[m/m]",
        "K_nash": "0.03[]",
        "K_lf": "0.01[]"
    }

    # *** Final SPOTPY summary ***
    # soil_params_depth: 2.48774
    # refkdt: 4.80965
    # max_gw_storage: 0.124376
    # Cgw: 0.00309729
    # expon: 3.94675
    # gw_storage: 0.233448
    # alpha_fc: 0.11962
    # soil_storage: 0.123554
    # K_nash: 0.0550566
    # K_lf: 0.0114604
    # MFSNO: 1.55732
    # Z0SNO: 0.00949403
    # SNOW_EMIS: 0.98235

    # set spotpy parameters as     
    cfe_spotpy_parameters = {
        "soil_params.depth": "2.48774[m]",
        "refkdt": "4.80965[]",
        "max_gw_storage": "0.124376[m]",
        "Cgw": "0.00309729[m h-1]",
        "expon": "3.94675[]",
        "gw_storage": "0.233448[m/m]",
        "alpha_fc": "0.11962[]",
        "soil_storage": "0.123554[m/m]",
        "K_nash": "0.0550566[]",
        "K_lf": "0.0114604[]"
    }

    # New Noah LSM parameter updates using
    noah_param_updates = {
        'MFSNO': f'{0.5:.2f}',
        'Z0SNO': f'  { 0.01:.6f}        !snow surface roughness length (m)',
        'SNOW_EMIS': f' {0.96:.2f}  !snow emissivity (brought from hard-coded value of 1.0)'
    }

    gage_id = "09081600"

    noah_directory = f'inputs/settings/{gage_id}'
    update_noah_parameters(noah_directory, noah_param_updates)

    cfe_directory = f'inputs/settings/{gage_id}/cfe'
    update_cfe_parameters(cfe_directory, cfe_spotpy_parameters)


    # Example usage
    #generate_parameter_files("09081600", "201810010000", "201909300000")
    #generate_init_files("09081600", "201810010000", "201909300000")

