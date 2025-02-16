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
    A Subwindow for staging and loading .txt data files into the data manager.
    """
    # Signal emitted when files are loaded, sending the file list to the main window
    files_loaded = pyqtSignal(list)

    def __init__(self):
        """
        Initialises the DataLoaderWindow UI and connects buttons to actions.
        """
        super().__init__()

        # Load UI
        self.content_widget = QWidget()
        uic.loadUi("gui/data_loader_window.ui", self.content_widget)
        self.setWindowIcon(QIcon("resources/icons/load.png"))
        self.setWidget(self.content_widget)
        self.setAttribute(0x00000002) # Qt.WA_DeleteOnClose ensures window is removed from memory when closed

        # Connect UI elements to their respective functions
        self.content_widget.pushButton_StageFiles.clicked.connect(self.stage_files)
        self.content_widget.pushButton_LoadFiles.clicked.connect(self.load_files)

        # List to store staged file paths
        self.staged_files = []

    def stage_files(self):
        """
        Opens a file dialog for users to select files and populates the file table.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog # Use Qt-stle file dialog
        options |= QFileDialog.ReadOnly  # Prevents file/folder modification

        # Open file dialog and allow multiple file selection 
        files, _ = QFileDialog.getOpenFileNames( 
            self, "Select .txt Files", "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )

        if files:
            self.staged_files = files # Store staged file paths
            self.content_widget.tableWidget_LoadFiles.setRowCount(0)  # Clear existing entries
            for file_path in files:
                self._add_file_to_table(file_path) # Add each file to the table

    def _add_file_to_table(self, file_path):
        """
        Adds a file to the table widget displaying staged files.

        :param file_path: File path to process
        """
        # Adds a new row in the file table
        row_position = self.content_widget.tableWidget_LoadFiles.rowCount() 
        self.content_widget.tableWidget_LoadFiles.insertRow(row_position)

        # Extracts file name from the path and adds it in the new row
        file_name = os.path.basename(file_path) 
        file_name_item = QTableWidgetItem(file_name)
        self.content_widget.tableWidget_LoadFiles.setItem(row_position, 0, file_name_item) 

    def load_files(self):
        """
        Emits the list of staged files and closes the window.
        """
        # Check if user hasn't staged any files
        if not self.staged_files: 
            QMessageBox.information(self, "No Files", "No files loaded to process.")
            return

        # Emit signal to main window and close
        self.files_loaded.emit(self.staged_files)
        self.close()