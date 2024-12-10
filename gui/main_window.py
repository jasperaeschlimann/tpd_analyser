from PyQt5.QtWidgets import (QMainWindow, QMdiArea)
from gui.data_loader_window import DataLoaderWindow
from gui.data_manager_window import DataManagerWindow
from gui.options_window import OptionsWindow
from gui.plot_window import PlotWindow

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

        # Create an MDI Area
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

        # Create the data loader and options pane windows
        self.create_data_loader_window()
        self.create_options_window()

    def create_options_window(self):
        """Creates the options pane."""
        self.options_window = OptionsWindow(self)
        self.mdi_area.addSubWindow(self.options_window)

        # Connect the signal from the options pane
        self.options_window.options_updated.connect(self.update_options)

    def update_options(self, slope_target, tolerance):
        """
        Updates options based on user inputs from the options pane.
        :param slope_target: Target slope for trimming.
        :param tolerance: Slope tolerance for trimming.
        :param show_legend: Whether to show legends in plots.
        """
        self.slope_target = slope_target
        self.tolerance = tolerance

        # Apply changes to trimming or re-plotting
        if hasattr(self, 'data_manager'):
            self.data_manager.trim_to_linear_region(
                target_slope=self.slope_target,
                tolerance=self.tolerance
            )

    def create_data_loader_window(self):
        """Creates a dockable widget for loading files and managing data."""
        self.data_loader_window = DataLoaderWindow(self)
        self.mdi_area.addSubWindow(self.data_loader_window)

    def create_data_manager_window(self):
        """
        """
        self.data_manager_window = DataManagerWindow(self.dataframes, self)
        self.mdi_area.addSubWindow(self.data_manager_window)
        self.data_manager_window.show()

    def plot_data(self, selected_files_and_dfs, dataframes, plot_type="Raw", include_legend=True):
        """
        Create a new PlotWindow for plotting selected DataFrames.

        :param selected_files_and_dfs: Dictionary with file names as keys and lists of selected DataFrame names as values.
        :param dataframes: Complete dictionary of DataFrames (raw or trimmed).
        :param plot_type: Indicates whether to plot raw or trimmed data.
        :param include_legend: Whether to include legends in the plot.
        """
        if not selected_files_and_dfs:
            print("No DataFrames selected for plotting.")
            return

        # Determine the data to plot (raw or trimmed)
        if plot_type == "Trimmed Data" and self.data_manager is not None:
            data_to_plot = self.data_manager.get_trimmed_dataframes()
        else:
            data_to_plot = dataframes

        # Create and show a PlotWindow
        plot_window = PlotWindow(
            self, selected_files_and_dfs, data_to_plot, plot_type, show_legend=include_legend
        )
        self.mdi_area.addSubWindow(plot_window)
        plot_window.show()
