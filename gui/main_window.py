import os
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QDockWidget
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from gui.data_loader import DataLoader
from gui.data_manager import DataManager
from gui.options_pane import OptionsPane

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Set the main window's properties
        self.setWindowTitle("TPD_Analyser")
        self.setGeometry(50, 50, 1600, 900)

        # List to store loaded file paths
        self.loaded_files = []

        # Placeholder for Matplotlib canvas and toolbar
        self.plot_canvas = None
        self.toolbar = None
        self.show_legend = True

        # Create the data manager and options pane
        self.create_dock_widget()
        self.create_options_pane()

    def create_options_pane(self):
        """Creates the options pane."""
        self.options_pane = OptionsPane(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.options_pane)

        # Connect the signal from the options pane
        self.options_pane.options_updated.connect(self.update_options)

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

    def create_dock_widget(self):
        """Creates a dockable widget for loading files and managing data."""
        self.dock_widget = QDockWidget("File Loader", self)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Create a widget for the dock content
        dock_content = QWidget()
        dock_layout = QVBoxLayout()

        # Add a button to load files
        load_button = QPushButton("Load Files")
        load_button.clicked.connect(self.load_files)
        dock_layout.addWidget(load_button)

        # Add a table to display file names
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(1)  # One column: File Name
        self.file_table.setHorizontalHeaderLabels(["File Name"])
        self.file_table.horizontalHeader().setStretchLastSection(True) # Sets last column header (File Name) to fill the remaining blank space in the table
        self.file_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.file_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Prevent editing
        dock_layout.addWidget(self.file_table)

        # Add the "Load Data" button
        load_data_button = QPushButton("Load Data")
        load_data_button.clicked.connect(self.load_data)
        dock_layout.addWidget(load_data_button)

        # Set the dock content
        dock_content.setLayout(dock_layout)
        self.dock_widget.setWidget(dock_content)

        # Add the dock widget to the main window
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def load_files(self):
        """Opens a file dialog to select files and populates the table with file names."""
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
        """Adds a single file to the table with its name."""
        file_name = os.path.basename(file_path) # Extracts file name without path
        row_position = self.file_table.rowCount() # Counts rows currently in table
        self.file_table.insertRow(row_position) # Inserts new entry into table on the next row

        file_name_item = QTableWidgetItem(file_name) # Creates table widget labelled as the file name
        file_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled) # Sets item flags so that it is selectable and enabled (not grayed out)
        self.file_table.setItem(row_position, 0, file_name_item) # Places the table widget in the first column of the row

    def load_data(self):
        """Handles the logic when 'Load Data' button is clicked."""
        if not self.loaded_files: # Checks if loaded_files is 'falsy' i.e. is empty
            print("No files loaded to process.")
            return

        # Create an instance of DataLoader with the loaded files
        self.data_loader = DataLoader(self.loaded_files)

        # Load the dataframes
        self.dataframes = self.data_loader.load_files_to_dataframes()

        # Trim the data to the linear region
        self.data_loader.trim_to_linear_region()

        # Replace the dock widget content with Data Manager
        self.replace_dock_widget_content()

    def replace_dock_widget_content(self):
        """Replaces the dock widget content with the Data Manager."""
        data_manager = DataManager(self.dataframes, self)
        self.dock_widget.setWidget(data_manager)
        self.dock_widget.setWindowTitle("Data Manager")

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
        self.setCentralWidget(plot_widget)

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

