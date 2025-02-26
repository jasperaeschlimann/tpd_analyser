from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

class MonolayerPlotWindow(QMdiSubWindow):
    """
    A subwindow dedicated to displaying the monolayer calibration plot.
    """
    def __init__(self, dosages, integrated_values):
        """
        Initialises the Monolayer Calibration Plot Window.

        :param dosages: List of dosage values.
        :param integrated_values: Corresponding integrated ion current values.
        """
        super().__init__()

        self.dosages = np.array(dosages, dtype=float) 
        self.integrated_values = np.array(integrated_values, dtype=float)

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

    def _plot_calibration_data(self):
        """
        Plots the integrated ion current vs dosage.
        """
        self.ax.clear()
        self.ax.scatter(self.dosages, self.integrated_values, marker="o", color="red", label="TPD Integrals")

        # Compute Linear Regression (Line of Best Fit)
        slope, intercept = np.polyfit(self.dosages, self.integrated_values, 1)  # Fit y = mx + b
        best_fit_line = slope * self.dosages + intercept

        # Plot Best-Fit Line
        self.ax.plot(self.dosages, best_fit_line, linestyle="-", color="blue", label="Linear Fit")

        self.ax.set_xlabel("Dosage (K arb.u.)")
        self.ax.set_ylabel("TPD Integral")
        self.ax.set_title("Linearity")
        self.ax.grid(True)

        self.plot_canvas.draw()
        
    def _toggle_legend(self):
        """
        Toggles legend visibility.
        """
        self.legend.set_visible(not self.legend.get_visible())
        self.plot_canvas.draw()