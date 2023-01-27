from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from ui.ui_app import Ui_MainWindow


class App(QMainWindow, Ui_MainWindow):
    star_sig = pyqtSignal(str)
    pause_sig = pyqtSignal(str)
    stop_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setupUi(self)
        self.star_sig.connect(self.handle_start)
        self.pause_sig.connect(self.handle_pause)
        self.stop_sig.connect(self.handle_stop)

    def handle_start(self):
        pass

    def handle_pause(self):
        pass

    def handle_stop(self):
        pass
