# -*- coding: utf-8 -*-
import copy as cp

from PyQt6 import QtWidgets
from ui.ui_skill_group_edit_dialog_ctrl import Ui_Dialog

KB_ACTION = {"KBPress", "KBRelease", "KBPressAndRelease"}
MS_ACTION = {"MSClick"}
OTHER_ACTION = {"wait"}


class SkillGroupEditDialog(QtWidgets.QDialog):
    simulation_items = {
        "键盘按键按下": "KBPress",
        "键盘按键释放": "KBRelease",
        "键盘按下并释放": "KBPressAndRelease",
        "鼠标点击": "MSClick",
        "等待": "wait",
    }

    def __init__(self, parent):
        super(SkillGroupEditDialog, self).__init__(parent)
        self.viewer = Ui_Dialog()
        self.viewer.setupUi(self)

        # 初始化数据部分
        self.group_data = []
        self.temp_block_idx = None
        self.temp_block = None
        self.temp_block_action_idx = None
        self.temp_block_action = None
        self.init_simulation_select()
        self.refresh_simulation_args()

        # 信号槽
        self.viewer.EditSkillModel.clicked.connect(self.refresh_skill_model)
        self.viewer.AddSkillModel.clicked.connect(self.refresh_skill_model)
        self.viewer.EditActionModel.clicked.connect(self.refresh_action_model)
        self.viewer.AddActionModel.clicked.connect(self.refresh_action_model)

        self.viewer.addSkillButton.clicked.connect(self.handel_add_skill_button)
        self.viewer.delSkillButton.clicked.connect(self.handel_del_skill_button)
        self.viewer.AddActionButton.clicked.connect(self.handel_add_action_button)
        self.viewer.delActionButton.clicked.connect(self.handel_del_action_button)

        self.viewer.simulationSelect.currentTextChanged.connect(self.handel_simulation_selection_change)
        self.viewer.SkillListWidget.itemClicked.connect(self.handel_skill_item_select_change)
        self.viewer.ActionListWidget.itemClicked.connect(self.handel_action_item_select_change)

        # 其他
        self.viewer.SkillListWidget.dropEvent = self.overload_SkillListWidget_dropEvent
        self.viewer.ActionListWidget.dropEvent = self.overload_ActionListWidget_dropEvent

    def set_group_data(self, data: list):
        self.group_data = cp.copy(data)
        self.refresh_skill_list_widget()

    def init_simulation_select(self):
        for desc, _ in self.simulation_items.items():
            self.viewer.simulationSelect.addItem(desc)

    def refresh_skill_list_widget(self):
        self.viewer.SkillListWidget.clear()
        for one in self.group_data:
            item = QtWidgets.QListWidgetItem(self.viewer.SkillListWidget)
            item.setData(0, one["name"])
            item.setData(1, one)
            self.viewer.SkillListWidget.addItem(item)

    def refresh_simulation_args(self, aType=None):
        cur_block_index = self.viewer.SkillListWidget.currentIndex()
        cur_pipelines_index = self.viewer.ActionListWidget.currentIndex()
        block_idx = cur_block_index.row()
        pipe_idx = cur_pipelines_index.row()

        if block_idx >= 0 and pipe_idx >= 0:
            block_idx = cur_block_index.row()
            pipe_idx = cur_pipelines_index.row()
            data = self.group_data[block_idx]["pipelines"][pipe_idx]
        else:
            data = {
                "type": "KBPress",
                "key": "",
            }

        aType = data["type"] if aType is None else aType
        if aType in KB_ACTION:
            self.viewer.label_3.setText("按键")
            if not isinstance(self.viewer.simulationArg1, QtWidgets.QLineEdit):
                self.viewer.simulationArg1 = QtWidgets.QLineEdit(parent=self.viewer.R4Frame)
            self.viewer.simulationArg1.setText(data.get("key", ""))
        elif aType in MS_ACTION:
            self.viewer.label_3.setText("按键")
            if not isinstance(self.viewer.simulationArg1, QtWidgets.QComboBox):
                self.viewer.simulationArg1 = QtWidgets.QComboBox(parent=self.viewer.R4Frame)
                self.viewer.simulationArg1.addItems(["left", "right"])
            self.viewer.simulationArg1.setCurrentText(data.get("key", ""))
        elif aType in OTHER_ACTION:
            self.viewer.label_3.setText("秒")
            if not isinstance(self.viewer.simulationArg1, QtWidgets.QLineEdit):
                self.viewer.simulationArg1 = QtWidgets.QLineEdit(parent=self.viewer.R4Frame)
            self.viewer.simulationArg1.setText(str(data.get("sec", 0)))
        self.viewer.simulationArg1.setObjectName("simulationArg1")
        self.viewer.gridLayout_5.addWidget(self.viewer.simulationArg1, 3, 1, 1, 1)

    def refresh_action_list_widget(self):
        cur_block_index = self.viewer.SkillListWidget.currentIndex()
        block_idx = cur_block_index.row()
        self.viewer.ActionListWidget.clear()
        if block_idx >= 0:
            block_idx = cur_block_index.row()
            for job in self.group_data[block_idx]["pipelines"]:
                job_name = self._build_action_desc(job)
                item = QtWidgets.QListWidgetItem(parent=self.viewer.ActionListWidget)
                item.setData(0, job_name)
                item.setData(1, job)
                self.viewer.ActionListWidget.addItem(item)

    def refresh_action_model(self):
        """
        刷新UI对编辑模式和刷新模式调整展示
        :return:
        """
        if self.viewer.EditActionModel.isChecked():
            self.viewer.AddActionButton.setText("保存动作")
            self.viewer.delActionButton.setEnabled(True)
        if self.viewer.AddActionModel.isChecked():
            self.viewer.AddActionButton.setText("添加动作")
            self.viewer.delActionButton.setEnabled(False)

    def refresh_skill_model(self):
        """
        刷新UI对编辑模式和刷新模式调整展示
        :return:
        """
        if self.viewer.EditSkillModel.isChecked():
            self.viewer.addSkillButton.setText("保存该技能")
            self.viewer.delSkillButton.setEnabled(True)
        if self.viewer.AddSkillModel.isChecked():
            self.viewer.addSkillButton.setText("新增该技能")
            self.viewer.delSkillButton.setEnabled(False)

    def _build_action_desc(self, job):
        """
        构建中间动作列表的列表项说明
        :param job:
        :return:
        """
        _ = dict()
        for v, k in self.simulation_items.items():
            _[k] = v

        prefix = _[job["type"]]
        middle = ""
        if job["type"] == "MSClick" and job["key"] == "left":
            middle = "左键"
        elif job["type"] == "MSClick" and job["key"] == "right":
            middle = "右键"
        elif job["type"] in KB_ACTION:
            middle = job["key"]
        elif job["type"] == "wait":
            middle = str(job["sec"]) + "秒"
        return prefix + middle

    def handel_simulation_selection_change(self):
        """
        处理动作方式改变时的参数显示
        :return:
        """
        aType = self.simulation_items[self.viewer.simulationSelect.currentText()]
        self.refresh_simulation_args(aType=aType)

    def handel_skill_item_select_change(self):
        cur_skill_item = self.viewer.SkillListWidget.currentItem()
        if cur_skill_item:
            self.viewer.skillNameEdit.setText(cur_skill_item.data(0))
            self.viewer.EditSkillModel.setChecked(True)
            self.refresh_skill_model()
            self.refresh_action_list_widget()

    def handel_action_item_select_change(self):
        cur_action_item = self.viewer.ActionListWidget.currentItem()
        if cur_action_item:
            _ = dict()
            for v, k in self.simulation_items.items():
                _[k] = v

            data = cur_action_item.data(1)
            self.viewer.simulationSelect.setCurrentText(_[data["type"]])
            self.viewer.EditActionModel.setChecked(True)
            self.refresh_action_model()
            self.refresh_simulation_args()

    def handel_add_skill_button(self):
        """
        添加或保存技能名称变动的逻辑
        :return:
        """
        if self.viewer.AddSkillModel.isChecked():
            new_struct = {
                "name": self.viewer.skillNameEdit.text(),
                "pipelines": []
            }
            self.group_data.append(new_struct)

            # 将动作的交互模式置为新增
            self.viewer.AddActionModel.setChecked(True)
            # 刷新UI
            self.refresh_skill_list_widget()
            self.refresh_action_model()
            self.refresh_action_list_widget()
        if self.viewer.EditSkillModel.isChecked():
            cur_row = self.viewer.SkillListWidget.currentRow()
            if cur_row >= 0:
                self.group_data[cur_row]["name"] = self.viewer.skillNameEdit.text()
                self.refresh_skill_list_widget()
            else:
                QtWidgets.QMessageBox.information(self, "提示", "请先选择一个已存在的技能再进行编辑！")

    def handel_del_skill_button(self):
        """
        删除技能的逻辑
        :return:
        """
        cur_row = self.viewer.SkillListWidget.currentRow()
        if cur_row >= 0:
            del self.group_data[cur_row]
            self.refresh_skill_list_widget()
            self.refresh_action_list_widget()
        else:
            QtWidgets.QMessageBox.information(self, "提示", "请先选择一个已存在的技能再进行删除！")

    def handel_add_action_button(self):
        """
        添加或保存技能名称变动的逻辑
        :return:
        """
        cur_block_index = self.viewer.SkillListWidget.currentIndex()
        block_idx = cur_block_index.row()
        sim_type = self.simulation_items[self.viewer.simulationSelect.currentText()]
        struct = {
            "type": sim_type,
        }
        if sim_type in KB_ACTION:
            struct["key"] = self.viewer.simulationArg1.text()
        if sim_type in MS_ACTION:
            struct["key"] = self.viewer.simulationArg1.currentText()
        if sim_type in OTHER_ACTION:
            try:
                struct["sec"] = float(self.viewer.simulationArg1.text())
            except ValueError:
                dialog = QtWidgets.QMessageBox(self)
                dialog.setText("存在部分动作应该的参数应该为数值类型，但是输入了其他的内容！")
                return

        if block_idx >= 0:
            if self.viewer.AddActionModel.isChecked():
                self.group_data[block_idx]["pipelines"].append(struct)
                self.refresh_action_list_widget()

            if self.viewer.EditActionModel.isChecked():
                cur_pipeline_index = self.viewer.ActionListWidget.currentIndex()
                if cur_pipeline_index:
                    pipe_idx = cur_pipeline_index.row()
                    self.group_data[block_idx]["pipelines"][pipe_idx] = struct
                    self.refresh_action_list_widget()
        else:
            QtWidgets.QMessageBox.information(self, "提示", "请先选择一个已存在技能中的动作再进行编辑！")

    def handel_del_action_button(self):
        """
        删除技能的逻辑
        :return:
        """
        cur_block_index = self.viewer.SkillListWidget.currentIndex()
        cur_pipeline_index = self.viewer.ActionListWidget.currentIndex()
        if cur_block_index is not None and cur_pipeline_index is not None:
            block_idx = cur_block_index.row()
            pipe_idx = cur_pipeline_index.row()
            del self.group_data[block_idx]["pipelines"][pipe_idx]
            self.refresh_action_list_widget()
        else:
            QtWidgets.QMessageBox.information(self, "提示", "请先选择一个已存在的技能中的动作再进行删除！")

    def overload_SkillListWidget_dropEvent(self, event):
        super(QtWidgets.QListWidget, self.viewer.SkillListWidget).dropEvent(event)
        new_group_data = []
        for cur_row in range(self.viewer.SkillListWidget.count()):
            item = self.viewer.SkillListWidget.item(cur_row)
            new_group_data.append(item.data(1))
        self.group_data = new_group_data
        self.refresh_skill_list_widget()
        self.refresh_action_list_widget()

    def overload_ActionListWidget_dropEvent(self, event):
        block_idx = self.viewer.SkillListWidget.currentRow()
        if block_idx >= 0:
            super(QtWidgets.QListWidget, self.viewer.ActionListWidget).dropEvent(event)
            new_pipelines = []
            for pipe_idx in range(self.viewer.ActionListWidget.count()):
                item = self.viewer.ActionListWidget.item(pipe_idx)
                new_pipelines.append(item.data(1))
            self.group_data[block_idx]["pipelines"] = new_pipelines
            self.refresh_action_list_widget()
        else:
            QtWidgets.QMessageBox.information(self, "提示", "请先选择一个要编辑的技能，之后才能编辑技能内部的动作顺序！")

    def collect(self):
        return self.group_data
