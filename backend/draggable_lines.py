from matplotlib.lines import Line2D

class DraggableLines:
    """
    A class for adding and manipulating draggable vertical trim lines on a Matplotlib axis.
    
    This allows users to adjust trim boundaries interactively by clicking and dragging the lines.

    Attributes:
        ax (matplotlib.axes.Axes): The axis where the lines are drawn.
        lines (list of Line2D): List containing the start and end trim lines.
        detection_range (float): Range in which a trim line is detected for interaction.
        selected_line (Line2D or None): The currently selected line for dragging.
        is_dragging (bool): Whether a line is being dragged.
        trim_boundaries (tuple of float, optional): Initial positions (start, end) for the trim lines.
    """
    def __init__(self, ax, trim_boundaries):
        """
        Initialises draggable trim lines on a Matplotlib axis.

        :param ax: Matplotlib axis where the lines will be drawn
        :param trim_boundaries: Tuple (start, end) specifying initial trim positions
        """
        self.ax = ax
        self.figure = ax.figure
        self.canvas = self.figure.canvas
        self.lines = []

        self.selected_line = None  # Track the selected line
        self.is_dragging = False  # Track dragging state
        self.detection_range = 2.0 # Detection window of lines
        
        # Connect event handlers
        self.cid_hover = self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.cid_click = self.canvas.mpl_connect("button_press_event", self._on_click)
        self.cid_drag = self.canvas.mpl_connect("motion_notify_event", self._on_drag)
        self.cid_release = self.canvas.mpl_connect("button_release_event", self._on_release)

        # If trim boundaries already exist, they are automatically added to the plot
        if trim_boundaries is not None:
            self.add_trim_lines(trim_boundaries)

    def add_trim_lines(self, trim_boundaries=None):
        """
        Adds trim lines at specified positions or defaults near graph edges.

        :param trim_boundaries: Tuple (start, end) or None to place lines at default positions.
        """
        if trim_boundaries is not None:
            x1, x2 = trim_boundaries  
        else:
            x_min, x_max = self.ax.get_xlim()
            x1, x2 = x_min + 10, x_max - 10  

        # Create vertical lines
        self.lines.append(Line2D([x1, x1], self.ax.get_ylim(), color="r", linestyle="-", linewidth=2, label="Start Trim"))
        self.lines.append(Line2D([x2, x2], self.ax.get_ylim(), color="g", linestyle="-", linewidth=2, label="End Trim"))

        for line in self.lines:
            self.ax.add_line(line)

        self.canvas.draw()

    def _on_hover(self, event):
        """
        Changes cursor when hovering near a trim line.
        """
        if event.inaxes != self.ax or event.xdata is None:
            return

        for line in self.lines:
            if abs(event.xdata - line.get_xdata()[0]) < self.detection_range:
                self.canvas.set_cursor(6)  # Horizontal resize cursor
                return

        self.canvas.set_cursor(1)  # Default cursor

    def _on_click(self, event):
        """
        Selects a trim line when clicked.
        """
        if event.inaxes != self.ax or event.xdata is None:
            return

        for line in self.lines:
            if abs(event.xdata - line.get_xdata()[0]) < self.detection_range:
                self.selected_line = line
                self.is_dragging = True
                return

        self.selected_line = None

    def _on_drag(self, event):
        """
        Moves the selected trim line while dragging.
        """
        if not self.is_dragging or self.selected_line is None or event.xdata is None:
            return

        # Get current positions
        start_x = self.lines[0].get_xdata()[0]  # Start Trim
        end_x = self.lines[1].get_xdata()[0]  # End Trim
        new_x = event.xdata  # Proposed new position

        # Prevent lines from crossing over
        if self.selected_line == self.lines[0]:  
            if new_x >= end_x:
                return  
        elif self.selected_line == self.lines[1]:  
            if new_x <= start_x:
                return  

        # Apply new position
        self.selected_line.set_xdata([new_x, new_x])
        self.canvas.draw()

    def _on_release(self, _):
        """
        Ends dragging when mouse is released.
        """
        self.selected_line = None
        self.is_dragging = False

    def get_trim_positions(self):
        """
        Returns the current trim line positions.
        """
        return self.lines[0].get_xdata()[0], self.lines[1].get_xdata()[0]
    