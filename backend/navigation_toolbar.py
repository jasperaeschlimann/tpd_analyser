from PyQt5.QtWidgets import QPushButton
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class CustomNavigationToolbar(NavigationToolbar):
    """
    A custom navigation toolbar with a toggle legend button.
    """
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)
        self.canvas = canvas
        self.add_legend_toggle_button()

    def add_legend_toggle_button(self):
        """Add a custom button to toggle legends."""
        # Create the button
        toggle_button = QPushButton("Toggle Legend")
        toggle_button.clicked.connect(self.toggle_legends)
        # Add the button to the toolbar
        self.addWidget(toggle_button)

    def toggle_legends(self):
        """Toggle the visibility of legends in all axes."""
        for ax in self.canvas.figure.axes:
            legend = ax.get_legend()
            if legend is not None:
                legend.set_visible(not legend.get_visible())
        self.canvas.draw()  # Redraw the canvas to apply changes
