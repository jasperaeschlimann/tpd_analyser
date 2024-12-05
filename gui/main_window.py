from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, 
    QMdiArea, QMdiSubWindow
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from gui.data_loader_window import DataLoaderWindow
from gui.data_manager_window import DataManagerWindow
from gui.options_window import OptionsWindow

class MainWindow(QMainWindow):
    """
    Main application window.
    """
    def __init__(self):
        super().__init__()

        # Set the main window's properties
        self.setWindowTitle("TPD_Analyser")
        self.setGeometry(50, 50, 1600, 900)

        # List to store loaded file paths
        self.loaded_files = []
        self.dataframes = []

        # Placeholders for Matplotlib canvas and toolbar
        self.plot_canvas = None
        self.toolbar = None
        self.show_legend = True

        # Create an MDI Area
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

        # Create the data loader and options pane windows
        self.create_data_loader()
        self.create_options_pane()

    def create_options_pane(self):
        """Creates the options pane."""
        self.options_window = OptionsWindow(self)
        self.mdi_area.addSubWindow(self.options_window)

        # Connect the signal from the options pane
        self.options_window.options_updated.connect(self.update_options)

    def update_options(self, slope_target, tolerance, show_legend):
        """
        Updates options based on user inputs from the options pane.
        :param slope_target: Target slope for trimming.
        :param tolerance: Slope tolerance for trimming.
        :param show_legend: Whether to show legends in plots.
        """
        self.slope_target = slope_target
        self.tolerance = tolerance

        # Apply changes to trimming or re-plotting
        if hasattr(self, 'data_loader'):
            self.data_loader.trim_to_linear_region(
                target_slope=self.slope_target,
                tolerance=self.tolerance
            )

        # Update plot to reflect the legend change if necessary
        if self.show_legend != show_legend:
            self.show_legend = show_legend
            self.update_plot_legend()

    def create_data_loader(self):
        """Creates a dockable widget for loading files and managing data."""
        self.data_loader_window = DataLoaderWindow(self)
        self.mdi_area.addSubWindow(self.data_loader_window)

    def create_data_manager(self):
        """
        """
        self.data_manager = DataManagerWindow(self.dataframes, self)
        self.mdi_area.addSubWindow(self.data_manager)
        self.data_manager.show()

    def plot_data(self, selected_files, dataframes, plot_type="Raw"):
        """
        Plots the selected dataframes in the main area with a navigation toolbar.

        :param selected_files: List of selected file names.
        :param dataframes: Dictionary of dataframes (raw or trimmed).
        :param plot_type: "Raw" for raw data, "Trimmed" for trimmed data.
        """
        if not selected_files:
            print("No files selected for plotting.")
            return

        # Use raw or trimmed data
        if plot_type == "Trimmed Data":
            print("Accessing trimmed data...")  # Debugging statement
            dataframes = self.data_loader.get_trimmed_dataframes()
            print(f"Trimmed data available: {dataframes}")  # Debugging statement

        # Create a new Matplotlib figure and canvas
        figure = Figure()
        self.plot_canvas = FigureCanvas(figure)
        ax_left = figure.add_subplot(111)
        ax_right = ax_left.twinx()  # Secondary y-axis for temperature

        # Plot data
        for file_name in selected_files:
            file_dataframes = dataframes[file_name]

            # Plot ion currents
            for df_name, df in list(file_dataframes.items())[:-1]:
                relative_time = df.iloc[:, 1].str.replace(",", ".").astype(float)
                ion_current = df.iloc[:, 2].str.replace(",", ".").astype(float)
                ax_left.plot(
                    relative_time,
                    ion_current,
                    label=f"{file_name} - {df_name} (Ion Current)"
                )

            # Plot temperature (last DataFrame)
            temp_df = list(file_dataframes.values())[-1]
            relative_time = temp_df.iloc[:, 1].str.replace(",", ".").astype(float)
            temperature = temp_df.iloc[:, 2].str.replace(",", ".").astype(float)
            ax_right.plot(
                relative_time,
                temperature,
                label=f"{file_name} - Temperature",
                linestyle="--"
            )

        # Customize the axes
        ax_left.set_title(f"Relative Time vs Ion Currents and Temperature ({plot_type} Data)")
        ax_left.set_xlabel("Relative Time (s)")
        ax_left.set_ylabel("Ion Current", color="blue")
        ax_right.set_ylabel("Temperature", color="red")
        if self.show_legend:
            ax_left.legend(loc="upper left")
            ax_right.legend(loc="upper right")
        ax_left.grid(True)

        # Add the Matplotlib canvas and toolbar to the main area
        plot_widget = QWidget()
        layout = QVBoxLayout(plot_widget)
        layout.addWidget(self.plot_canvas)

        # Add a navigation toolbar
        self.toolbar = NavigationToolbar(self.plot_canvas, self)
        layout.addWidget(self.toolbar)

        # Set the central widget
        self.plot_window = QMdiSubWindow()
        self.plot_window.setWidget(plot_widget)
        self.mdi_area.addSubWindow(self.plot_window)

        # Show the plot window
        self.plot_window.show()

        # Draw the canvas
        self.plot_canvas.draw()

        # Debug: Check what data is being plotted
        for file_name in selected_files:
            print(f"Plotting data for {file_name} ({plot_type}):")

    def update_plot_legend(self):
        """Update the visibility of the legend in the current plot."""
        if self.plot_canvas:
            ax_left = self.plot_canvas.figure.axes[0]  # Left axis (primary)
            ax_right = self.plot_canvas.figure.axes[1]  # Right axis (secondary)

        if self.show_legend:
            ax_left.legend(loc="upper left")
            ax_right.legend(loc="upper right")
        else:
            ax_left.legend_.remove()
            ax_right.legend_.remove()

        self.plot_canvas.draw()

