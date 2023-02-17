# -*- coding: utf-8 -*-
import time
import traceback

from win32gui import FindWindow

import operation.classics_op as classics_op
import operation.cv_op as cv_op
import operation.merge_scroll as merge_scroll
from app.init_resource import global_var
from app.init_func import init_labels_dic
from utils.cv_utils import Detector
from utils.muti_utils import FormatMsg
from utils.simulate_utils import KeyboardSimulate, MouseSimulate

fmmsg = FormatMsg(source="模拟动作")


def start_action(sig_dic, sig_mutex, msg_queue, window_title: str, window_class: str, title_height: int, onnx_path: str,
                 label_dic_path: str, debug: bool):
    """
    动作执行模块
    :param sig_dic:
    :param sig_mutex:
    :param msg_queue:
    :param window_title:
    :param window_class:
    :param title_height:
    :param onnx_path:
    :param label_dic_path:
    :param debug:
    :return:
    """
    from utils.log_utils import Logger

    # 初始化资源
    # # 初始化相关资源
    Logger.set_log_name("action_simulate.log")

    # # 确认是否有程序句柄
    hwnd = FindWindow(window_class, window_title)
    if hwnd == 0:
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/my_config.toml 中的 BDO.window_class 是否与游戏窗口名一致",
            level="error"))
        Logger.error("No Found hwnd: BlackDesert!")
        return

    # # 目前检测器
    label_dic = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, label_dic, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    detector.set_img_scale((576, 1024))

    # # 全局变量的加载
    global_var["BDO_window_title_bar_height"] = title_height

    try:
        action(sig_mutex, sig_dic, msg_queue, detector, hwnd, debug=debug)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        msg_queue.put(fmmsg.to_str("意外退出!请查看日志文件定位错误。", level="error"))

    # over
    msg_queue.put(fmmsg.to_str("完成了所有操作！", level="info"))
    with sig_mutex:
        sig_dic.update({"stop": True, "start": False, "pause": False})


def action(sig_mutex, sig_dic, msg_queue, detector, hwnd, debug=False):
    # # 复位的耗时
    reset_place_wait_time = 15
    # # 等待识别允许开始识别进度条的时间
    allow_infer_process_time = 1
    # # 从开始召唤到boss第一次出现变成可打击目标的总耗时
    boss1_can_be_hit_cool_time = 35.5
    # # 使用卷轴后的硬直时间
    the_stiffening_time_after_using_the_scroll = 15
    # # 后撤移动作的耗时
    back_action_cost_time = 1
    # # 第二段等待多时间到第一个boss的出现
    after_back_action_wait_time = boss1_can_be_hit_cool_time - the_stiffening_time_after_using_the_scroll - \
                                  back_action_cost_time - allow_infer_process_time
    # # 技能组动作耗时
    skill_action_time = 3.5
    # # 真正击杀boss1耗时
    real_kill_boss1_time = 3.5
    # # boss1完成倒地动画耗时
    boss1_dead_action_time = 3
    # # 从boss1死亡到boss2可以被打击耗时
    boss2_can_be_hit_cool_time = 14.5
    # # 完成boss1击杀确认目标识别后真正需要等待的数据
    boss2_real_wait_time = boss2_can_be_hit_cool_time - skill_action_time - boss1_dead_action_time - 0.1

    # 统计指标
    exec_count = 0
    msg_queue.put(fmmsg.to_str("开始运行"))
    start_at = time.perf_counter()

    # 运行时的计数变量
    retry_back_to_call_place = 0
    max_retry_back_to_call_place = 1
    retry_skill = 0
    max_retry_skill_using_skill_2 = 1  # 如果重试次数达到本次数则切换技能组（霸体，大范围）

    q = []

    # 任务开始前全局执行一次
    # # 重置到最大视角
    q.append((classics_op.reset_viewer, (), "重置到最大视角"))
    q.append((time.sleep, (0.5,), "等待0.5s"))
    # # TODO 确认宠物是否开启

    time.sleep(1)

    # init queue TODO 未来根据不同的初始化位置初始化队列
    q.append((classics_op.open_bag, (), "打开背包"))
    q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, debug), "找到召唤书并召唤"))

    while len(q) > 0:
        # 是否有来自GUI或者GM检测进程或者前置步骤的中断或者暂停信号
        with sig_mutex:
            if sig_dic["pause"]:
                time.sleep(1)
                continue
            if sig_dic["stop"]:
                msg_queue.put(fmmsg.to_str("接受到停止请求，停止模拟!", level="info"))
                break

        tup = q.pop(0)
        func, args, intention = tup
        msg_queue.put(fmmsg.to_str(intention, level="debug"))
        rst = func(*args)

        if func.__name__ == "use_Pila_Fe_scroll":
            find_id, scroll_pos, reason = rst
            if not find_id:
                # 如果找不到召唤书，正常结束
                msg_queue.put(fmmsg.to_str(reason))
                msg_queue.put(fmmsg.to_str("找不到更多的召唤书，接下来将执行清理背包、修武器、回城等任务。"))
                # 关闭背包UI
                q.append((classics_op.close_bag, (), "关闭背包UI"))

                # TODO 下方操作是否执行应该配置化
                # 杂物主动利用仓库女仆提交仓库
                q.append((cv_op.clear_bag, (detector, hwnd, debug), "杂物主动利用仓库女仆提交仓库"))

                # 打开帐篷修理武器，后回收帐篷
                q.append((classics_op.repair_weapons_by_tent, (hwnd,), "打开帐篷修理武器，后回收帐篷"))
                # 睡眠0.5s 让UI完成一部分动画
                q.append((time.sleep, (allow_infer_process_time,), "睡眠0.5s 让UI完成一部分动画"))
                # 打开寻找NPC的UI回到交易所
                q.append((cv_op.back_to_market, (detector, hwnd, debug), "打开寻找NPC的UI回到交易所"))
                # 睡眠160s，让人物移动到交易所 TODO 配置化
                q.append((time.sleep, (160,), "等待人物回交易所的时间"))
                # # #对话鲁西比恩坤并打开交易所仓库
                q.append(
                    (classics_op.chat_with_LucyBenKun_to_show_market_ui, (hwnd,), "对话鲁西比恩坤并打开交易所仓库"))
            else:
                # 鼠标移动到卷轴图标
                q.append((MouseSimulate.move, (scroll_pos[0], scroll_pos[1], True, 0.1), "鼠标移动到卷轴图标"))
                # 鼠标右键使用
                q.append((MouseSimulate.click, (MouseSimulate.RIGHT,), "鼠标右键使用"))
                # 按下回城确认召唤
                q.append((KeyboardSimulate.press_and_release, ("return",), "按下回城确认召唤"))
                # 关闭背包
                q.append((classics_op.close_bag, (), "关闭背包UI"))
                # 睡眠0.5s 让UI完成一部分动画
                q.append((time.sleep, (1,), "睡眠0.5s 让UI完成一部分动画"))
                # 判断是否出现远方目的地 TODO 数据收集结束后记得关闭debug模式
                q.append((cv_op.found_ui_process_bar, (detector, hwnd, 2, True or debug), "判断是否出现进度条UI"))

        elif func.__name__ == "found_ui_process_bar":
            # 如果没有出现进度条UI，并且重试次数还没有大于上线次数，则再次重试进行召唤
            if not rst and retry_back_to_call_place <= max_retry_back_to_call_place:
                retry_back_to_call_place += 1
                # 等待自动走到目的地
                q.append((time.sleep, (reset_place_wait_time,), "等待自动走回卷轴召唤地"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, debug), "找到召唤书并召唤"))

            elif not rst and retry_back_to_call_place > max_retry_back_to_call_place:
                retry_back_to_call_place += 1

                move_keys = ["A", "D", "S"]
                move_key = move_keys[retry_back_to_call_place % len(move_keys)]

                # 按住s向后走几步，帮助自动路线规划重置
                q.append((KeyboardSimulate.press_and_release, ("S",), f"按下S终端自动走路"))
                q.append((KeyboardSimulate.press, (move_key,), f"按住{move_key}向后走几步"))
                q.append((time.sleep, (5,), "等待自动走回卷轴召唤地"))
                q.append((KeyboardSimulate.release, (move_key,), f"松开{move_key}"))
                q.append((KeyboardSimulate.press_and_release, ("T",), "按下T重新按照游戏规划的自动路线前进"))

                # 等待自动走到目的地
                q.append((time.sleep, (reset_place_wait_time,), "等待自动走回卷轴召唤地"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, debug), "找到召唤书并召唤"))

            # 如果出现了进度条UI，此时的卷轴正在被正常召唤
            else:
                # 把重试回到召唤地点的次数重置为0
                retry_back_to_call_place = 0
                # 把重试技能次数重置为0
                retry_skill = 0

                # 等待使用卷轴时的硬直事件
                q.append((time.sleep, (the_stiffening_time_after_using_the_scroll,), "等待使用卷轴时的硬直事件"))
                # 向后移动给即将下落的boss腾出相应的体积，避免人物被挤压 TODO 未来配置化
                q.append((classics_op.reposition_after_call, (), "向后移动给即将下落的boss腾出相应的体积"))
                # 后撤位移后等待boss1变成可击杀状态
                q.append((time.sleep, (after_back_action_wait_time,), "后撤位移后等待boss1变成可击杀状态"))

                # 播放自定义技能动作  TODO 未来配置化
                q.append((classics_op.skill_action, (), "播放自定义技能动作"))
                # 等待BOSS玛格岚倒地动画完成
                q.append((time.sleep, (boss1_dead_action_time,), "等待BOSS玛格岚倒地动画完成"))
                # 目标检测-BOSS玛格岚是否还没死
                q.append((cv_op.found_boss_Magram_dead_or_Khalk_appear, (detector, hwnd, 3, debug),
                          "检测-BOSS玛格岚是否死亡或柯尔克是否出现"))

        #
        elif func.__name__ == "found_boss_Magram_dead_or_Khalk_appear" and intention == "检测-BOSS玛格岚是否死亡或柯尔克是否出现":
            # 如果没有发现玛格岚或看到了柯尔克
            if rst:
                # 把重试技能次数重置为0
                retry_skill = 0
                # 等待Boss2变成可被击杀的状态
                q.append((time.sleep, (boss2_real_wait_time,), "等待BOSS柯尔特变成可击杀状态"))

                # 如果重试次数小于
                if retry_skill <= max_retry_skill_using_skill_2:
                    # 播放动作  TODO 未来配置化
                    q.append((classics_op.skill_action, (), "播放自定义技能动作"))
                else:
                    if retry_skill % 2 == 0:
                        q.append((classics_op.skill_action2, (), "播放自定义技能动作2"))
                    else:
                        q.append((classics_op.skill_action, (), "播放自定义技能动作"))

                # 检测是否完成任务
                q.append((cv_op.found_task_over, (detector, hwnd, 2, debug), "检测-任务是否完成"))

            # 还是发现boss玛格岚
            else:
                retry_skill += 1
                # 如果重试次数小于
                if retry_skill <= max_retry_skill_using_skill_2:
                    # 播放动作  TODO 未来配置化
                    q.append((classics_op.skill_action, (), "播放自定义技能动作"))
                else:
                    if retry_skill % 2 == 0:
                        q.append((classics_op.skill_action2, (), "播放自定义技能动作2"))
                    else:
                        q.append((classics_op.skill_action, (), "播放自定义技能动作"))

                # 等待BOSS玛格岚倒地动画完成
                q.append((time.sleep, (boss1_dead_action_time,), "等待BOSS玛格岚倒地动画完成"))
                # 检测-BOSS玛格岚是否死亡或柯尔克是否出现
                q.append((cv_op.found_boss_Magram_dead_or_Khalk_appear, (detector, hwnd, 3, debug), "检测-BOSS玛格岚是否死亡或柯尔克是否出现"))

        elif func.__name__ == "found_task_over":
            if rst:
                retry_skill = 0
                # 等待任务变成可以呼出小黑的状态
                q.append((time.sleep, (3,), "等待任务变成可以呼出小黑的状态"))
                # 呼出小精灵完成任务
                q.append((classics_op.call_black_wizard_to_finish_task, (), "呼出小精灵完成任务"))
                # 按T回到召唤地点
                q.append((classics_op.reposition_before_call, (), "按T回到召唤地点"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, debug), "找到召唤书并召唤"))

            else:
                # 播放自定义技能动作  TODO 未来配置化
                q.append((classics_op.skill_action, (), "播放自定义技能动作"))
                # 检测是否完成任务
                q.append((cv_op.found_task_over, (detector, hwnd, 2, debug), "检测是否完成任务"))

        elif func.__name__ == "call_black_wizard_to_finish_task":
            # 统计性能指标
            exec_count += 1
            now_at = time.perf_counter()
            cur_cost_min = round((now_at - start_at) / 60)
            efficiency = round(exec_count / ((now_at - start_at) / 3600), 2)
            msg_queue.put(fmmsg.to_str(f"执行 {exec_count} 次，花费 {cur_cost_min} 分钟，平均 {efficiency} 个/小时。"))


def start_merge(sig_dic, sig_mutex, msg_queue, window_title: str, window_class: str, title_height: int, onnx_path: str,
                label_dic_path: str, debug: bool):
    from utils.log_utils import Logger

    Logger.set_log_name("action_simulate.log")

    # # 确认是否有程序句柄
    hwnd = FindWindow(window_class, window_title)
    if hwnd == 0:
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/my_config.toml 中的 BDO.window_class 是否与游戏窗口名一致",
            level="error"))
        Logger.error("No Found hwnd: BlackDesert!")
        return

    # # 目前检测器
    label_dic = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, label_dic)

    # # 全局变量的加载
    global_var["BDO_window_title_bar_height"] = title_height

    try:
        merge_scroll.retrieve_the_scroll_from_the_trading_warehouse(sig_mutex, sig_dic, msg_queue, detector, hwnd, debug=debug)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        msg_queue.put(fmmsg.to_str("意外退出!请查看日志文件定位错误。", level="error"))

    # over
    msg_queue.put(fmmsg.to_str("完成了所有操作！", level="info"))
    with sig_mutex:
        sig_dic.update({"stop": True, "start": False, "pause": False})