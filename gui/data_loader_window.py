import os
from PyQt5.QtWidgets import (
    QWidget,QFileDialog, QTableWidgetItem, 
    QMdiSubWindow,QMessageBox
)
from PyQt5.QtCore import Qt
from backend.data_manager import DataManager
from PyQt5 import uic

class DataLoaderWindow(QMdiSubWindow):
    """
    Window for user to stage and load .txt data files into the data manager.
    """
    def __init__(self, parent=None):
        # Call QMdiSubWindow constructor
        super().__init__(parent)
        self.setMinimumSize(300,650)

        # Initialise UI for Data Loader
        self.content_widget = QWidget()
        uic.loadUi("gui/data_loader_window.ui", self.content_widget)
        self.content_widget.pushButton_StageFiles.clicked.connect(self.stage_files)
        self.content_widget.pushButton_LoadFiles.clicked.connect(self.load_files)
        self.setWidget(self.content_widget)
        self.setAttribute(0x00000002) # Qt.WA_DeleteOnClose

        # Placeholder for list of loaded file paths
        self.loaded_files = []

        # Sets parent as a callable attribute
        self.main_window = parent

    def stage_files(self):
        """
        Opens a file dialog to select files for staging and populates the table with their file names.
        """
        options = QFileDialog.Options() # Instantiate the QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog # Uses Qt style file dialogue

        # Allow selecting multiple files
        files, _ = QFileDialog.getOpenFileNames( # Returns file paths
            self, 
            "Select .txt Files", # Title of file dialog window
            "", # Intial directory to open, blank means current directory
            "Text Files (*.txt);;All Files (*)", # File filters
            options=options # Applies earlier options
        )

        if files:
            self.content_widget.tableWidget_LoadFiles.setRowCount(0)  # Clear the table before adding new rows
            self.loaded_files = files # Stores list of file paths in loaded_files for later use
            for file_path in files:
                self.add_file_to_table(file_path) # For each file in list, file path gets added to table

    def add_file_to_table(self, file_path):
        """
        Adds a single file to the table by displaying it's filename.
        """
        file_name = os.path.basename(file_path) # Extracts file name without path
        row_position = self.content_widget.tableWidget_LoadFiles.rowCount() # Counts rows currently in table
        self.content_widget.tableWidget_LoadFiles.insertRow(row_position) # Inserts new entry into table on the next row

        file_name_item = QTableWidgetItem(file_name) # Creates table widget labelled as the file name
        file_name_item.setFlags(Qt.ItemIsEnabled) # Sets item flags so that it is selectable and enabled (not grayed out)
        self.content_widget.tableWidget_LoadFiles.setItem(row_position, 0, file_name_item) # Places the table widget in the first column of the row

    def load_files(self):
        """
        Loads the staged files into the data manager, and calls the data manager window to open.
        """
        if not self.loaded_files: # Checks if loaded_files is 'falsy' i.e. is empty
            QMessageBox.information(self, "No Files", "No files loaded to process.")
            return

        # Create an instance of DataManager with the loaded files
        self.main_window.data_manager = DataManager(self.loaded_files)

        # Load the dataframes
        self.main_window.dataframes = self.main_window.data_manager.extract_data_to_dataframes()

        # Trim the data to the linear region
        self.main_window.data_manager.trim_to_linear_region()
        
        self.main_window.create_data_manager_window()

        # Close the DataLoaderWindow
        self.close()