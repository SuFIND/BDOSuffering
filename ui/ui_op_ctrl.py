# Form implementation generated from reading ui file 'designer/op.ui'
#
# Created by: PyQt6 UI code generator 6.4.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_OpCtrl(object):
    def setupUi(self, OpCtrl):
        OpCtrl.setObjectName("OpCtrl")
        OpCtrl.resize(609, 344)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(OpCtrl)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(parent=OpCtrl)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.UseWarehouseMaidCheckBox = QtWidgets.QCheckBox(parent=self.frame)
        self.UseWarehouseMaidCheckBox.setChecked(True)
        self.UseWarehouseMaidCheckBox.setObjectName("UseWarehouseMaidCheckBox")
        self.gridLayout.addWidget(self.UseWarehouseMaidCheckBox, 4, 1, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.frame)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
        self.WarehouseMaidkeySequenceEdit = QtWidgets.QKeySequenceEdit(parent=self.frame)
        self.WarehouseMaidkeySequenceEdit.setObjectName("WarehouseMaidkeySequenceEdit")
        self.gridLayout.addWidget(self.WarehouseMaidkeySequenceEdit, 4, 3, 1, 1)
        self.RepairWeaponsCheckBox = QtWidgets.QCheckBox(parent=self.frame)
        self.RepairWeaponsCheckBox.setChecked(True)
        self.RepairWeaponsCheckBox.setObjectName("RepairWeaponsCheckBox")
        self.gridLayout.addWidget(self.RepairWeaponsCheckBox, 5, 1, 1, 1)
        self.RepairWeaponskeySequenceEdit = QtWidgets.QKeySequenceEdit(parent=self.frame)
        self.RepairWeaponskeySequenceEdit.setObjectName("RepairWeaponskeySequenceEdit")
        self.gridLayout.addWidget(self.RepairWeaponskeySequenceEdit, 6, 3, 1, 1)
        self.SetTentSequenceEdit = QtWidgets.QKeySequenceEdit(parent=self.frame)
        self.SetTentSequenceEdit.setObjectName("SetTentSequenceEdit")
        self.gridLayout.addWidget(self.SetTentSequenceEdit, 5, 3, 1, 1)
        self.label_6 = QtWidgets.QLabel(parent=self.frame)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 6, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(parent=self.frame)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 9, 1, 1, 1)
        self.RecycleTentkeySequenceEdit = QtWidgets.QKeySequenceEdit(parent=self.frame)
        self.RecycleTentkeySequenceEdit.setObjectName("RecycleTentkeySequenceEdit")
        self.gridLayout.addWidget(self.RecycleTentkeySequenceEdit, 7, 3, 1, 1)
        self.label_5 = QtWidgets.QLabel(parent=self.frame)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 5, 2, 1, 1)
        self.ResetViewCheckBox = QtWidgets.QCheckBox(parent=self.frame)
        self.ResetViewCheckBox.setChecked(True)
        self.ResetViewCheckBox.setTristate(False)
        self.ResetViewCheckBox.setObjectName("ResetViewCheckBox")
        self.gridLayout.addWidget(self.ResetViewCheckBox, 1, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.frame)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 4, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.frame)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(parent=self.frame)
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 7, 2, 1, 1)
        self.AuditionAlarmButton = QtWidgets.QPushButton(parent=self.frame)
        self.AuditionAlarmButton.setObjectName("AuditionAlarmButton")
        self.gridLayout.addWidget(self.AuditionAlarmButton, 10, 2, 1, 1)
        self.IntoHuttonCheckBox = QtWidgets.QCheckBox(parent=self.frame)
        self.IntoHuttonCheckBox.setTristate(False)
        self.IntoHuttonCheckBox.setObjectName("IntoHuttonCheckBox")
        self.gridLayout.addWidget(self.IntoHuttonCheckBox, 10, 1, 1, 1)
        self.BackExchaneCheckBox = QtWidgets.QCheckBox(parent=self.frame)
        self.BackExchaneCheckBox.setChecked(True)
        self.BackExchaneCheckBox.setObjectName("BackExchaneCheckBox")
        self.gridLayout.addWidget(self.BackExchaneCheckBox, 8, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(parent=OpCtrl)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.StartPauseButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.StartPauseButton.setObjectName("StartPauseButton")
        self.horizontalLayout.addWidget(self.StartPauseButton)
        self.EndButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.EndButton.setObjectName("EndButton")
        self.horizontalLayout.addWidget(self.EndButton)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.frame_2)
        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(OpCtrl)
        QtCore.QMetaObject.connectSlotsByName(OpCtrl)

    def retranslateUi(self, OpCtrl):
        _translate = QtCore.QCoreApplication.translate
        OpCtrl.setWindowTitle(_translate("OpCtrl", "Form"))
        self.UseWarehouseMaidCheckBox.setToolTip(_translate("OpCtrl", "需要至少有4个仓库女仆，存放：記憶的碎片、獵人勛章、以及兩種召喚怪物掉落的雜物"))
        self.UseWarehouseMaidCheckBox.setText(_translate("OpCtrl", "女仆存放杂物"))
        self.label.setText(_translate("OpCtrl", "开始前"))
        self.WarehouseMaidkeySequenceEdit.setKeySequence(_translate("OpCtrl", "1"))
        self.RepairWeaponsCheckBox.setToolTip(_translate("OpCtrl", "需要购买珍珠商品帐篷"))
        self.RepairWeaponsCheckBox.setText(_translate("OpCtrl", "帐篷修理装备"))
        self.RepairWeaponskeySequenceEdit.setKeySequence(_translate("OpCtrl", "4"))
        self.SetTentSequenceEdit.setKeySequence(_translate("OpCtrl", "3"))
        self.label_6.setText(_translate("OpCtrl", "帐篷修理 alt +"))
        self.label_4.setText(_translate("OpCtrl", "其他"))
        self.RecycleTentkeySequenceEdit.setKeySequence(_translate("OpCtrl", "5"))
        self.label_5.setText(_translate("OpCtrl", "设置帐篷 alt +"))
        self.ResetViewCheckBox.setText(_translate("OpCtrl", "重置到最大视野"))
        self.label_2.setText(_translate("OpCtrl", "仓库女仆 alt +"))
        self.label_3.setText(_translate("OpCtrl", "结束后"))
        self.label_7.setText(_translate("OpCtrl", "回收帐篷 alt +"))
        self.AuditionAlarmButton.setText(_translate("OpCtrl", "试听GM警报"))
        self.IntoHuttonCheckBox.setToolTip(_translate("OpCtrl", "需要确认所在线是否可以进入赫顿领域，赛季及新手线不支持"))
        self.IntoHuttonCheckBox.setText(_translate("OpCtrl", "进入赫顿领域"))
        self.BackExchaneCheckBox.setText(_translate("OpCtrl", "回到交易所"))
        self.StartPauseButton.setText(_translate("OpCtrl", "开始 F10"))
        self.EndButton.setText(_translate("OpCtrl", "结束 F11"))
