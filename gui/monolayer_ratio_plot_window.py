from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

class MonolayerRatioPlotWindow(QMdiSubWindow):
    """
    A subwindow dedicated to displaying the monolayer calibration plot.
    """
    def __init__(self, dosages, ratio_integrated_values):
        """
        Initialises the Monolayer Calibration Plot Window.

        :param dosages: List of dosage values.
        :param integrated_values: Corresponding integrated ion current values.
        """
        super().__init__()

        self.dosages = np.array(dosages, dtype=float) 
        self.integrated_values = np.array(ratio_integrated_values, dtype=float)

        self.setWindowIcon(QIcon("resources/icons/plot.png"))        
        self.setWindowTitle(f"Monolayer Calibration")

        # Load UI
        self.content_widget = QWidget()
        uic.loadUi("gui/monolayer_plot_window.ui", self.content_widget)
        self.setWidget(self.content_widget)
        self.plot_widget = self.content_widget.findChild(QWidget, "plotWidget")
        self.toolbar_widget = self.content_widget.findChild(QWidget, "toolbarWidget")
        self.toggle_legend_button = self.content_widget.findChild(QPushButton, "pushButton_ToggleLegend")

        # Connect UI elemenents
        self.toggle_legend_button.clicked.connect(self._toggle_legend)

        # Initialise plot
        self._init_plot()

    def _init_plot(self):
        """
        Sets up the Matplotlib plot and toolbar inside the UI.
        """
        # Create Matplotlib figure and canvas
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.plot_canvas = FigureCanvas(self.figure)

        # Add plot canvas to UI
        plot_layout = self.plot_widget.layout()
        plot_layout.addWidget(self.plot_canvas)

        # Plot data
        self._plot_calibration_data()

        # Add Matplotlib toolbar
        toolbar_layout = self.toolbar_widget.layout()
        self.toolbar = NavigationToolbar(self.plot_canvas, self.content_widget)
        toolbar_layout.addWidget(self.toolbar)

        # Configure legend
        self.legend = self.figure.legend(loc="upper left")
        self.legend.set_visible(False)
        self.legend.set_draggable(True)

    def piecewise_linear(self, x, x_threshold, slope):
        """
        Defines a piecewise linear function for monolayer calibration.

        - For dosages (x) below the threshold (x_threshold), the function remains at 0.
        - For dosages equal to or greater than the threshold, the function increases linearly.

        Mathematically:
            f(x) = 0,                 if x < x_threshold
            f(x) = slope * (x - x_threshold),   if x >= x_threshold

        :param x: Array of dosage values.
        :param x_threshold: The dosage value at which the function transitions from 0 to linear growth.
        :param slope: The rate of increase after x_threshold.
        :return: Array of function values corresponding to x.
        """
        return np.where(x < x_threshold, 0, slope * (x - x_threshold))

    def _plot_calibration_data(self):
        """
        Plots integrated ion current vs dosage with a correctly implemented piecewise function:
        - Flat at 0 before threshold
        - Linear increase after threshold
        """
        self.ax.clear()
        
        # Scatter plot of raw data
        self.ax.scatter(self.dosages, self.integrated_values, marker="o", color="red", label="TPD Integrals")

        # Initial Guess for Fit Parameters
        initial_threshold = np.median(self.dosages)  # Start with median dosage
        initial_slope = (max(self.integrated_values) - min(self.integrated_values)) / (max(self.dosages) - min(self.dosages))  
        initial_guess = [initial_threshold, initial_slope]  # [x_threshold, slope]

        # Call to curve_fit()
        popt, _ = curve_fit(lambda x, x_threshold, slope: self.piecewise_linear(x, x_threshold, slope),
                            self.dosages, self.integrated_values, p0=initial_guess)

        # Extract fitted parameters
        x_threshold_fit, slope_fit = popt

        # Generate smooth x values for visualization
        x_smooth = np.linspace(min(self.dosages), max(self.dosages), 100)
        y_smooth = self.piecewise_linear(x_smooth, *popt) 

        # Plot the Piecewise Fit
        self.ax.plot(x_smooth, y_smooth, linestyle="-", color="blue", label=f"Piecewise Fit (Threshold: {x_threshold_fit:.2f})")

        # Labelling
        self.ax.set_xlabel("Dosage (K arb.u.)")
        self.ax.set_ylabel("TPD Integral")
        self.ax.set_title("Monolayer Calibration: Piecewise Fit with 0 Baseline")
        self.ax.grid(True)

        self.plot_canvas.draw()

    def _toggle_legend(self):
        """
        Toggles legend visibility.
        """
        self.legend.set_visible(not self.legend.get_visible())
        self.plot_canvas.draw()
