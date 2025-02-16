from PyQt5.QtWidgets import( 
    QWidget, QMdiSubWindow, 
    QTreeWidgetItem, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import uic

class DataManagerWindow(QMdiSubWindow):
    """
    Window for selecting data to plot.
    """
    # Signals for interacting with the main window
    dataframe_double_clicked = pyqtSignal(str, str)
    file_double_clicked = pyqtSignal(str)
    plot_button_clicked = pyqtSignal(dict, str)

    def __init__(self, dataframes):
        """
        Initialises the DataManagerWindow UI.

        :param dataframes: Nested dictionary containing loaded files and their corresponding dictionary of DataFrames
        """
        super().__init__()

        self.dataframes = dataframes # Stores the loaded data

        # Load UI
        self.content_widget = QWidget()
        uic.loadUi("gui/data_manager_window.ui", self.content_widget)
        self.content_widget.pushButton_Plot.clicked.connect(self.plot_selected_dataframes)
        self.setWindowIcon(QIcon("resources/icons/manager.png"))
        self.setWidget(self.content_widget)

        # Populate the tree widget with files and their respective DataFrames
        self._populate_tree()

        # Connect double-click event to function
        self.content_widget.treeWidget_Files.itemDoubleClicked.connect(self._handle_double_click)

    def _populate_tree(self):
        """
        Populates the QTreeWidget with files and their corresponding DataFrames.
        """
        for file_name, dataframes in self.dataframes.items():
            self._add_file_with_dataframes(file_name, dataframes)

    def _add_file_with_dataframes(self, file_names, dataframe_names):
        """
        Adds a file and its associated DataFrames as tree items in QTreeWidget.

        :param file_name: Name of the file
        :param dataframe_names: List of DataFrame names associated with the file
        """
        file_item = QTreeWidgetItem(self.content_widget.treeWidget_Files)
        file_item.setText(1, file_names)
        file_item.setCheckState(0,0)
        
        # Connect checkbox click signal to function
        self.content_widget.treeWidget_Files.itemChanged.connect(self._toggle_child_checkboxes)

        # Add DataFrames as child items
        for df_name in dataframe_names:
            df_item = QTreeWidgetItem(file_item)
            df_item.setText(1, df_name)
            df_item.setCheckState(0,0)

    def _toggle_child_checkboxes(self, item):
        """
        Ensures that when a file is checked/unchecked, all its child DataFrames follow the same state.

        :param item: The QTreeWidgetItem that was toggled
        """
        if item.parent() is None:  # Check if it's a file (top-level item)
            state = item.checkState(0)  # Get its check state (Checked/Unchecked)
            
            # Apply the same state to all child items (DataFrames)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)

    def _handle_double_click(self, item):
        """
        Handles double-click events on files and DataFrames.

        - If a file is double-clicked, it emits `file_double_clicked` (triggers full file raw plotting).
        - If a DataFrame is double-clicked, it emits `dataframe_double_clicked` (triggers single DataFrame raw plotting).

        :param item: The QTreeWidgetItem that was double-clicked.
        """
        if item.parent() is None:   # It's a file
            file_name = item.text(1).strip()
            self.file_double_clicked.emit(file_name)    # Plot the entire file
        else:   # It's a DataFrame
            file_name = item.parent().text(1).strip()
            df_name = item.text(1).strip()
            self.dataframe_double_clicked.emit(file_name, df_name)  # Plot a single DataFrame

    def plot_selected_dataframes(self):
        """
        Collects selected DataFrames and emits a signal to the MainWindow for plotting.
        """
        selected_files_and_dfs = {}  # Dictionary of selected files and their chosen DataFrames

        # Iterate over top-level (file) items
        for i in range(self.content_widget.treeWidget_Files.topLevelItemCount()):
            file_item = self.content_widget.treeWidget_Files.topLevelItem(i)
            file_name = file_item.text(1).strip()

            selected_dataframes = []

            # Iterate over child (DataFrame) items
            for j in range(file_item.childCount()):
                df_item = file_item.child(j)
                df_name = df_item.text(1).strip()

                if df_item.checkState(0) == Qt.Checked:  # Only add DataFrames that have been selected
                    selected_dataframes.append(df_name)

            if selected_dataframes:   # Only add files that have selected DataFrames
                selected_files_and_dfs[file_name] = selected_dataframes

        if not selected_files_and_dfs:
            QMessageBox.information(self, "No Selection", "No DataFrames selected for plotting.")
            return

        # Get the selected plot type from the dropdown menu
        plot_type = self.content_widget.comboBox_PlotType.currentText()

        # Emit signal with selected files, DataFrames, and plot type
        self.plot_button_clicked.emit(selected_files_and_dfs, plot_type)
