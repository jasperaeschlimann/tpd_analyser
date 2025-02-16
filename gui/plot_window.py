from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from backend.navigation_toolbar import CustomNavigationToolbar
from backend.plot_backend import PlotBackend 
from matplotlib.figure import Figure

class PlotWindow(QMdiSubWindow):
    """
    A subwindow for displaying plots of selected DataFrames.
    """
    def __init__(self, selected_files_and_dfs, dataframes, plot_type="Raw", show_legend=True):
        """
        Initialises the PlotWindow.

        :param selected_files_and_dfs: Dictionary containing selected files as keys and their chosen DataFrame names as values
        :param dataframes: Nested dictionary containing loaded files and their corresponding dictionary of DataFrames
        :param plot_type: The type of plot to generate ("Raw", "Trimmed Data - Time", "Trimmed Data - Temperature")
        :param show_legend: Boolean indicating whether to display the legend in the plot
        """
        super().__init__()

        self.setWindowIcon(QIcon("resources/icons/plot.png"))
        self.plot_backend = PlotBackend(dataframes, selected_files_and_dfs, plot_type, show_legend)

        # Load UI from Qt Designer
        self.content_widget = QWidget()
        uic.loadUi("gui/plot_window.ui", self.content_widget)
        self.setWidget(self.content_widget)

        # Assign UI elements
        self.plot_widget = self.content_widget.findChild(QWidget, "plotWidget")
        self.toolbar_widget = self.content_widget.findChild(QWidget, "toolbarWidget")

        # Initialise the plot
        self._init_plot()

    def _init_plot(self):
        """
        Sets up the Matplotlib plot and toolbar inside the UI.
        """
        # Create Matplotlib figure and canvas
        figure = Figure()
        self.plot_canvas = FigureCanvas(figure)

        # Configure axes using PlotBackend
        try:
            ax_left, ax_right = self.plot_backend.configure_axes(figure)
        except ValueError as e:
            print(str(e))
            self.close()
            return

        # Plot data
        self.plot_backend.plot_data(ax_left, ax_right)

        # Embed FigureCanvas in the plot widget of the UI     
        plot_layout = QVBoxLayout(self.plot_widget)
        plot_layout.addWidget(self.plot_canvas)
        self.plot_widget.setLayout(plot_layout)


        # Embed navigation toolbar in the toolbar_widget of the UI
        self.toolbar = CustomNavigationToolbar(self.plot_canvas, self)
        toolbar_layout = QVBoxLayout(self.toolbar_widget)
        toolbar_layout.addWidget(self.toolbar)
        self.toolbar_widget.setLayout(toolbar_layout)
    
        # Dynamically name the plot window
        self.setWindowTitle(f"Plot - {self.plot_backend.plot_type}")

        # Draw the canvas
        self.plot_canvas.draw()
