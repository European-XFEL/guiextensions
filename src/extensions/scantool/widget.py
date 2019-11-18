from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QWidget


def get_container(parent, layout=QVBoxLayout()):
    widget = ContainerWidget(parent)
    widget.setLayout(layout)
    return widget


class ContainerWidget(QWidget):

    def __init__(self, parent=None):
        super(ContainerWidget, self).__init__(parent)

    # -----------------------------------------------------------------------
    # Public methods

    def add_widget(self, widget, **coords):
        layout = self.layout()
        if layout is None:
            return

        if isinstance(layout, QGridLayout):
            row, col = coords["row"], coords["col"] if coords else (0, 0)
            layout.addWidget(widget, row, col)
        else:
            layout.addWidget(widget)

    def remove_widget(self, widget):
        self.layout().removeWidget(widget)
