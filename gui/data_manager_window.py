from PyQt5.QtWidgets import( 
    QWidget, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QCheckBox, QPushButton, 
    QComboBox, QMdiSubWindow
)
from PyQt5.QtCore import Qt

class DataManagerWindow(QMdiSubWindow):
    """
    Window for selecting data to plot.
    """
    def __init__(self, dataframes, parent=None):
        super().__init__(parent)
        # Initialises instance variables
        self.dataframes = dataframes
        self.main_window = parent 

        # Tracks which files are expanded in the table
        self.expanded_files = set()

        # Sets window title
        self.setWindowTitle("Data Manager")

        # Set widget for the window and initialise layout
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        self.main_layout = QVBoxLayout()

        # Table to display file names with checkboxes
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)  # Checkbox, File Name, Toggle Arrow
        self.file_table.setHorizontalHeaderLabels(["Select", "File Name"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.verticalHeader().setVisible(False)
        
        # Enable interaction with the header
        header = self.file_table.horizontalHeader()
        header.sectionClicked.connect(self.handle_header_click)
        
        # Handle toggle clicks
        self.file_table.cellClicked.connect(self.handle_toggle_click)

        # Add table to layout
        self.main_layout.addWidget(self.file_table)

        # Populate the table with file names
        self.populate_file_table()

        # Add dropdown to select plot type
        self.plot_type_dropdown = QComboBox()
        self.plot_type_dropdown.addItems(["Raw Data", "Trimmed Data", "Integrated Data"])
        self.main_layout.addWidget(self.plot_type_dropdown)

        # Add checkbox to toggle legend inclusion in plots
        self.legend_checkbox = QCheckBox("Include Legend")
        self.legend_checkbox.setChecked(True)  # Default to include legend
        self.main_layout.addWidget(self.legend_checkbox)

        # Add button to trigger plot for selected files
        self.plot_button = QPushButton("Plot Selected DataFrames")
        self.plot_button.clicked.connect(self.plot_selected_dataframes)
        self.main_layout.addWidget(self.plot_button)

        # Add layout to the main widget
        self.main_widget.setLayout(self.main_layout)

        # Track whether all checkboxes are currently checked
        self.all_checked = False

    def populate_file_table(self):
        """
        Populates the table with file names and associated dataframes.
        """
        # Clears table and then fills each row for files and their DataFrames
        self.file_table.setRowCount(0)
        for file_name, dataframes in self.dataframes.items():
            self.add_file_row(file_name)
            for df_name in dataframes.keys():
                self.add_dataframe_row(df_name)
    
    def add_file_row(self, file_name):
        """
        Fills a row with a filename, checkbox, and toggle button.
        """
        # Finds where last row in table is, and inserts new row below
        row_position = self.file_table.rowCount()
        self.file_table.insertRow(row_position)

        # Add checkbox
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, row=row_position: self.toggle_file_checkboxes(row, state == Qt.Checked))
        self.file_table.setCellWidget(row_position, 0, checkbox)

        # Add file name with toggle arrow
        file_name_item = QTableWidgetItem(f"> {file_name}")  
        file_name_item.setFlags(Qt.ItemIsEnabled) 
        self.file_table.setItem(row_position, 1, file_name_item)
    
    def add_dataframe_row(self, df_name):
        """
        Adds a row for a DataFrame.
        """
        row_position = self.file_table.rowCount()
        self.file_table.insertRow(row_position)

        # Add checkbox
        checkbox = QCheckBox()
        self.file_table.setCellWidget(row_position, 0, checkbox)

        # Add DataFrame name (indented for clarity)
        df_name_item = QTableWidgetItem(f"    {df_name}")
        df_name_item.setFlags(Qt.ItemIsEnabled) 
        self.file_table.setItem(row_position, 1, df_name_item)

        # Initially hide the row
        self.file_table.setRowHidden(row_position, True)

    def handle_header_click(self, column):
        """
        Handles clicks on the header of table to toggle all checkboxes.
        """
        # Toggle current state of all checkboxes if checkbox column header is clicked
        if column == 0: 
            self.all_checked = not self.all_checked 

            # For all rows in the table, set the checkboxes to match the all checkboxes boolean
            for row in range(self.file_table.rowCount()):
                checkbox = self.file_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(self.all_checked)

    def handle_toggle_click(self, row, column):
        """
        Handles clicks on the toggle cells of the table to expand or collapse rows.
        """
        if column != 1:  # Only handle clicks on the File Name column
            return

        file_name_item = self.file_table.item(row, 1)
        if not file_name_item or not file_name_item.text().startswith(("> ", "v ")):
            return  # Ignore clicks on non-toggle items

        file_name = file_name_item.text()[2:]  # Extract file name without the arrow

        if file_name in self.expanded_files:
            # Collapse the rows
            self.toggle_dataframe_visibility(row, hide=True)
            file_name_item.setText(f"> {file_name}")  # Update arrow
            self.expanded_files.remove(file_name)
        else:
            # Expand the rows
            self.toggle_dataframe_visibility(row, hide=False)
            file_name_item.setText(f"v {file_name}")  # Update arrow
            self.expanded_files.add(file_name)

    def toggle_dataframe_visibility(self, file_row, hide):
        """
        Toggles visibility of rows for the DataFrames of the given file.
        """
        dataframes = self.dataframes[self.file_table.item(file_row, 1).text()[2:]]
        start_row = file_row + 1

        for _ in dataframes.keys():
            self.file_table.setRowHidden(start_row, hide)
            start_row += 1

    def toggle_file_checkboxes(self, file_row, checked):
        """
        Toggles the checkboxes for all DataFrames associated with a file.
        """
        file_name_item = self.file_table.item(file_row, 1)
        if not file_name_item:
            return

        file_name = file_name_item.text().strip()[2:]  # Remove the arrow
        dataframes = self.dataframes[file_name]

        # Toggle checkboxes for all associated DataFrame rows
        start_row = file_row + 1
        for _ in dataframes.keys():
            checkbox = self.file_table.cellWidget(start_row, 0)
            if checkbox:
                checkbox.setChecked(checked)
            start_row += 1
            
    def plot_selected_dataframes(self):
        """
        Sends the selected DataFrames to the MainWindow for plotting.
        """
        selected_files_and_dfs = {}  # Dictionary to hold selected files and their DataFrames

        current_file = None
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            file_or_df_name = self.file_table.item(row, 1).text().strip()

            if file_or_df_name.startswith(">") or file_or_df_name.startswith("v"):
                # File row (strip the arrow)
                current_file = file_or_df_name[2:]  # Extract file name
                if current_file not in selected_files_and_dfs:
                    selected_files_and_dfs[current_file] = []  # Initialize entry

                if not checkbox or not checkbox.isChecked():
                    continue  # Skip processing file itself, but keep current_file set

            elif current_file:
                # DataFrame row
                if checkbox and checkbox.isChecked():
                    selected_files_and_dfs[current_file].append(file_or_df_name)

        if not selected_files_and_dfs:
            print("No DataFrames selected for plotting.")
            return

        # Get the selected plot type
        plot_type = self.plot_type_dropdown.currentText()

        # Get the legend inclusion status
        include_legend = self.legend_checkbox.isChecked()

        # Send the selected files and their DataFrames to the main window
        self.main_window.plot_data(selected_files_and_dfs, self.dataframes, plot_type=plot_type, include_legend=include_legend)
