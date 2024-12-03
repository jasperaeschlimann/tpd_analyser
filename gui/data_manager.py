from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QCheckBox, QPushButton, QComboBox
from PyQt5.QtCore import Qt

class DataManager(QWidget):
    """Widget to display loaded file names and their DataFrames."""

    def __init__(self, dataframes, main_window):
        super().__init__()

        self.dataframes = dataframes
        self.main_window = main_window  # Reference to the MainWindow for plotting

        # Layout for the viewer
        layout = QVBoxLayout(self)

        # Table to display file names with checkboxes
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)  # Checkbox, File Name
        self.file_table.setHorizontalHeaderLabels(["Select", "File Name"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.verticalHeader().setVisible(False)
        # Enable interaction with the header
        header = self.file_table.horizontalHeader()
        header.sectionClicked.connect(self.handle_header_click)
        layout.addWidget(self.file_table)

        # Populate the table with file names
        self.populate_file_table()

        # Dropdown to select plot type
        self.plot_type_dropdown = QComboBox()
        self.plot_type_dropdown.addItems(["Raw Data", "Trimmed Data"])
        layout.addWidget(self.plot_type_dropdown)

        # Add button to plot selected files
        self.plot_button = QPushButton("Plot Selected DataFrames")
        self.plot_button.clicked.connect(self.plot_selected_dataframes)
        layout.addWidget(self.plot_button)

        # Track whether all checkboxes are currently checked
        self.all_checked = False

    def populate_file_table(self):
        """Populates the table with file names and checkboxes."""
        self.file_table.setRowCount(len(self.dataframes)) # Sets number of rows to the length of dictionary of files:dataframes
        for row, file_name in enumerate(self.dataframes.keys()): # Enumerate generates pairs of (index, key), with key taken from dictionary. Row is the index
            # Add checkbox
            checkbox = QCheckBox()
            self.file_table.setCellWidget(row, 0, checkbox) # Places the checkbox on the left column of each row.

            # Add file name
            file_name_item = QTableWidgetItem(file_name) # Prepares a table entry for file name
            file_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled) # Sets flags for making table entry selectable and not greyed out.
            self.file_table.setItem(row, 1, file_name_item) # Sets row to contain the file 
            
    def handle_header_click(self, index):
        """Handles clicks on the header (toggle all checkboxes)."""
        if index == 0:  # If "Select" header is clicked
            self.all_checked = not self.all_checked  # Toggle the current state
            for row in range(self.file_table.rowCount()):
                checkbox = self.file_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(self.all_checked)

    def plot_selected_dataframes(self):
        """Sends the selected data to the MainWindow for plotting."""
        selected_files = []

        # Collect selected files
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox.isChecked():
                file_name = self.file_table.item(row, 1).text()
                selected_files.append(file_name)

        if not selected_files:
            print("No files selected for plotting.")
            return

        # Get the selected plot type
        plot_type = self.plot_type_dropdown.currentText()
        print(f"Selected plot type in DataViewer: {plot_type}") 

        # Send the selected files and plot type to the main window
        self.main_window.plot_data(selected_files, self.dataframes, plot_type=plot_type)