from PyQt5.QtWidgets import (QMainWindow, QMessageBox)
from PyQt5.QtGui import QIcon
from gui.data_loader_window import DataLoaderWindow
from gui.data_manager_window import DataManagerWindow
from gui.trimming_options_window import TrimmingOptionsWindow
from gui.plot_window import PlotWindow
from gui.monolayer_full_plot_window import MonolayerFullPlotWindow
from gui.monolayer_ratio_plot_window import MonolayerRatioPlotWindow
from backend.data_manager import DataManager
from backend.asc_to_txt_converter import FileConverter
from PyQt5 import uic

class MainWindow(QMainWindow):
    """
    Main application window with an MDI area for holding all other windows. Also contains a taskbar for menu options.
    """
    def __init__(self):
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

        # Initialise the File Converter and Data Manager
        self.file_converter = FileConverter(self)
        self.data_manager = DataManager()

        # Connect "Convert .asc to .txt" action to File Converter
        self.actionConvert_asc_to_txt.triggered.connect(self.file_converter.convert_asc_to_txt)

        # Connect Data Manager signal to trigger creation of data manager and trimming option windows
        self.data_manager.data_processed.connect(self.create_data_manager_window)
        self.data_manager.data_processed.connect(self.create_trimming_options_window)

        # Create the data loader
        self.create_data_loader_window()

    def create_data_loader_window(self):
        """
        Creates and displays a window for staging and loading files.
        """
        # Create data loader window, connect files_loaded signal, and add window to mdiArea
        self.data_loader_window = DataLoaderWindow()
        self.data_loader_window.files_loaded.connect(self.data_manager.set_files)
        self.mdiArea.addSubWindow(self.data_loader_window) 
    
    def create_data_manager_window(self):
        """
        Creates and displays a window for managing the loaded files.
        """
        # Create data manager window
        self.data_manager_window = DataManagerWindow(self.data_manager.dataframes)
        self.mdiArea.addSubWindow(self.data_manager_window)
        self.data_manager_window.show()

        # Connect signals
        self.data_manager_window.dataframe_double_clicked.connect(
            lambda file_name, df_name: self.plot_dataframes({file_name: [df_name]})
        )
        self.data_manager_window.file_double_clicked.connect(self.plot_entire_file)
        self.data_manager_window.plot_button_clicked.connect(
            lambda selected_files_and_dfs, plot_type: self.plot_dataframes(
                selected_files_and_dfs, {}, plot_type
            )
        )

    def create_trimming_options_window(self):
        """Creates and displays a window for handling trimming parameters of loaded data."""
        self.options_window = TrimmingOptionsWindow()
        self.mdiArea.addSubWindow(self.options_window)

        # Connect the signal from the options pane
        self.options_window.options_updated.connect(self.data_manager.trim_to_linear_region)
        self.options_window.show()

    def plot_dataframes(self, selected_files_and_dfs, trim_boundaries={},  plot_type = "Raw", enable_trimming=False):
        """
        Handles plotting for both a single DataFrame (double-click) and multiple selected DataFrames (plot button).

        :param selected_files_and_dfs: Dictionary where keys are file names and values are lists of selected DataFrame names
        :param trim_boundaries: Dictionary mapping file names to their trimming boundaries (start, end)
        :param plot_type: The type of plot selected by the user
                        Options: "Raw", "Trimmed Data - Time", "Trimmed Data - Temperature"
        :param enable_trimming: Boolean flag indicating whether trimming should be enabled
        """
        if not selected_files_and_dfs:
            return

        # Check if user selected "Trimmed Data - Time" and if trimming exists
        if plot_type in ("Trimmed Data - Time", "Trimmed Data - Temperature"):
            trimmed_data = self.data_manager.trimmed_dataframes  # Retrieve trimmed data

            # Validate if there is trimmed data for the selected files            
            valid_data = any(
                file_name in trimmed_data and trimmed_data[file_name]
                for file_name in selected_files_and_dfs.keys()
            )
            if not valid_data:
                QMessageBox.information(
                    self,
                    "No Trimmed Data Available",
                    "No linear region found for the selected files. Unable to plot trimmed data."
                )
                return
            data_to_plot = trimmed_data
        else:
            data_to_plot = self.data_manager.dataframes

        # Create and show a PlotWindow with the selected data
        plot_window = PlotWindow(
            selected_files_and_dfs, data_to_plot, trim_boundaries, plot_type, enable_trimming
        )
        self.mdiArea.addSubWindow(plot_window)
        plot_window.monolayer_calibration_requested.connect(self.perform_monolayer_calibration)
        plot_window.show()

    def plot_entire_file(self, file_name):
        """
        Handles plotting when an entire file is double-clicked.

        :param file_name: The name of the file to be plotted
        """
        if file_name not in self.data_manager.dataframes:
            QMessageBox.warning(self, "Error", f"File '{file_name}' not found.")
            return
        
        selected_files_and_dfs = {file_name: list(self.data_manager.dataframes[file_name].keys())}
        file_name = list(selected_files_and_dfs.keys())[0]  # Assuming one file at a time

        # Get stored trimming boundaries from DataManager
        trim_boundaries = self.data_manager.get_trim_boundaries(file_name)
        plot_window = PlotWindow(
            selected_files_and_dfs, self.data_manager.dataframes, trim_boundaries, plot_type="Raw", enable_trimming=True
            )
        self.mdiArea.addSubWindow(plot_window)
        plot_window.show()
        plot_window.trim_boundaries_updated.connect(self.update_trim_boundaries)

    def update_trim_boundaries(self, file_name, trim_start_time, trim_end_time):
        """
        Receives trimming boundaries from PlotWindow and updates DataManager.

        :param file_name: The name of the file whose trimming boundaries are being updated
        :param trim_start_time: The starting time for trimming
        :param trim_end_time: The ending time for trimming
        """
        self.data_manager.apply_trim_boundaries(file_name, trim_start_time, trim_end_time)

    def perform_monolayer_calibration(self, selected_files_and_dfs, smoothing_window, integration_boundaries):
        """
        Triggers integration in DataManager for the selected trimmed-temperature curves and plots calibration results.

        :param selected_files_and_dfs: Dictionary where keys are file names and values are lists of selected DataFrame names
        :param smoothing_window: Integer representing the window size for smoothing the data before integration
        :param integration_boundaries: Tuple containing (left_start_temp, left_end_temp, right_start_temp, right_end_temp)
                                    which define the integration regions

        :returns: Displays two monolayer calibration plots:
                1. A full integration plot (MonolayerFullPlotWindow)
                2. A ratio integration plot (MonolayerRatioPlotWindow)
        """
        full_integration_results = self.data_manager.perform_full_integration(selected_files_and_dfs, smoothing_window)
        
        ratio_integration_results = self.data_manager.perform_ratio_integration(
            selected_files_and_dfs, smoothing_window, integration_boundaries
        )

        # Extract dosage and integrated values
        dosages = sorted(full_integration_results.keys())
        full_integrated_values = [full_integration_results[d] for d in dosages]
        ratio_integrated_values = [ratio_integration_results[d] for d in dosages]


        # Create and show the Monolayer Plot Window
        monolayer_full_plot_window = MonolayerFullPlotWindow(dosages, full_integrated_values)
        self.mdiArea.addSubWindow(monolayer_full_plot_window)
        monolayer_ratio_plot_window = MonolayerRatioPlotWindow(dosages, ratio_integrated_values)
        self.mdiArea.addSubWindow(monolayer_ratio_plot_window)

        monolayer_full_plot_window.show()
        monolayer_ratio_plot_window.show()

