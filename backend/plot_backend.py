class PlotBackend1:
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

    def configure_axes(self, figure):
        """
        Configures the Matplotlib axes based on the selected data.
        
        :param figure: Matplotlib figure to which axes will be added
        :return: Tuple (ax_left, ax_right). ax_right is None for single-axis plots
        """
        # Check if ion current data is present
        include_ion_currents = any(
            df_name != list(self.dataframes[file_name].keys())[-1]
            for file_name, df_names in self.selected_files_and_dfs.items()
            for df_name in df_names
        )

        # Check if temperature data is present
        include_temperature = any(
            df_name == list(self.dataframes[file_name].keys())[-1]
            for file_name, df_names in self.selected_files_and_dfs.items()
            for df_name in df_names
        )

        # Configure axes based on available data
        if include_ion_currents and include_temperature:
            ax_left = figure.add_subplot(111)
            ax_right = ax_left.twinx() # Add second y axis
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
            
            # Skip if file is not found
            if file_name not in self.dataframes:
                continue

            file_dataframes = self.dataframes[file_name]
            temp_df_name = list(file_dataframes.keys())[-1] # Assume last DataFrame is temperature

            # Skip if DataFrame is not found
            for df_name in selected_df_names:
                if df_name not in file_dataframes:
                    continue 

                # Time data is assumed to be in the first column
                df = file_dataframes[df_name]
                relative_time = df.iloc[:, 0]

                # Plot ion current data on primary y-axis
                if df_name != temp_df_name:
                    ion_current = df.iloc[:, 1]
                    ax_left.plot(
                        relative_time,
                        ion_current,
                        label=f"{file_name} - {df_name} (Ion Current)"
                    )
                # Plot temperature data on secondary y-axis if available
                elif ax_right is not None:
                    temperature = df.iloc[:, 1]
                    ax_right.plot(
                        relative_time,
                        temperature,
                        label=f"{file_name} - Temperature",
                        linestyle="--"
                    )
                # Plot temperature data on primary y-axis if only a temperature DataFrame present and no secondary y-axis
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
        if ax_right:
            # Dual axes: Ion Currents on the left, Temperature on the right
            ax_left.set_title(f"Relative Time vs Ion Currents and Temperature ({self.plot_type})")
            ax_left.set_xlabel("Relative Time (s)")
            ax_left.set_ylabel("Ion Current (A)")
            ax_right.set_ylabel("Temperature (k)")

        else:
            # Single axis: Determine if it's Ion Currents or Temperature
            ax_left.set_xlabel("Relative Time (s)")

            # Determine y-axis label and title based on the type of data plotted
            contains_ion_current = any(
                df_name != list(self.dataframes[file_name].keys())[-1]  # Non-temperature DataFrame
                for file_name, df_names in self.selected_files_and_dfs.items()
                for df_name in df_names
            )
            if contains_ion_current:
                ax_left.set_ylabel("Ion Current (A)")
                ax_left.set_title(f"Relative Time vs Ion Current ({self.plot_type})")
            else:
                ax_left.set_ylabel("Temperature (K)")
                ax_left.set_title(f"Relative Time vs Temperature ({self.plot_type})")
        
        ax_left.grid(True)  # Enable grid for better readability

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
                    ax_left.plot(
                        temperature,
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
