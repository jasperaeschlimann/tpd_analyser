class PlotBackend:
    """
    Handles the logic for plotting data.
    """
    def __init__(self, dataframes, selected_files_and_dfs, plot_type="Raw", show_legend=True):
        self.dataframes = dataframes
        self.selected_files_and_dfs = selected_files_and_dfs
        self.plot_type = plot_type
        self.show_legend = show_legend

    def configure_axes(self, figure):
        """
        Configures the axes based on the selected data.
        :param figure: Matplotlib figure to which axes are added.
        :return: Tuple of (ax_left, ax_right) axes. ax_right is None for single-axis plots.
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

        if include_ion_currents and include_temperature:
            ax_left = figure.add_subplot(111)
            ax_right = ax_left.twinx()
            return ax_left, ax_right
        elif include_ion_currents:
            ax_left = figure.add_subplot(111)
            return ax_left, None
        elif include_temperature:
            ax_left = figure.add_subplot(111)
            return ax_left, None
        else:
            raise ValueError("No valid data to plot.")

    def plot_data(self, ax_left, ax_right=None):
        """
        Plots the data on the given axes.
        :param ax_left: Primary y-axis.
        :param ax_right: Secondary y-axis (for temperature), if applicable.
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
                relative_time = df.iloc[:, 1].str.replace(",", ".").astype(float)

                if df_name != temp_df_name:
                    ion_current = df.iloc[:, 2].str.replace(",", ".").astype(float)
                    ax_left.plot(
                        relative_time,
                        ion_current,
                        label=f"{file_name} - {df_name} (Ion Current)"
                    )
                elif ax_right is not None:
                    temperature = df.iloc[:, 2].str.replace(",", ".").astype(float)
                    ax_right.plot(
                        relative_time,
                        temperature,
                        label=f"{file_name} - Temperature",
                        linestyle="--"
                    )
                else:
                    temperature = df.iloc[:, 2].str.replace(",", ".").astype(float)
                    ax_left.plot(
                        relative_time,
                        temperature,
                        label=f"{file_name} - Temperature",
                        linestyle="--"
                    )

        # Customize axes
        self._customize_axes(ax_left, ax_right)

    def _customize_axes(self, ax_left, ax_right):
        """
        Customizes the axes appearance and adds legends.
        """
        if ax_right:
            # Dual axes: Ion Currents on the left, Temperature on the right
            ax_left.set_title(f"Relative Time vs Ion Currents and Temperature ({self.plot_type})")
            ax_left.set_xlabel("Relative Time (s)")
            ax_left.set_ylabel("Ion Current", color="blue")
            ax_right.set_ylabel("Temperature", color="red")
            ax_left.grid(True)

            if self.show_legend:
                ax_left.legend(loc="upper left")
                ax_right.legend(loc="upper right")
        else:
            # Single axis: Determine if it's Ion Currents or Temperature
            ax_left.set_title(f"Relative Time ({self.plot_type})")
            ax_left.set_xlabel("Relative Time (s)")

            # Determine which y-axis label to use based on plotted data
            if any(
                df_name != list(self.dataframes[file_name].keys())[-1]  # Not temperature DataFrame
                for file_name, df_names in self.selected_files_and_dfs.items()
                for df_name in df_names
            ):
                ax_left.set_ylabel("Ion Current", color="blue")
            else:
                ax_left.set_ylabel("Temperature", color="red")

            ax_left.grid(True)

            if self.show_legend:
                ax_left.legend(loc="upper left")

