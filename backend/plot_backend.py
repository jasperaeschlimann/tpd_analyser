from scipy.ndimage import uniform_filter1d

class PlotBackend:
    """
    Handles data plotting logic, configuring axes and rendering selected DataFrames.
    """
    def __init__(self, dataframes, selected_files_and_dfs, plot_type="Raw"):
        """
        Initialises the PlotBackend.
        
        :param dataframes: Dictionary containing loaded files and their corresponding DataFrames
        :param selected_files_and_dfs: Mapping of selected files to chosen DataFrame names
        :param plot_type: Type of plot to generate (e.g., "Raw", "Trimmed Data - Time", "Trimmed Data - Temperature")
        """
        self.dataframes = dataframes
        self.selected_files_and_dfs = selected_files_and_dfs
        self.plot_type = plot_type
        self.smoothing_window = 1

    def configure_axes(self, figure):
        """
        Configures the Matplotlib axes based on the selected data.
        
        :param figure: Matplotlib figure to which axes will be added
        :return: Tuple (ax_left, ax_right). ax_right is None for single-axis plots
        """
        include_ion_currents = any(
            df_name != list(self.dataframes[file_name].keys())[-1]
            for file_name, df_names in self.selected_files_and_dfs.items()
            for df_name in df_names
        )

        include_temperature = any(
            df_name == list(self.dataframes[file_name].keys())[-1]
            for file_name, df_names in self.selected_files_and_dfs.items()
            for df_name in df_names
        )

        if self.plot_type == "Trimmed Data - Temperature":
            ax_x = figure.add_subplot(111)
            return ax_x, None
        
        if include_ion_currents and include_temperature:
            ax_left = figure.add_subplot(111)
            ax_right = ax_left.twinx()
            return ax_left, ax_right
        elif include_ion_currents or include_temperature:
            ax_left = figure.add_subplot(111)
            return ax_left, None
        else:
            raise ValueError("No valid data to plot.")
    
    def plot_data(self, ax_left, ax_right=None):
        """
        Plots data on the given axes.
        
        :param ax_left: Primary y-axis for Ion Current data
        :param ax_right: Secondary y-axis for Temperature data (if applicable)
        """
        for file_name, selected_df_names in self.selected_files_and_dfs.items():
            if file_name not in self.dataframes:
                continue

            file_dataframes = self.dataframes[file_name]
            temp_df_name = list(file_dataframes.keys())[-1]

            for df_name in selected_df_names:
                if df_name not in file_dataframes:
                    continue 

                df = file_dataframes[df_name]
                relative_time = df.iloc[:, 0]

                # Ignore plotting Temperature vs. Temperature
                if self.plot_type == "Trimmed Data - Temperature" and df_name == temp_df_name:
                    print(f"Skipping Temperature vs. Temperature plot for {file_name}")
                    continue  # Skip this iteration

                if self.plot_type == "Trimmed Data - Temperature":
                    if temp_df_name not in file_dataframes:
                        continue

                    temp_df = file_dataframes[temp_df_name]
                    temperature = temp_df.iloc[:, 1]
                    ion_current = df.iloc[:, 1]
                    
                    # Apply Smoothing to Temperature Data
                    smoothed_temperature = uniform_filter1d(temperature, size=self.smoothing_window)
                    
                    ax_left.plot(
                        smoothed_temperature,
                        ion_current,
                        label=f"{file_name} - {df_name} vs Temperature"
                    )
                else:
                    if df_name != temp_df_name:
                        ion_current = df.iloc[:, 1]
                        ax_left.plot(
                            relative_time,
                            ion_current,
                            label=f"{file_name} - {df_name} (Ion Current)"
                        )
                    elif ax_right is not None:
                        temperature = df.iloc[:, 1]
                        ax_right.plot(
                            relative_time,
                            temperature,
                            label=f"{file_name} - Temperature",
                            linestyle="--"
                        )
                    else:
                        temperature = df.iloc[:, 1]
                        ax_left.plot(
                            relative_time,
                            temperature,
                            label=f"{file_name} - Temperature",
                            linestyle="--"
                        )

        # Customize axes appearance
        self._customize_axes(ax_left, ax_right)
    
    def _customize_axes(self, ax_left, ax_right):
        """
        Customises axis labels, grid, and titles based on the plotted data.
        
        :param ax_left: Primary y-axis
        :param ax_right: Secondary y-axis (if applicable)
        """
        if self.plot_type == "Trimmed Data - Temperature":
            ax_left.set_xlabel("Temperature (K)")
            ax_left.set_ylabel("Ion Current (A)")
            ax_left.set_title(f"Ion Current vs Temperature ({self.plot_type})")
        else:
            if ax_right:
                ax_left.set_title(f"Ion Currents and Temperature vs Relative Time ({self.plot_type})")
                ax_left.set_xlabel("Relative Time (s)")
                ax_left.set_ylabel("Ion Current (A)")
                ax_right.set_ylabel("Temperature (K)")
            else:
                ax_left.set_xlabel("Relative Time (s)")
                contains_ion_current = any(
                    df_name != list(self.dataframes[file_name].keys())[-1]
                    for file_name, df_names in self.selected_files_and_dfs.items()
                    for df_name in df_names
                )
                if contains_ion_current:
                    ax_left.set_ylabel("Ion Current (A)")
                    ax_left.set_title(f"Ion Current vs Relative Time ({self.plot_type})")
                else:
                    ax_left.set_ylabel("Temperature (K)")
                    ax_left.set_title(f"Temperature vs Relative Time ({self.plot_type})")
        ax_left.grid(True)
