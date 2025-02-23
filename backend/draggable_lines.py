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
    def __init__(self, ax):
        """
        Initialises draggable trim lines on a Matplotlib axis.

        :param ax: Matplotlib axis where the lines will be drawn
        """
        self.ax = ax
        self.figure = ax.figure
        self.canvas = self.figure.canvas
        self.lines = {"trim": [], "integration_1": [], "integration_2": []}  # Store multiple sets

        self.selected_line = None  # Track the selected line
        self.is_dragging = False  # Track dragging state
        self.detection_range = 2.0  # Detection window for interaction

        # Connect event handlers
        self.cid_hover = self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.cid_click = self.canvas.mpl_connect("button_press_event", self._on_click)
        self.cid_drag = self.canvas.mpl_connect("motion_notify_event", self._on_drag)
        self.cid_release = self.canvas.mpl_connect("button_release_event", self._on_release)

    def add_trim_lines(self, trim_boundaries=None, line_type="trim"):
        """
        Adds trim lines at specified positions or defaults near graph edges.

        :param trim_boundaries: Tuple (start, end) or None to place lines at default positions.
        :param line_type: "trim" (red), "integration_1" (blue, 15-25% left), or "integration_2" (orange, 15-25% right).
        """
        if line_type not in self.lines:
            raise ValueError("Invalid line_type. Must be 'trim', 'integration_1', or 'integration_2'.")

        x_min, x_max = self.ax.get_xlim()  # Get current x-axis range

        if line_type == "trim":
            # Keep trimming behavior unchanged (default placement if not provided)
            if trim_boundaries is not None:
                x1, x2 = trim_boundaries
            else:
                x1, x2 = x_min + 10, x_max - 10  

        elif line_type == "integration_1":
            # Place 15% and 25% from the left
            x1 = x_min + 0.15 * (x_max - x_min)
            x2 = x_min + 0.25 * (x_max - x_min)

        elif line_type == "integration_2":
            # Place 15% and 25% from the right
            x1 = x_max - 0.25 * (x_max - x_min)
            x2 = x_max - 0.15 * (x_max - x_min)

        # Define colors for different line sets
        color_map = {"trim": "r", "integration_1": "b", "integration_2": "orange"}
        color = color_map[line_type]

        # Create vertical lines
        line1 = Line2D([x1, x1], self.ax.get_ylim(), color=color, linestyle="-", linewidth=2, label=f"{line_type} Start")
        line2 = Line2D([x2, x2], self.ax.get_ylim(), color=color, linestyle="-", linewidth=2, label=f"{line_type} End")

        # Store lines in the dictionary
        self.lines[line_type] = [line1, line2]

        for line in self.lines[line_type]:
            self.ax.add_line(line)

        self.canvas.draw()

    def _on_hover(self, event):
        """ 
        Changes cursor when hovering near a trim line. 
        """
        if event.inaxes != self.ax or event.xdata is None:
            if hasattr(self, "_cursor_changed") and self._cursor_changed:
                self.canvas.set_cursor(1)
                self._cursor_changed = False
            return

        for line_set in self.lines.values():
            for line in line_set:
                if abs(event.xdata - line.get_xdata()[0]) < self.detection_range:
                    self.canvas.set_cursor(6)  # Horizontal resize cursor
                    self._cursor_changed = True
                    return

        if hasattr(self, "_cursor_changed") and self._cursor_changed:
            self.canvas.set_cursor(1)
            self._cursor_changed = False

    def _on_click(self, event):
        """ 
        Selects a trim line when clicked. 
        """
        if event.inaxes != self.ax or event.xdata is None:
            return

        for line_set in self.lines.values():
            for line in line_set:
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
        for line_set in self.lines.values():
            if self.selected_line in line_set:
                start_x = line_set[0].get_xdata()[0]  # Start Line
                end_x = line_set[1].get_xdata()[0]  # End Line
                new_x = event.xdata  # Proposed new position

                # Prevent lines from crossing over
                if self.selected_line == line_set[0]:  
                    if new_x >= end_x:
                        return  
                elif self.selected_line == line_set[1]:  
                    if new_x <= start_x:
                        return  

                # Apply new position
                self.selected_line.set_xdata([new_x, new_x])
                self.canvas.draw()
                return

    def _on_release(self, _):
        """ 
        Ends dragging when mouse is released. 
        """
        self.selected_line = None
        self.is_dragging = False

    def get_trim_positions(self, line_type="trim"):
        """
        Returns the current trim line positions for a given type.

        :param line_type: "trim", "integration_1", or "integration_2"
        :return: Tuple (start_x, end_x) for the specified line type
        """
        if line_type not in self.lines or not self.lines[line_type]:
            return None

        return self.lines[line_type][0].get_xdata()[0], self.lines[line_type][1].get_xdata()[0]

    