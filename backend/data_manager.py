import os
import io
import re
import pandas as pd
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.integrate import simps
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox

class DataManager(QObject):
    """
    Handles the logic for loading and managing data from files.
    """
    # Signal to notify that data processing is complete
    data_processed = pyqtSignal()

    def __init__(self):
        """
        Initialises the DataManager with placeholders for data storage.
        """
        super().__init__()

        # Data placeholders
        self.file_paths =  [] # List of loaded file paths
        self.dataframes = {}  # Dictionary containing extracted data
        self.trimmed_dataframes = {}  # Dictionary for trimmed data
        self.trim_regions = {}  # Dictionary to store trimming regions {file_name: (start, end)}


    def set_files(self, loaded_file_paths):
        """
        Receives file paths and starts processing.

        :param loaded_file_paths: List of user-loaded files
        """
        self.file_paths = loaded_file_paths
        self._extract_data_to_dataframes()
        self.data_processed.emit() # Emit signal once processing is done

    def _extract_data_to_dataframes(self):
        """
        Extracts data from each file and organises it into a nested dictionary 
        where each filename maps to multiple DataFrames (one per header).        
        """
        for file_path in self.file_paths:
            filename = os.path.splitext(os.path.basename(file_path))[0]

            # Read the file into a list of lines
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # Extract headers from the 7th line (e.g. ion name, temperature, etc.)
            headers_line = lines[6].strip() 
            headers = [header.strip() for header in headers_line.split("\t") if header]

            # Convert the remaining lines in a DataFrame
            data_string = "\n".join(lines[7:-1]) # Join lines after header
            df = pd.read_csv(io.StringIO(data_string), delimiter="\t", header=None, engine="python")

            # Store extracted DataFrames per header in a file dictionary
            file_dataframes = {}
            for i, header in enumerate(headers):
                start_col, end_col = (i * 3) + 1, (i + 1) * 3
                subset_df = df.iloc[:, start_col:end_col] # Extract relevant columns
                subset_df.columns = subset_df.iloc[0] # Set first row as column names
                subset_df = subset_df[1:].reset_index(drop=True) # Remove the header row

                subset_df = subset_df.applymap(lambda x: str(x).replace(",", ".") if isinstance(x, str) else x)
                subset_df = subset_df.astype(float)
                
                # Store DataFrame with a dynamic name combining filename and header
                file_dataframes[f"{filename}_{header}"] = subset_df 

            # Store per-file dictionary
            self.dataframes[filename] = file_dataframes

    def trim_to_linear_region(self, target_slope, tolerance, smoothing_enabled, smoothing_window):
        """
        Identifies the linear region with a desired gradient in temperature data and trims accordingly.

        :param target_slope: Expected slope of the linear region
        :param tolerance: Allowable deviation from the target slope
        :param smoothing_enabled: Whether to apply smoothing before gradient calculation
        :param smoothing_window: Window size for smoothing filter
        """
        self.slope_target = target_slope
        self.tolerance = tolerance
        self.smoothing_enabled = smoothing_enabled
        self.smoothing_window = smoothing_window
        
        for file_name, dataframes in self.dataframes.items():
            if file_name not in self.trimmed_dataframes:
                self.trimmed_dataframes[file_name] = {}

            # Identify the temperature DataFrame (assumed to be the last DataFrame)
            temp_df_name = list(dataframes.keys())[-1]
            temp_df = dataframes[temp_df_name]

            # Extract time and temperature columns            
            relative_time = temp_df.iloc[:, 0]
            temperature = temp_df.iloc[:, 1]

            # Apply smoothing if enabled
            if smoothing_enabled:
                temperature = uniform_filter1d(temperature, size=smoothing_window)

            # Calculate the slope
            delta_temp = np.diff(temperature)
            delta_time = np.diff(relative_time)
            slopes = delta_temp / delta_time
            slopes = np.insert(slopes, 0, np.nan)

            # Identify regions with the desired gradient
            within_gradient = np.abs(slopes - target_slope) <= tolerance

            # Locate first valid continuous region of at least 20 seconds
            min_duration = 20  
            start_idx, end_idx = None, None
            current_start = None

            for i in range(len(within_gradient)):
                if within_gradient[i]:
                    if current_start is None:
                        current_start = i
                else:
                    if current_start is not None:
                        # Check if the region duration is at least 20 seconds
                        if relative_time[i - 1] - relative_time[current_start] >= min_duration:
                            start_idx = current_start
                            end_idx = i - 1
                            break
                        current_start = None

            if start_idx is None or end_idx is None:
                self.trim_regions[file_name] = None  # Store None for later reference
                continue

            # Store trimming boundaries
            trim_start_time = relative_time.iloc[start_idx]
            trim_end_time = relative_time.iloc[end_idx]
            self.trim_regions[file_name] = (trim_start_time, trim_end_time)

            # Trim and store DataFrames based on identified region
            for df_name, df in dataframes.items():
                trimmed_df = df.iloc[start_idx:end_idx + 1].reset_index(drop=True)
                self.trimmed_dataframes[file_name][df_name] = trimmed_df
            
            self.apply_trim_boundaries(file_name, trim_start_time, trim_end_time)

    def apply_trim_boundaries(self, file_name, trim_start_time, trim_end_time):
        """
        Applies trimming to all DataFrames for a given file based on start and end time.

        :param file_name: Name of the file to trim
        :param trim_start_time: The start time for trimming
        :param trim_end_time: The end time for trimming
        """
        if file_name not in self.dataframes:
            return

        # Ensure `trimmed_dataframes` exists
        if file_name not in self.trimmed_dataframes:
            self.trimmed_dataframes[file_name] = {}

        # Store updated trim boundaries
        self.trim_regions[file_name] = (trim_start_time, trim_end_time)

        # Use the temperature dataframe as the reference for trimming
        reference_df_name = next((df_name for df_name in self.dataframes[file_name] if "Temp" in df_name), None)  
        if reference_df_name is None:
            reference_df_name = list(self.dataframes[file_name].keys())[0]  # Use the first dataframe
        reference_df = self.dataframes[file_name][reference_df_name]
        
        # Find indices where time is within the trim boundaries
        valid_indices = reference_df[(reference_df.iloc[:, 0] >= trim_start_time) & 
                                    (reference_df.iloc[:, 0] <= trim_end_time)].index

        if valid_indices.empty:
            return

        # Apply trimming based on these indices
        for df_name, df in self.dataframes[file_name].items():
            df = df.loc[df.index.intersection(valid_indices)].reset_index(drop=True)
            self.trimmed_dataframes[file_name][df_name] = df

    def get_trim_boundaries(self, file_name):
        """
        Returns the trimming boundaries (start, end) for a given file if they exist.
        
        :param file_name: Name of the file
        :return: Tuple (trim_start, trim_end) or None if no trimming exists
        """
        return self.trim_regions.get(file_name, None)
    
    def extract_dosage_from_filename(self, file_name):
        """
        Extracts dosage value from a filename in the format 'Xe_5K_1' or 'Xe_5k_1'.

        :param file_name: The name of the file.
        :return: The extracted dosage as an integer, or None if extraction fails.
        """
        # Ensure we start matching after the first '_'
        match = re.search(r"(\d{1,3}[.,]?\d*)[kK]_", file_name.split("_", 1)[-1]) 

        if match:
            dosage_str = match.group(1).replace(",", ".")  # Convert ',' to '.'
            try:
                return float(dosage_str)  # Return as float
            except ValueError:
                return None  # If conversion fails, return None

        return None  # No match found

    def perform_full_integration(self, selected_files_and_dfs, smoothing_window):
        """
        Performs full integration of ion current over the entire trimmed temperature range,
        but only for the selected files and DataFrames.

        - Applies a smoothing filter before integration.
        - Uses Simpson's rule for numerical integration.
        - Extracts dosage from the filename.
        - Ensures the temperature DataFrame is used even if not explicitly selected.

        :param selected_files_and_dfs: Dictionary containing selected files and their chosen DataFrame names.
        :return: Dictionary mapping dosage values to integrated values.
        """
        integration_results = {}  # Store dictionary {dosage: integrated_value}

        for file_name, selected_df_names in selected_files_and_dfs.items():
            dosage = self.extract_dosage_from_filename(file_name)  # Use new function
            if dosage is None:
                QMessageBox.warning(None, "Extraction Error", f"Warning: Unable to extract dosage from {file_name}")
                continue

            # Find temperature DataFrame (assumed to be the last DataFrame)
            temp_df_name = next((df_name for df_name in self.trimmed_dataframes[file_name] if "Temp" in df_name), None)
            if temp_df_name is None:
                continue  # Skip if no temperature DataFrame exists

            temp_df = self.trimmed_dataframes[file_name][temp_df_name]
            temperature = temp_df.iloc[:, 1].to_numpy()  # Temperature values

            # Apply smoothing filter
            smoothed_temperature = uniform_filter1d(temperature, size=smoothing_window)

            # Sum the integration from all selected ion current DataFrames
            total_integrated_value = 0

            for df_name in selected_df_names:
                if df_name == temp_df_name:  # Ignore temperature DataFrame itself
                    continue

                ion_current = self.trimmed_dataframes[file_name][df_name].iloc[:, 1].to_numpy()  # Ion current values

                # Perform full integration over the entire trimmed temperature range
                integrated_value = simps(ion_current, smoothed_temperature)

                total_integrated_value += integrated_value

            # Store the total integration result
            integration_results[dosage] = total_integrated_value

        return integration_results

    def perform_ratio_integration(self, selected_files_and_dfs, smoothing_window, integration_boundaries):
        """
        Performs integration of ion current over the selected temperature range.

        :param selected_files_and_dfs: Dictionary containing selected files and their chosen DataFrame names.
        :param smoothing_window: Window size for 1D smoothing filter.
        :param integration_boundaries: Tuple (left_start_temp, left_end_temp, right_start_temp, right_end_temp).
        :return: Dictionary mapping file names to integration ratios.
        """
        left_start_temp, left_end_temp, right_start_temp, right_end_temp = integration_boundaries

        integration_ratios = {}  # Store ratio of left/right integration for each file

        for file_name, selected_df_names in selected_files_and_dfs.items():
            dosage = self.extract_dosage_from_filename(file_name)  # Use new function
            if dosage is None:
                QMessageBox.warning(None, "Extraction Error", f"Warning: Unable to extract dosage from {file_name}")
                continue
            
            # Find temperature DataFrame (assumed to be the last DataFrame)
            temp_df_name = next((df_name for df_name in self.trimmed_dataframes[file_name] if "Temp" in df_name), None)
            if temp_df_name is None:
                continue  # Skip if no temperature DataFrame exists

            # Extract temperature DataFrame
            temp_df = self.trimmed_dataframes[file_name][temp_df_name]
            temperature = temp_df.iloc[:, 1].to_numpy()  

            # Smooth the temperature data
            smoothed_temperature = uniform_filter1d(temperature, size=smoothing_window)

            for df_name in selected_df_names:
                if df_name == temp_df_name:
                    continue  # Skip temperature DataFrame

                if df_name not in self.trimmed_dataframes[file_name]:
                    continue  # Skip missing data

                # Extract ion current values
                ion_current = self.trimmed_dataframes[file_name][df_name].iloc[:, 1].to_numpy()

                # Filter the data for left integration region
                left_mask = (smoothed_temperature >= left_start_temp) & (smoothed_temperature <= left_end_temp)
                left_temp_filtered = smoothed_temperature[left_mask]
                left_ion_filtered = ion_current[left_mask]

                # Filter the data for right integration region
                right_mask = (smoothed_temperature >= right_start_temp) & (smoothed_temperature <= right_end_temp)
                right_temp_filtered = smoothed_temperature[right_mask]
                right_ion_filtered = ion_current[right_mask]

                if len(left_temp_filtered) == 0 or len(right_temp_filtered) == 0:
                    continue  # Avoid integration if no data is within bounds

                # Perform integration using Simpson's Rule
                left_integral = simps(left_ion_filtered, left_temp_filtered)
                right_integral = simps(right_ion_filtered, right_temp_filtered)

                # Compute ratio of left to right integration
                ratio = left_integral / right_integral if right_integral != 0 else np.nan

                # Store result
                integration_ratios[dosage] = ratio

        return integration_ratios


