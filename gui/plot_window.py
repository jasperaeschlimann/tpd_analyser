from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QPushButton, QSpinBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from backend.plot_backend import PlotBackend 
from backend.draggable_lines import DraggableLines

class PlotWindow(QMdiSubWindow):
    """
    A subwindow for displaying plots of selected DataFrames.
    """
    # Signal to communicate new trimming boundaries to MainWindow
    trim_boundaries_updated = pyqtSignal(str, float, float) 
    # Signal to trigger monolayer calibration (integration)
    monolayer_calibration_requested = pyqtSignal(dict, int, tuple)

    def __init__(self, selected_files_and_dfs, dataframes, trim_boundaries, plot_type="Raw", enable_trimming=False):
        """
        Initialises the PlotWindow.

        :param selected_files_and_dfs: Dictionary mapping selected files to chosen DataFrame names
        :param dataframes: Nested dictionary containing loaded files and their corresponding DataFrames
        :param trim_boundaries: Tuple (start, end) specifying initial trim positions
        :param plot_type: Type of plot to generate ("Raw", "Trimmed Data - Time", "Trimmed Data - Temperature")
        :param enable_trimming: Whether trimming functionality should be enabled
        """
        super().__init__()
        
        self.selected_files_and_dfs = selected_files_and_dfs
        self.dataframes = dataframes
        self.plot_type = plot_type
        self.enable_trimming = enable_trimming 
        self.trim_boundaries = trim_boundaries

        # State tracking for integration lines
        self.integration_lines_added = 0

        # Set window properties
        self.setWindowIcon(QIcon("resources/icons/plot.png"))        
        self.setWindowTitle(f"Plot - {self.plot_type}")

        # Load UI
        self.content_widget = QWidget()
        uic.loadUi("gui/plot_window.ui", self.content_widget)
        self.setWidget(self.content_widget)
        self.plot_widget = self.content_widget.findChild(QWidget, "plotWidget")
        self.toolbar_widget = self.content_widget.findChild(QWidget, "toolbarWidget")
        self.toggle_legend_button = self.content_widget.findChild(QPushButton, "pushButton_ToggleLegend")
        self.add_trim_button = self.content_widget.findChild(QPushButton, "pushButton_AddTrim")
        self.save_trim_button = self.content_widget.findChild(QPushButton, "pushButton_SaveTrim")
        self.add_peak_button = self.content_widget.findChild(QPushButton, "pushButton_AddPeak")
        self.smooth_window_box = self.content_widget.findChild(QSpinBox, "spinBox_SmoothWindow")
        self.monolayer_calibration_button = self.content_widget.findChild(QPushButton, "pushButton_Monolayer")

        # Connect UI elemenents
        self.toggle_legend_button.clicked.connect(self._toggle_legend)
        self.add_trim_button.clicked.connect(self._add_trim)
        self.save_trim_button.clicked.connect(self._save_trimming_boundaries)
        self.add_peak_button.clicked.connect(self._add_integration)
        self.smooth_window_box.valueChanged.connect(self._update_smoothing_window)
        self.monolayer_calibration_button.clicked.connect(self._monolayer_calibration)

        self.monolayer_calibration_button.setEnabled(False)

        # Disable trimming buttons if trimming not enabled
        if not self.enable_trimming:
            self.save_trim_button.setEnabled(False)
            self.add_trim_button.setEnabled(False)

        # Disable adding peaks and smoothing temp unless trimmed data - temp plot
        if not self.plot_type == "Trimmed Data - Temperature":
            self.add_peak_button.setEnabled(False)
            self.smooth_window_box.setEnabled(False)

        # Initialise plot
        self.plot_backend = PlotBackend(self.dataframes, self.selected_files_and_dfs, self.plot_type)
        self._init_plot()

    def _init_plot(self):
        """
        Sets up the Matplotlib plot and toolbar inside the UI.
        """
        # Create Matplotlib figure and canvas
        self.figure = plt.figure()
        self.plot_canvas = FigureCanvas(self.figure)

        # Configure axes using PlotBackend
        self.ax_left, self.ax_right = self.plot_backend.configure_axes(self.figure)

        # Add plot canvas to UI
        plot_layout = self.plot_widget.layout()
        plot_layout.addWidget(self.plot_canvas)

        # Plot data
        self.plot_backend.plot_data(self.ax_left, self.ax_right)

        if self.ax_right is not None:
            self.draggable_lines = DraggableLines(self.ax_right)
        else:
            self.draggable_lines = DraggableLines(self.ax_left)

        # Enable trim lines if required
        if self.enable_trimming:
            # Prevent new trim lines if boundaries already exist
            if self.trim_boundaries is not None:
                self.draggable_lines.add_trim_lines(self.trim_boundaries)
                self.add_trim_button.setEnabled(False)

        # Add Matplotlib toolbar
        toolbar_layout = self.toolbar_widget.layout()
        self.toolbar = NavigationToolbar(self.plot_canvas, self.content_widget)
        toolbar_layout.addWidget(self.toolbar)

        # Configure legend
        self.legend = self.figure.legend(loc="upper left")
        self.legend.set_visible(False)
        self.legend.set_draggable(True)
        
    def _toggle_legend(self):
        """
        Toggles legend visibility.
        """
        self.legend.set_visible(not self.legend.get_visible())
        self.plot_canvas.draw()

    def _add_trim(self):
        """
        Adds draggable trim lines when the user clicks "Add Trim".
        """
        self.draggable_lines.add_trim_lines()
        self.add_trim_button.setEnabled(False) # Prevent more than one set of trim lines
    
    def _save_trimming_boundaries(self):
        """
        Emits the new trimming boundaries to MainWindow.
        """
        trim_start, trim_end = self.draggable_lines.get_trim_positions()
        file_name = list(self.selected_files_and_dfs.keys())[0]  # Assuming one file at a time
        
        self.trim_boundaries_updated.emit(file_name, trim_start, trim_end)  # Emit signal to MainWindow

    def _update_smoothing_window(self, value):
        """
        Updates the smoothing window size and refreshes the plot when the user changes the spin box.

        :param value: The new smoothing window size (integer) from the QSpinBox
        """
        # Update smoothing window size
        self.plot_backend.smoothing_window = value  

        # Clear and redraw graph
        self.ax_left.clear()
        if self.ax_right:
            self.ax_right.clear()

        self.plot_backend.plot_data(self.ax_left, self.ax_right)

        # Retrieve existing integration boundaries
        existing_integration = self.draggable_lines.get_trim_positions("integration")
        self.draggable_lines = DraggableLines(self.ax_left)
        if existing_integration:
            int1_left, int1_right, int2_left, int2_right = existing_integration
            self.draggable_lines.add_trim_lines(trim_boundaries=(int1_left, int1_right, int2_left, int2_right), line_type="integration")

        # Re-initialise plot legend
        self.legend = self.figure.legend(loc="upper left")
        self.legend.set_visible(False)
        self.legend.set_draggable(True)

        self.plot_canvas.draw()

    def _add_integration(self):
        """
        Handles adding two sets of integration lines:
        """
        self.draggable_lines.add_trim_lines(line_type="integration")  
        self.add_peak_button.setEnabled(False)  
        self.monolayer_calibration_button.setEnabled(True)

    def _monolayer_calibration(self):
        """
        Emits a signal to perform monolayer calibration (integration) on the selected files and DataFrames.
        """
        integration_boundaries = self.draggable_lines.get_trim_positions("integration")
        print(integration_boundaries)
        smoothing_window = self.smooth_window_box.value()  # Get current smoothing value
        self.monolayer_calibration_requested.emit(self.selected_files_and_dfs, smoothing_window, integration_boundaries)
