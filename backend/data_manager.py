import os
import io
import pandas as pd
import numpy as np
from scipy.ndimage import uniform_filter1d
from PyQt5.QtCore import pyqtSignal, QObject

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
    