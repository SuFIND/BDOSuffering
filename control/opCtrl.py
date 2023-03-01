import datetime
import traceback

from PyQt6 import QtWidgets, QtCore
from ui.ui_op_ctrl import Ui_OpCtrl
from app.init_resource import global_var
from operation.v2 import start_action, start_merge
from operation.gm_check import GM_check_loop
from utils.log_utils import Logger


class OpCtrl(QtWidgets.QWidget):
    button_sig = QtCore.pyqtSignal(str)

    def __init__(self, parent, logCtrl, *args):
        super(OpCtrl, self).__init__(parent, *args)

        self.LogCtrl = logCtrl

        self.viewer = Ui_OpCtrl()
        self.viewer.setupUi(self)
        self.other_init()

        self.viewer.StartPauseButton.clicked.connect(self.clicked_for_start_pause_button)
        self.viewer.EndButton.clicked.connect(self.clicked_for_end_button)
        self.viewer.AuditionAlarmButton.clicked.connect(self.handle_audition_alarm)
        self.viewer.MergeALButton.clicked.connect(self.clicked_for_al_button)
        self.viewer.TestButton.clicked.connect(self.handel_test_button)

        self.button_sig.connect(self.handel_button_logic)

    def other_init(self):
        # 根据 global_var 中标志变量的情况设置GUI控件的可编辑情况
        if not global_var["enable_email"]:
            self.viewer.EmailEdit.setDisabled(True)
            self.viewer.EmailAlarmCheckBox.setDisabled(True)

    def clicked_for_start_pause_button(self):
        button_flag = self.viewer.StartPauseButton.text()
        if button_flag == "开始 F10":
            self.button_sig.emit("start")
        elif button_flag == "暂停 F10":
            self.button_sig.emit("pause")

    def clicked_for_end_button(self):
        self.button_sig.emit("stop")

    def clicked_for_al_button(self):
        self.button_sig.emit("mergeAL")

    def handel_button_logic(self, sig):
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        if sig == "start":
            # 来自GUI可视化配置的资源
            available, gui_params, reason = self.collect()
            if not available:
                msgBox = QtWidgets.QMessageBox(self)
                msgBox.setText(reason)
                msgBox.show()
                return

            # 初始化信号量
            with sig_mutex:
                sig_dic.update({"start": True, "pause": False, "stop": False})
            # 从全局变量中获取进程所需资源
            debug = global_var["debug"]
            process_pool = global_var["process_pool"]
            sig_dic = global_var["process_sig"]
            sig_mutex = global_var["process_sig_lock"]
            msg_queue = global_var["process_msg_queue"]
            window_title = global_var['BDO_window_title']
            window_class = global_var['BDO_window_class']
            window_title_bar_height = global_var["BDO_window_title_bar_height"]

            # #GM检测想关资源
            gm_check_cool_time = global_var["gm_check_cool_time"]
            gm_chat_color = global_var["gm_chat_color"]
            gm_find_pix_max_count = global_var["gm_find_pix_max_count"]

            # 模型相关的资源
            onnx_file_path = global_var["onnx_file_path"]
            classes_id_file_path = global_var["classes_id_file_path"]

            # 启动打三角进程
            process_pool.submit(start_action, sig_dic, sig_mutex, msg_queue, window_title, window_class,
                                window_title_bar_height, onnx_file_path, classes_id_file_path, gui_params, debug)

            # 启动GM守护进程
            process_pool.submit(GM_check_loop, sig_dic, sig_mutex, msg_queue, window_title, window_class,
                                gm_chat_color, gm_check_cool_time, gm_find_pix_max_count)
            # 并重置按钮文字为暂停
            self.viewer.StartPauseButton.setText("暂停 F10")

        elif sig == "pause":
            self.LogCtrl.add_log(msg="暂停")
            # 释放暂停信号
            with sig_mutex:
                sig_dic.update({"stop": False, "start": False, "pause": True})

            # 并重置按钮文字为开始
            self.viewer.StartPauseButton.setText("开始 F10")

        elif sig == "stop":
            # 释放结束信号
            with sig_mutex:
                sig_dic.update({"stop": True, "start": False, "pause": False})

            self.LogCtrl.add_log("手动停止")
        elif sig == "refresh_display:pause":
            self.viewer.StartPauseButton.setText("暂停 F10")
        elif sig == "refresh_display:start":
            self.viewer.StartPauseButton.setText("开始 F10")
        elif sig == "mergeAL":
            # 来自GUI可视化配置的资源
            available, gui_params, reason = self.collect()
            if not available:
                msgBox = QtWidgets.QMessageBox(self)
                msgBox.setText(reason)
                msgBox.show()
                return

            with sig_mutex:
                sig_dic.update({"start": True, "pause": False, "stop": False})
            # 从全局变量中获取进程所需资源
            debug = global_var["debug"]
            process_pool = global_var["process_pool"]
            sig_dic = global_var["process_sig"]
            sig_mutex = global_var["process_sig_lock"]
            msg_queue = global_var["process_msg_queue"]
            window_title = global_var['BDO_window_title']
            window_class = global_var['BDO_window_class']
            window_title_bar_height = global_var["BDO_window_title_bar_height"]

            # 模型相关的资源
            onnx_file_path = global_var["onnx_file_path"]
            classes_id_file_path = global_var["classes_id_file_path"]

            process_pool.submit(start_merge, sig_dic, sig_mutex, msg_queue, window_title, window_class,
                                window_title_bar_height, onnx_file_path, classes_id_file_path, debug, gui_params)

    def handle_audition_alarm(self):
        q = global_var["process_msg_queue"]
        mutex = global_var["process_sig_lock"]
        dic = global_var["process_sig"]
        with mutex:
            dic.update({"stop": False})
        q.put("action::show_gm_modal")

    def handel_test_button(self):
        available, gui_params, reason = self.collect()
        if not available:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText(reason)
            msgBox.show()
        else:
            print(gui_params)

    def collect(self) -> (bool, dict, str):
        """
        收集GUI上的所有配置设置打包成一个数据字典
        :return:
        """
        available = True
        rst = {}
        reason = ""

        # 重置最大视角
        resetView = self.viewer.ResetViewCheckBox.isChecked()
        # 从交易所开始
        startAtTradingWarehouse = self.viewer.StartAtTradingWarehouseButton.isChecked()
        # 从球点开始
        startAtCallPlace = self.viewer.StartAtCallPlaceButton.isChecked()
        # 仓库女仆
        useWarehouseMaid = self.viewer.UseWarehouseMaidCheckBox.isChecked()
        # 仓库女仆快捷键
        useWarehouseMaidShortcut = self.viewer.WarehouseMaidkeySequenceEdit.keySequence()
        # 使用帐篷维修武器
        repairWeapons = self.viewer.RepairWeaponsCheckBox.isChecked()
        # 设置帐篷的快捷键
        setTentShortcut = self.viewer.SetTentSequenceEdit.keySequence()
        # 帐篷修理武器的快捷键
        tentRepairWeaponsShortcut = self.viewer.RepairWeaponskeySequenceEdit.keySequence()
        # 回收帐篷的快捷键
        recycleTentShortcut = self.viewer.RecycleTentkeySequenceEdit.keySequence()
        # 打完球后是否回到交易所
        backExchange = self.viewer.BackExchangeCheckBox.isChecked()
        # 如果可以进入赫顿领域，是否要进入赫顿打球
        intoHutton = self.viewer.IntoHuttonCheckBox.isChecked()

        boss1CanBeHitCoolTimeStr = self.viewer.Boss1CanBeHitCoolTimeEdit.text()
        boss2CanBeHitCoolTimeStr = self.viewer.Boss2CanBeHitCoolTimeEdit.text()
        skillGroup1KillBoss1CostStr = self.viewer.SkillGroup1KillBoss1CostEdit.text()
        backTradingHouseTimeStr = self.viewer.backTradingHouseTimeEdit.text()

        to_checks = [
            # BasicTab
            ("resetView", resetView, "", None),
            ("startAtTradingWarehouse", startAtTradingWarehouse, "", None),
            ("startAtCallPlace", startAtCallPlace, "", None),
            ("useWarehouseMaid", useWarehouseMaid, "", None),
            ("repairWeapons", repairWeapons, "", None),
            ("backExchange", backExchange, "", None),
            ("intoHutton", intoHutton, "", None),
            ("enableEmailAlarm", self.viewer.EmailAlarmCheckBox.isChecked(), "", None),
            ("email", self.viewer.EmailEdit.text(), "", None),

            # TimeTab
            ("boss1CanBeHitCoolTime", boss1CanBeHitCoolTimeStr, "召唤到玛格岚可以被打(s)必须为数字类型", "num"),
            ("boss2CanBeHitCoolTime", boss2CanBeHitCoolTimeStr, "玛格岚死到柯尔特出现(s)必须为数字类型", "num"),
            ("skillGroup1KillBoss1Cost", skillGroup1KillBoss1CostStr, "技能组1预计击杀耗时(s)必须为数字类型", "num"),
            ("backTradingHouseTime", backTradingHouseTimeStr, "球点至交易所的耗时(s)必须为数字类型", "num"),

            # DataCollectionTab
            ("collectImgTaskOver", self.viewer.CollectTaskOverCheckBox.isChecked(), "", None),
            ("collectImgBagUI", self.viewer.CollectBagUiCheckBox.isChecked(), "", None),
            ("collectImgProcessBar", self.viewer.CollectProcessBarCheckBox.isChecked(), "", None),
            ("collectImgMargram", self.viewer.CollectMagramCheckBox.isChecked(), "", None),
            ("collectImgKhalk", self.viewer.CollectKhalkCheckBox.isChecked(), "", None),
            ("collectImgUseWarehouseMaid", self.viewer.CollectUseWarehouseMaidCheckBox.isChecked(), "", None),
            ("collectImgFindNPC", self.viewer.CollectFindNPCCheckBox.isChecked(), "", None),
            ("collectImgGMCheck", self.viewer.CollectGMCheck.isChecked(), "", None),
        ]

        # 如果开启仓库女仆放杂物的功能
        if useWarehouseMaid:
            to_checks.append(
                ("useWarehouseMaidShortcut", useWarehouseMaidShortcut, "开启仓库女仆存放功能，但未设置仓库女仆快捷键",
                 "shortcut")
            )

        # 如果打完后自动维修武器的功能
        if repairWeapons:
            to_checks.extend([
                ("setTentShortcut", setTentShortcut, "开启维修武器功能，但未设置设置帐篷快捷键", "shortcut"),
                ("tentRepairWeaponsShortcut", tentRepairWeaponsShortcut, "开启维修武器功能，但未设置帐篷维修武器快捷键",
                 "shortcut"),
                ("recycleTentShortcut", recycleTentShortcut, "开启维修武器功能，但未设置回收快捷键", "shortcut")
            ])

        for key, val, desc, check_type in to_checks:
            try:
                if check_type == "num":
                    rst[key] = float(val)
                elif check_type == "shortcut":
                    _val = val.toString()
                    if val == "":
                        raise ValueError
                    rst[key] = _val
                else:
                    rst[key] = val
            except Exception:
                available = False
                reason += f"{desc}\n"

        return available, rst, reason

    def load_config(self, config):
        try:
            # BasicTab
            self.viewer.ResetViewCheckBox.setChecked(config["resetView"])
            self.viewer.StartAtTradingWarehouseButton.setChecked(config["startAtTradingWarehouse"])
            self.viewer.StartAtCallPlaceButton.setChecked(config["startAtCallPlace"])
            self.viewer.UseWarehouseMaidCheckBox.setChecked(config["useWarehouseMaid"])
            self.viewer.RepairWeaponsCheckBox.setChecked(config["repairWeapons"])
            self.viewer.BackExchangeCheckBox.setChecked(config["backExchange"])
            self.viewer.IntoHuttonCheckBox.setChecked(config["intoHutton"])
            if global_var["enable_email"]:
                self.viewer.EmailAlarmCheckBox.setChecked(config["enableEmailAlarm"])
                self.viewer.EmailEdit.setText(config["email"])

            # TimeTab
            self.viewer.Boss1CanBeHitCoolTimeEdit.setText(str(config["boss1CanBeHitCoolTime"]))
            self.viewer.Boss2CanBeHitCoolTimeEdit.setText(str(config["boss2CanBeHitCoolTime"]))
            self.viewer.SkillGroup1KillBoss1CostEdit.setText(str(config["skillGroup1KillBoss1Cost"]))
            self.viewer.backTradingHouseTimeEdit.setText(str(config["backTradingHouseTime"]))

            # DataCollectionTab
            self.viewer.CollectTaskOverCheckBox.setChecked(config['collectImgTaskOver'])
            self.viewer.CollectBagUiCheckBox.setChecked(config['collectImgBagUI'])
            self.viewer.CollectProcessBarCheckBox.setChecked(config['collectImgProcessBar'])
            self.viewer.CollectMagramCheckBox.setChecked(config['collectImgMargram'])
            self.viewer.CollectKhalkCheckBox.setChecked(config['collectImgKhalk'])
            self.viewer.CollectUseWarehouseMaidCheckBox.setChecked(config['collectImgUseWarehouseMaid'])
            self.viewer.CollectFindNPCCheckBox.setChecked(config['collectImgFindNPC'])
            self.viewer.CollectGMCheck.setChecked(config['collectImgGMCheck'])

        except Exception as e:
            err = traceback.format_exc()
            Logger.error(err)

            # 弹窗提醒
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText("加载配置文件失败，该文件可能与当前程序版本不匹配，请在日志文件中确认报错！")
            msgBox.show()
