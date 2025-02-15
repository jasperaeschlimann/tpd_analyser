import os
from PyQt5.QtWidgets import (
    QWidget,QFileDialog, QTableWidgetItem, 
    QMdiSubWindow,QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

class DataLoaderWindow(QMdiSubWindow):
    """
    Window for user to stage and load .txt data files into the data manager.
    """
    # Signal that sends the loaded files list to the main window when load button is clicked
    files_loaded = pyqtSignal(list)

    def __init__(self):
        # Call QMdiSubWindow constructor
        super().__init__()

        # Initialise UI for Data Loader
        self.content_widget = QWidget()
        uic.loadUi("gui/data_loader_window.ui", self.content_widget)
        self.setWindowIcon(QIcon("resources/icons/load.png"))
        self.content_widget.pushButton_StageFiles.clicked.connect(self.stage_files)
        self.content_widget.pushButton_LoadFiles.clicked.connect(self.load_files)
        self.setWidget(self.content_widget)
        self.setAttribute(0x00000002) # Qt.WA_DeleteOnClose

        # Placeholder for list of staged files
        self.staged_files = []

    def stage_files(self):
        """
        Opens a file dialog to select files for staging and populates the file table with their file names.
        """
        # Set Qt style file dialog instead of OS dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog 

        # Extracts user selected file paths 
        files, _ = QFileDialog.getOpenFileNames( # Returns file paths
            self, 
            "Select .txt Files", # Title of file dialog window
            "", # Intial directory to open, blank means current directory
            "Text Files (*.txt);;All Files (*)", # File filters to restrict selection
            options=options # Applies Qt style file dialog
        )

        # Adds staged files to the file table
        if files:
            self.content_widget.tableWidget_LoadFiles.setRowCount(0)  # Clear the table before adding new rows
            self.staged_files = files # Stores list of staged file paths for later check during load_files
            for file_path in files:
                self._add_file_to_table(file_path) # For each user selected file, file path gets added to file table

    def _add_file_to_table(self, file_path):
        """
        Adds a single file to the table by displaying it's filename.

        :param file_path: File path to process
        """
        # Adds a new row in the file table
        row_position = self.content_widget.tableWidget_LoadFiles.rowCount() 
        self.content_widget.tableWidget_LoadFiles.insertRow(row_position)

        # Extracts file name from the path and adds it in the new row
        file_name = os.path.basename(file_path) 
        file_name_item = QTableWidgetItem(file_name) # Creates table widget labelled as the file name
        self.content_widget.tableWidget_LoadFiles.setItem(row_position, 0, file_name_item) # Places the table widget in the first column of the row

    def load_files(self):
        """
        Loads the staged files by sending them to the data manager.
        """
        # Check if staged_files is 'falsy' i.e. user hasn't staged any files
        if not self.staged_files: 
            QMessageBox.information(self, "No Files", "No files loaded to process.")
            return

        # Sends loaded files list to main window
        self.files_loaded.emit(self.staged_files)

        # Close the DataLoaderWindow
        self.close()