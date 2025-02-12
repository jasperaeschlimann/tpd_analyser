from PyQt5.QtWidgets import (QMainWindow, QMessageBox)
from PyQt5.QtGui import QIcon
from gui.data_loader_window import DataLoaderWindow
from gui.data_manager_window import DataManagerWindow
from gui.trimming_options_window import TrimmingOptionsWindow
from gui.plot_window import PlotWindow
from backend.asc_to_txt_converter import FileConverter
from PyQt5 import uic

class MainWindow(QMainWindow):
    """
    Main application window with an MDI area for holding all other windows. Also contains a taskbar for menu options.
    """
    def __init__(self):
        # Call QMainWindow constructor
        super().__init__()

        #Load main window UI file
        uic.loadUi("gui/main_window.ui", self)

        #Set window and menu icons
        self.setWindowIcon(QIcon("resources/icons/TPD.ico"))
        self.actionNew.setIcon(QIcon("resources/icons/new.png"))
        self.actionOpen.setIcon(QIcon("resources/icons/open.png"))
        self.actionSave_As.setIcon(QIcon("resources/icons/save.png"))
        self.actionUndo.setIcon(QIcon("resources/icons/undo.png"))
        self.actionRedo.setIcon(QIcon("resources/icons/redo.png"))
        self.actionConvert_asc_to_txt.setIcon(QIcon("resources/icons/convert.png"))

        # Initialize the File Converter
        self.file_converter = FileConverter(self)

        # Connect "Convert .asc to .txt" action
        self.actionConvert_asc_to_txt.triggered.connect(self.file_converter.convert_asc_to_txt)

        # List to store loaded file paths
        self.loaded_files = []
        self.dataframes = []

        # Placeholders for Matplotlib canvas and toolbar
        self.plot_canvas = None
        self.toolbar = None

        # Create the data loader and options pane windows
        self.create_data_loader_window()

    def create_trimming_options_window(self):
        """Creates the trimming options window."""
        self.options_window = TrimmingOptionsWindow(self)
        self.mdiArea.addSubWindow(self.options_window)

        # Connect the signal from the options pane
        self.options_window.options_updated.connect(self.update_options)

        self.options_window.show()

    def update_options(self, slope_target, tolerance, smoothing_enabled, smoothing_window):
        """
        Updates options based on user inputs from the options pane.
        """
        self.slope_target = slope_target
        self.tolerance = tolerance
        self.smoothing_enabled = smoothing_enabled
        self.smoothing_window = smoothing_window

        # Apply changes to trimming logic
        if hasattr(self, 'data_manager'):
            self.data_manager.trim_to_linear_region(
                target_slope=self.slope_target,
                tolerance=self.tolerance,
                smoothing_enabled=self.smoothing_enabled,
                smoothing_window=self.smoothing_window
            )

    def create_data_loader_window(self):
        """Creates a dockable widget for loading files and managing data."""
        self.data_loader_window = DataLoaderWindow(self)
        self.mdiArea.addSubWindow(self.data_loader_window)

    def create_data_manager_window(self):
        """
        """
        self.create_trimming_options_window()
        self.data_manager_window = DataManagerWindow(self.dataframes, self)
        self.mdiArea.addSubWindow(self.data_manager_window)
        self.data_manager_window.show()

    def plot_data(self, selected_files_and_dfs, dataframes, plot_type="Raw", include_legend=True):
        """
        Create a new PlotWindow for plotting selected DataFrames.
        """
        if not selected_files_and_dfs:
            print("No DataFrames selected for plotting.")
            return

        # Determine the data to plot
        if plot_type == "Trimmed Data" and self.data_manager is not None:
            data_to_plot = self.data_manager.get_trimmed_dataframes()

            # Check if any trimmed data exists
            valid_data = any(
                file_name in data_to_plot and data_to_plot[file_name]
                for file_name in selected_files_and_dfs.keys()
            )
            if not valid_data:
                QMessageBox.information(
                    self,
                    "No Data to Plot",
                    "No linear region found for the selected files. Unable to plot trimmed data."
                )
                return
        else:
            data_to_plot = dataframes

        # Create and show a PlotWindow
        plot_window = PlotWindow(
            self, selected_files_and_dfs, data_to_plot, plot_type, show_legend=include_legend
        )
        self.mdiArea.addSubWindow(plot_window)
        plot_window.show()
