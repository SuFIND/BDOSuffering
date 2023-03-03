# -*- coding: utf-8 -*-

from PyQt6 import QtWidgets

from ui.ui_about import Ui_Dialog


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent, *args):
        super(AboutDialog, self).__init__(parent, *args)
        self.viewer = Ui_Dialog()
        self.viewer.setupUi(self)
