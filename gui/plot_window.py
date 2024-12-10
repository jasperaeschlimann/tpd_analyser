from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from backend.navigation_toolbar import CustomNavigationToolbar
from backend.plot_backend import PlotBackend  # Import the PlotBackend class
from matplotlib.figure import Figure

class PlotWindow(QMdiSubWindow):
    """
    A subwindow for plotting selected DataFrames.
    """
    def __init__(self, parent, selected_files_and_dfs, dataframes, plot_type="Raw", show_legend=True):
        super().__init__(parent)

        self.plot_backend = PlotBackend(dataframes, selected_files_and_dfs, plot_type, show_legend)

        # Set up the plot widget
        self.plot_canvas = None
        self.toolbar = None
        self.init_plot()

    def init_plot(self):
        """Initialize and display the plot."""
        # Create a new Matplotlib figure and canvas
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

        # Create the plot widget
        plot_widget = QWidget()
        layout = QVBoxLayout(plot_widget)
        layout.addWidget(self.plot_canvas)

        # Add a navigation toolbar
        self.toolbar = CustomNavigationToolbar(self.plot_canvas, self)
        layout.addWidget(self.toolbar)

        # Set the subwindow widget
        self.setWidget(plot_widget)
        self.setWindowTitle(f"Plot - {self.plot_backend.plot_type}")

        # Draw the canvas
        self.plot_canvas.draw()
