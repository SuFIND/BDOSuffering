from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from ui.ui_app import Ui_MainWindow
from system_hotkey import SystemHotkey


class App(QMainWindow, Ui_MainWindow):
    sig_hotkey = pyqtSignal(str)

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setupUi(self)

        self.hk_start_pause = SystemHotkey()
        self.hk_stop = SystemHotkey()

        self.sig_hotkey.connect(self.handleHotKeyEvent)
        self.hk_start_pause.register(('f10',), callback=lambda x: self.sendHotKeySig('f10'))
        self.hk_stop.register(('f11',), callback=lambda x: self.sendHotKeySig('f11'))

    def sendHotKeySig(self, i_str):
        self.sig_hotkey.emit(i_str)

    def handleHotKeyEvent(self, i_str):
        if i_str == 'f10':
            # 开始 / 暂停
            self.OpCtrl.clicked_for_start_pause_button()
        if i_str == 'f11':
            # 停止
            self.OpCtrl.clicked_for_end_button()
