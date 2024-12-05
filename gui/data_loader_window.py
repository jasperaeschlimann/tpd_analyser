import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton,QFileDialog, 
    QTableWidget, QTableWidgetItem, QMdiSubWindow
)
from PyQt5.QtCore import Qt
from gui.data_loader import DataLoader

class DataLoaderWindow(QMdiSubWindow):
    """
    window
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_window = parent

        # Create a widget window
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        self.main_widget_layout = QVBoxLayout()

        # Add a button to load files
        self.load_files_button = QPushButton("Load Files")
        self.load_files_button.clicked.connect(self.load_files)
        self.main_widget_layout.addWidget(self.load_files_button)

        # Add a table to display file names
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(1)  # One column: File Name
        self.file_table.setHorizontalHeaderLabels(["File Name"])
        self.file_table.horizontalHeader().setStretchLastSection(True) # Sets last column header (File Name) to fill the remaining blank space in the table
        self.file_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.file_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Prevent editing
        self.main_widget_layout.addWidget(self.file_table)

        # Add the "Load Data" button
        load_data_button = QPushButton("Load Data")
        load_data_button.clicked.connect(self.load_data)
        self.main_widget_layout.addWidget(load_data_button)

        # Set the widget layout
        self.main_widget.setLayout(self.main_widget_layout)

    def load_files(self):
        """
        Opens a file dialog to select files and populates the table with file names.
        """
        options = QFileDialog.Options() # Instantiate the QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog # Uses Qt style file dialogue

        # Allow selecting multiple files
        files, _ = QFileDialog.getOpenFileNames( # Returns file paths
            self, # Parent widget, in this case the main application window
            "Select .txt Files", # Title of file dialog window
            "", # Intial directory to open, blank means current directory
            "Text Files (*.txt);;All Files (*)", # File filters
            options=options # Applies earlier options
        )

        if files:
            self.file_table.setRowCount(0)  # Clear the table before adding new rows
            self.loaded_files = files # Stores list of file paths in loaded_files for later use
            for file_path in files:
                self.add_file_to_table(file_path) # For each file in list, file path gets added to table

    def add_file_to_table(self, file_path):
        """
        Adds a single file to the table with its name.
        """
        file_name = os.path.basename(file_path) # Extracts file name without path
        row_position = self.file_table.rowCount() # Counts rows currently in table
        self.file_table.insertRow(row_position) # Inserts new entry into table on the next row

        file_name_item = QTableWidgetItem(file_name) # Creates table widget labelled as the file name
        file_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled) # Sets item flags so that it is selectable and enabled (not grayed out)
        self.file_table.setItem(row_position, 0, file_name_item) # Places the table widget in the first column of the row

    def load_data(self):
        """
        Handles the logic when 'Load Data' button is clicked.
        """
        if not self.loaded_files: # Checks if loaded_files is 'falsy' i.e. is empty
            print("No files loaded to process.")
            return

        # Create an instance of DataLoader with the loaded files
        self.data_loader = DataLoader(self.loaded_files)

        # Load the dataframes
        self.main_window.dataframes = self.data_loader.load_files_to_dataframes()

        # Trim the data to the linear region
        self.data_loader.trim_to_linear_region()
        
        self.main_window.create_data_manager()