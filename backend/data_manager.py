import os
import io
import pandas as pd
import numpy as np
from scipy.ndimage import uniform_filter1d

class DataManager:
    """
    Handles the logic for loading and managing data from files.
    """
    def __init__(self, file_paths=None):
        """
        Initializes the DataLoader with optional file paths.

        :param file_paths: List of file paths to process (default: None).
        """
        self.file_paths = file_paths or []
        self.dataframes = {}  # Dictionary to hold the loaded data
        self.trimmed_dataframes = {}  # Dictionary to hold trimmed data

    def extract_data_to_dataframes(self):
        """
        Processes the file paths to extract data and organize it into DataFrames.

        :return: A dictionary where keys are filenames and values are dictionaries of DataFrames.
        """

        for file_path in self.file_paths:
            # Extract the filename without the extension
            filename = os.path.splitext(os.path.basename(file_path))[0]

            # Read the file
            with open(file_path, 'r') as file:
                lines = file.readlines() # List of entries of lines of file with a \n inserted at the end

            # Extract the 7th line (index 6) for headers
            headers_line = lines[6].strip() # Removes white space, \t, \n etc at start and end of entry
            headers = [header.strip() for header in headers_line.split("\t") if header] 

            # Combine remaining lines into a single string and load into a DataFrame
            data_string = "\n".join(lines[7:]) # Combines all lines in list after headers line, with a single \n separating each line
            df = pd.read_csv(io.StringIO(data_string), delimiter="\t", header=None, engine="python") # Passes string as a file like object which is readable by pd.read_csv

            # Create a dictionary to hold DataFrames for this file
            file_dataframes = {}

            # Populate the dictionary with DataFrames dynamically linked to header keys
            for i, header in enumerate(headers): # For each header, and the index of the header
                start_col = i * 3
                end_col = start_col + 3
                subset_df = df.iloc[:, start_col:end_col] # Finds subset of dataframe corresponding to each header
                subset_df.columns = subset_df.iloc[0] # Sets column headers to the first row of the subset dataframes
                subset_df = subset_df[1:].reset_index(drop=True)
                dataframe_name = f"{filename}_{header}"
                file_dataframes[dataframe_name] = subset_df 

            # Store the file-specific dictionary in the main dictionary and linked by a filename key
            self.dataframes[filename] = file_dataframes

        return self.dataframes

    def trim_to_linear_region(self, target_slope=1.0, tolerance=0.3):
        """
        Smooths the temperature data, identifies the linear region with the desired gradient,
        and trims the original data accordingly.
        """
        for file_name, dataframes in self.dataframes.items():
            if file_name not in self.trimmed_dataframes:
                self.trimmed_dataframes[file_name] = {}

            # Identify the temperature DataFrame (assumed to be the last DataFrame)
            temp_df_name = list(dataframes.keys())[-1]
            temp_df = dataframes[temp_df_name]

            # Extract and clean relative time (column 2) and temperature (column 3)
            relative_time = temp_df.iloc[:, 1].str.replace(",", ".").astype(float)
            temperature = temp_df.iloc[:, 2].str.replace(",", ".").astype(float)

            # Apply box smoothing filter
            smoothed_temperature = uniform_filter1d(temperature, size=10)

            # Calculate the slope
            delta_temp = np.diff(smoothed_temperature)
            delta_time = np.diff(relative_time)
            slopes = delta_temp / delta_time
            slopes = np.insert(slopes, 0, np.nan)

            # Identify regions with the desired gradient
            within_gradient = np.abs(slopes - target_slope) <= tolerance

            # Find continuous regions meeting the criteria for at least 20 seconds
            min_duration = 20  # seconds
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
                print(f"No valid linear region found for {file_name}.")
                continue

            print(f"Linear region for {file_name}: Start {start_idx}, End {end_idx}")

            # Trim the original data based on the identified range
            for df_name, df in dataframes.items():
                trimmed_df = df.iloc[start_idx:end_idx + 1].reset_index(drop=True)
                self.trimmed_dataframes[file_name][df_name] = trimmed_df

    def get_trimmed_dataframes(self):
        """
        Returns the trimmed DataFrames.
        """
        return self.trimmed_dataframes
    