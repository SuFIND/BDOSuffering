# -*- coding: utf-8 -*-
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from win32gui import FindWindow, SetForegroundWindow, GetForegroundWindow

import operation.classics_op as classics_op
import operation.cv_op as cv_op
import operation.merge_scroll as merge_scroll
import operation.thread_op as thread_op
from app.init_resource import global_var
from app.init_func import init_labels_dic
from utils.win_utils import get_bdo_rect
from utils.cv_utils import Detector
from utils.muti_utils import FormatMsg, ExecSig
from utils.simulate_utils import KeyboardSimulate, MouseSimulate

fmmsg = FormatMsg(source="模拟动作")


def start_action(sig_dic, sig_mutex, msg_queue, window_title: str, window_class: str, title_height: int, onnx_path: str,
                 label_dic_path: str, gui_params: dict, debug: bool):
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
    :param gui_params:
    :param debug:
    :return:
    """
    from utils.log_utils import Logger

    # 初始化资源
    # # 初始化相关资源
    Logger.set_log_name("action_simulate.log")

    # # 初始化信号量控制方法
    exec_sig = ExecSig(sig_dic, sig_mutex)

    # # 全局变量的加载
    global_var["BDO_window_title_bar_height"] = title_height

    # # 确认是否有程序句柄
    hwnd = FindWindow(window_class, window_title)

    if hwnd == 0:
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/basic.toml 中的 BDO.window_title 是否与游戏窗口名一致",
            level="error"))
        Logger.error("No Found hwnd: BlackDesert!")
        return

    # # 目前检测器
    label_dic = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, label_dic, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])

    # # 初始化线程池，数量为0，用于收集怪物截图
    executor = ThreadPoolExecutor(max_workers=1)

    # 如果开始方式为从交易所出发或从球点出发
    task_queue = []
    if gui_params["startAtTradingWarehouse"] or gui_params["startAtCallPlace"]:
        task_queue.append((action, (exec_sig, msg_queue, detector, hwnd, gui_params, executor)))
        # 如果启动了回到交易所的功能，那么初始化时回到交易所后将会自动合球并回到并球场继续打球
        if gui_params["backExchange"]:
            task_queue.append((merge_action, (exec_sig, msg_queue, detector, hwnd, gui_params, debug)))
    # 如果开始方式为需要先合球，在从交易所出发那么
    if gui_params["StartAtTradingWarehouseAndMergeScroll"]:
        task_queue = [(merge_action, (exec_sig, msg_queue, detector, hwnd, gui_params, debug))]

    # # 激活当前前台窗口
    if GetForegroundWindow() != hwnd:
        SetForegroundWindow(hwnd)
        c_l, c_t, c_r, c_b = get_bdo_rect(hwnd)
        MouseSimulate.move(round((c_l + c_r)/2), round(c_t + c_b)/2)
        MouseSimulate.click()

    while len(task_queue) > 0:
        # 是否有来自GUI或者GM检测进程或者前置步骤的中断或者暂停信号
        if exec_sig.is_pause():
            time.sleep(2)
            continue
        if exec_sig.is_stop():
            msg_queue.put(fmmsg.to_str("接受到停止请求，停止模拟!", level="info"))
            break

        func, args = task_queue.pop(0)
        try:
            rst = func(*args)

            if func.__name__ == "action":
                if not gui_params["backExchange"]:
                    task_queue = []

            if func.__name__ == "merge_action":
                success, to_continue, reason = rst

                # 如果回到了交易所并且完成了合球，那么需要对初始化配置进行修改，因为此时人物角色位于交易所，相当于从交易所开始
                gui_params["startAtCallPlace"] = False
                gui_params["startAtTradingWarehouse"] = True
                gui_params["StartAtTradingWarehouseAndMergeScroll"] = False

                # 如果合球成功
                if success:
                    task_queue.extend([
                        (action, (exec_sig, msg_queue, detector, hwnd, gui_params, executor)),
                        (merge_action, (exec_sig, msg_queue, detector, hwnd, gui_params, debug)),
                    ])
                else:
                    task_queue.extend([
                        (action, (exec_sig, msg_queue, detector, hwnd, gui_params, executor)),
                    ])

        except Exception as e:
            err = traceback.format_exc()
            Logger.error(err)
            msg_queue.put(fmmsg.to_str("意外退出!请查看日志文件定位错误。", level="error"))

    # over
    Logger.shutdown()
    exec_sig.is_stop()
    msg_queue.put(fmmsg.to_str("完成了所有操作！", level="info"))


def action(exec_sig, msg_queue, detector, hwnd, gui_params, executor):
    # 超参数
    # # 复位的耗时
    reset_place_wait_time = 15
    # # 等待识别允许开始识别进度条的时间
    allow_infer_process_time = 1
    # # 从开始召唤到boss第一次出现变成可打击目标的总耗时
    boss1_can_be_hit_cool_time = gui_params["boss1CanBeHitCoolTime"]
    # # 使用卷轴后的硬直时间
    the_stiffening_time_after_using_the_scroll = 15

    # # 预估真正击杀boss1耗时
    estimated_kill_boss1_time = gui_params["skillGroup1KillBoss1Cost"]
    # # 等待boss1完成倒地动画耗时
    boss1_dead_action_time = 3
    # # 从boss1死亡到boss2可以被打击耗时
    boss2_can_be_hit_cool_time = gui_params["boss2CanBeHitCoolTime"]
    # # 从球点到交易所的路途耗时
    back_trading_house_time = gui_params["backTradingHouseTime"]

    # # 仓库女仆快捷键
    useWarehouseMaidShortcut = gui_params["useWarehouseMaidShortcut"]
    # # 设置帐篷快捷键
    setTentShortcut = gui_params["setTentShortcut"]
    # # 使用帐篷修理快捷键
    tentRepairWeaponsShortcut = gui_params["tentRepairWeaponsShortcut"]
    # # 回收帐篷快捷键
    recycleTentShortcut = gui_params["recycleTentShortcut"]

    # # 收集任务完成标志
    collect_img_task_over = gui_params["collectImgTaskOver"]
    collect_img_bas_ui = gui_params["collectImgBagUI"]
    collect_img_processBar = gui_params["collectImgProcessBar"]
    collect_img_useWarehouseMaid = gui_params["collectImgUseWarehouseMaid"]
    collect_img_FindNPC = gui_params["collectImgFindNPC"]
    collect_img_Magram = gui_params["collectImgMargram"]
    collect_img_Khalk = gui_params["collectImgKhalk"]

    # # 初始化技能执行模块
    # TODO mock_group 将有GUI中的参数去取代
    skill_config = [
        {
            "groupName": "技能组1",
            "groupExpectCost": 3.75,
            "blocks": [
                {
                    "name": "强：蝶旋风",
                    "pipelines": [
                        {
                            "type": "KBPress",
                            "key": "left shift"
                        },
                        {
                            "type": "MSClick",
                            "key": "left"
                        },
                        {
                            "type": "KBRelease",
                            "key": "left shift"
                        },
                        {
                            "type": "wait",
                            "sec": 1.4
                        }
                    ]
                },
                {
                    "name": "强：飓风",
                    "pipelines": [
                        {
                            "type": "KBPress",
                            "key": "space"
                        },
                        {
                            "type": "wait",
                            "sec": 1
                        },
                        {
                            "type": "KBRelease",
                            "key": "space"
                        },
                        {
                            "type": "wait",
                            "sec": 0.5
                        }
                    ]
                }
            ]
        },
        {
            "groupName": "技能组2",
            "groupExpectCost": 8,
            "blocks": [
                {
                    "name": "霸体：左移动",
                    "pipelines": [
                        {
                            "type": "KBPress",
                            "key": "left shift"
                        },
                        {
                            "type": "KBPressAndRelease",
                            "key": "D"
                        },
                        {
                            "type": "KBRelease",
                            "key": "left shift"
                        },
                        {
                            "type": "wait",
                            "sec": 0.75
                        }
                    ]
                },
                {
                    "name": "霸体：右移动",
                    "pipelines": [
                        {
                            "type": "KBPress",
                            "key": "left shift"
                        },
                        {
                            "type": "KBPressAndRelease",
                            "key": "A"
                        },
                        {
                            "type": "KBRelease",
                            "key": "left shift"
                        },
                        {
                            "type": "wait",
                            "sec": 0.75
                        }
                    ]
                },
                {
                    "name": "强：骤雨",
                    "pipelines": [
                        {
                            "type": "KBPress",
                            "key": "left shift"
                        },
                        {
                            "type": "KBPressAndRelease",
                            "key": "Q"
                        },
                        {
                            "type": "KBRelease",
                            "key": "left shift"
                        }
                    ]
                }
            ]
        }
    ]
    skill_model = classics_op.SkillAction(skill_config)

    # 自有变量
    # # 统计指标
    exec_count = 0
    msg_queue.put(fmmsg.to_str("开始运行"))
    start_at = time.perf_counter()

    # # 运行时的计数变量
    retry_back_to_call_place = 0  # 重试回到卷轴召唤地点的次数
    max_retry_back_to_call_place = 1  # 不采用ADS干预下，允许的自动回到卷轴召唤地点的最大次数

    my_timer = {
        "usePilaFeScoreAt": None,
        "readyHitBossMagram": None,
    }

    # 任务开始前全局执行一次
    # # 重置到最大视角
    q = []
    # 如果GUI的开关中开启了重置视角
    if gui_params["resetView"]:
        q.append((classics_op.reset_viewer, (), "重置到最大视角"))
        q.append((time.sleep, (0.5,), "等待0.5s"))

    # 如果需要进入赫顿，且当前的角色不在赫顿
    if gui_params["intoHutton"] and not gui_params["inHutton"]:
        q.append((cv_op.go_into_or_out_hutton, (detector, hwnd), "进入赫顿"))
    # # TODO 确认宠物是否开启

    time.sleep(1)

    # init queue 根据不同的初始化位置初始化队列
    # 从卷轴召唤地点开始
    if gui_params["startAtCallPlace"]:
        q.append((classics_op.open_bag, (), "打开背包"))
        q.append((cv_op.bag_auto_sort_on, (hwnd,), "打开背包自动排列功能"))
        q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "找到召唤书并召唤"))

    # 从交易所长鲁西比恩跟前开始
    if gui_params["startAtTradingWarehouse"]:
        q.append((classics_op.open_bag, (), "打开背包"))
        q.append((cv_op.bag_auto_sort_on, (hwnd,), "打开背包自动排列功能"))
        q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "找到召唤书并激活卷轴导航"))

    while len(q) > 0:
        # 是否有来自GUI或者GM检测进程或者前置步骤的中断或者暂停信号
        if exec_sig.is_pause():
            time.sleep(2)
            continue
        if exec_sig.is_stop():
            msg_queue.put(fmmsg.to_str("接受到停止请求，停止模拟!", level="info"))
            break

        tup = q.pop(0)
        func, args, intention = tup
        msg_queue.put(fmmsg.to_str(intention, level="debug"))
        rst = func(*args)

        if func.__name__ == "go_into_or_out_hutton":
            if intention == "进入赫顿":
                gui_params["inHutton"] = True
            elif intention == "离开赫顿":
                gui_params["inHutton"] = False

        if func.__name__ == "use_Pila_Fe_scroll":
            find_it, scroll_pos, reason = rst
            # 常规打球流程中
            if intention in {"找到召唤书并召唤", "再次找到召唤书并尝试召唤"}:
                if not find_it:
                    # 如果找不到召唤书，正常结束
                    msg_queue.put(fmmsg.to_str(reason))
                    msg_queue.put(fmmsg.to_str("找不到更多的召唤书，接下来将执行清理背包、修武器、回城等任务。"))
                    # 关闭背包UI
                    q.append((classics_op.close_bag, (), "关闭背包UI"))

                    # 启用仓库女仆提交杂物的功能
                    if gui_params["useWarehouseMaid"]:
                        # 杂物主动利用仓库女仆提交仓库
                        q.append(
                            (cv_op.clear_bag, (detector, hwnd, useWarehouseMaidShortcut, collect_img_useWarehouseMaid),
                             "杂物主动利用仓库女仆提交仓库"))

                    # 启用维修装备的功能
                    if gui_params["repairWeapons"]:
                        # 打开帐篷修理武器，后回收帐篷
                        q.append((classics_op.repair_weapons_by_tent,
                                  (hwnd, setTentShortcut, tentRepairWeaponsShortcut, recycleTentShortcut),
                                  "打开帐篷修理武器，后回收帐篷"))
                        # 睡眠0.5s 让UI完成一部分动画
                        q.append((time.sleep, (allow_infer_process_time,), "睡眠0.5s 让UI完成一部分动画"))

                    # 启用回到交易所的功能，如果启动自动合球该功能将无法关闭
                    if gui_params["backExchange"]:
                        # 打开寻找NPC的UI回到交易所
                        q.append(
                            (cv_op.back_to_market, (detector, hwnd, collect_img_FindNPC), "打开寻找NPC的UI回到交易所"))
                        # 睡眠160s，让人物移动到交易所
                        q.append((time.sleep, (back_trading_house_time,), "等待人物回交易所的时间"))
                        # 往前走一步，可以和鲁西比恩坤对话
                        q.append((KeyboardSimulate.press, ("w",), "往前走"))
                        q.append((time.sleep, (0.3,), "等待人物回交易所的时间"))
                        q.append((KeyboardSimulate.release, ("w",), "往前走"))
                        q.append((time.sleep, (1,), "等待人物停稳定可以和鲁西比恩坤进行对话交互"))

                    # 如果人正在赫顿
                    if gui_params["inHutton"]:
                        q.append((cv_op.go_into_or_out_hutton, (detector, hwnd), "离开赫顿"))
                else:
                    # 鼠标移动到卷轴图标
                    q.append((MouseSimulate.move, (scroll_pos[0], scroll_pos[1], True, 0.1), "鼠标移动到卷轴图标"))
                    # 鼠标右键使用
                    q.append((MouseSimulate.click, (MouseSimulate.RIGHT,), "鼠标右键使用"))
                    # 按下回车确认召唤
                    q.append((KeyboardSimulate.press_and_release, ("return",), "按下回城确认召唤"))
                    # 记录使用卷轴的时间
                    q.append(
                        (classics_op.set_timer_key_value, (my_timer, "usePilaFeScoreAt"), "记录使用卷轴召唤的时间"))
                    # 关闭背包
                    q.append((classics_op.close_bag, (), "关闭背包UI"))
                    # 睡眠1s 让UI完成一部分动画
                    q.append((time.sleep, (1,), "睡眠0.5s 让UI完成一部分动画"))
                    # 判断是否出现进度条UI
                    q.append((cv_op.found_ui_process_bar, (detector, hwnd, 5, 0.75, collect_img_processBar),
                              "判断是否出现进度条UI"))

            # 如果角色从交易所开始启动脚本
            elif intention in {"找到召唤书并激活卷轴导航"}:
                # 如果没有找到则结束，也不需要回到交易所
                if not find_it:
                    msg_queue.put(fmmsg.to_str("背包里没有卷轴，无法导航到召唤地点"))

                # 如果找到了，则准备按T，然后等待角色自己走回打球地点
                else:
                    # 鼠标移动到卷轴图标
                    q.append((MouseSimulate.move, (scroll_pos[0], scroll_pos[1], True, 0.1), "鼠标移动到卷轴图标"))
                    # 鼠标右键使用
                    q.append((MouseSimulate.click, (MouseSimulate.RIGHT,), "鼠标右键使用"))
                    # 按下回城确认召唤
                    q.append((KeyboardSimulate.press_and_release, ("return",), "按下回城确认召唤"))
                    # 关闭背包
                    q.append((classics_op.close_bag, (), "关闭背包UI"))
                    # 按下回城确认召唤
                    q.append((KeyboardSimulate.press_and_release, ("T",), "开始自动导航从交易所回到打球地点"))
                    # 等待回到召唤地点的时间
                    q.append((time.sleep, (back_trading_house_time,), "等待回到召唤地点的时间"))
                    # 打开背包
                    q.append((classics_op.open_bag, (), "打开背包"))
                    # 尝试召唤卷轴
                    q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "找到召唤书并召唤"))

        elif func.__name__ == "found_ui_process_bar":
            # 如果没有出现进度条UI，并且重试次数还没有大于上线次数，则再次重试进行召唤
            if not rst and retry_back_to_call_place <= max_retry_back_to_call_place:
                retry_back_to_call_place += 1
                # 等待自动走到目的地
                q.append((time.sleep, (reset_place_wait_time,), "没有识别到进度条，等待自动走回卷轴召唤地"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "再次找到召唤书并尝试召唤"))

            # 如果没有出现进度条UI，并且重试次数大于上线次数，则尝试左平移或右平移或后撤，脱离卡死
            elif not rst and retry_back_to_call_place > max_retry_back_to_call_place:
                retry_back_to_call_place += 1

                move_keys = ["A", "D", "S"]
                move_key = move_keys[retry_back_to_call_place % len(move_keys)]

                # 按住s向后走几步，帮助自动路线规划重置
                q.append((KeyboardSimulate.press_and_release, ("S",),
                          f"尝试第{retry_back_to_call_place}后没有识别到进度条， 按下S中断自动走路"))
                q.append((KeyboardSimulate.press, (move_key,), f"按住{move_key}向后走几步"))
                q.append((time.sleep, (3,), "等待自动走回卷轴召唤地"))
                q.append((KeyboardSimulate.release, (move_key,), f"松开{move_key}"))
                q.append((KeyboardSimulate.press_and_release, ("T",), "按下T重新按照游戏规划的自动路线前进"))

                # 等待自动走到目的地
                q.append((time.sleep, (reset_place_wait_time,), "等待自动走回卷轴召唤地"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "再次找到召唤书并尝试召唤"))

            # 如果出现了进度条UI，此时的卷轴正在被正常召唤
            else:
                # 把重试回到召唤地点的次数重置为0
                retry_back_to_call_place = 0

                # 等待使用卷轴时的硬直事件
                q.append((time.sleep, (the_stiffening_time_after_using_the_scroll,), "等待使用卷轴时的硬直事件"))
                # 向后移动给即将下落的boss腾出相应的体积，避免人物被挤压 TODO 未来配置化
                q.append((classics_op.reposition_after_call, (), "向后移动给即将下落的boss腾出相应的体积"))

        elif intention == "向后移动给即将下落的boss腾出相应的体积":
            # 拆解出这个部分，引入动态执行时间的概念
            has_been_cost = classics_op.calculate_the_elapsed_time_so_far(my_timer["usePilaFeScoreAt"])

            # 计算出本次步骤中需要等待的事件
            after_back_action_wait_time = boss1_can_be_hit_cool_time - has_been_cost

            # 后撤位移后等待boss1变成可击杀状态
            q.append((time.sleep, (after_back_action_wait_time,), "后撤位移后等待boss1变成可击杀状态"))
            # 记录准备对boss1释放技能的时间
            q.append(
                (classics_op.set_timer_key_value, (my_timer, "readyHitBossMagram"), "记录准备对boss1释放技能的时间"))
            # 启动采集玛格岚图片的线程
            if collect_img_Magram:
                q.append((thread_op.run_thread_op, (executor,
                                                    "CollectImgThread",
                                                    (hwnd, "logs/img/Magram", estimated_kill_boss1_time, 0.1)),
                          "启动采集玛格岚图片的线程"))
            # 播放自定义技能动作
            q.append((skill_model.run, (), "播放自定义技能动作"))

            # 等待BOSS玛格岚倒地动画完成
            q.append((time.sleep, (boss1_dead_action_time,), "等待BOSS玛格岚倒地动画完成"))
            # 目标检测-BOSS玛格岚是否还没死
            q.append((cv_op.found_boss_Magram_dead_or_Khalk_appear, (detector, hwnd, 3),
                      "检测-BOSS玛格岚是否死亡或柯尔克是否出现"))

        elif func.__name__ == "found_boss_Magram_dead_or_Khalk_appear":
            # 如果没有发现玛格岚或看到了柯尔克
            if rst:
                # 重置重试技能次数为0
                skill_model.reset_exec_times()

                boss2_real_wait_time = boss2_can_be_hit_cool_time + estimated_kill_boss1_time - \
                                       classics_op.calculate_the_elapsed_time_so_far(my_timer["readyHitBossMagram"])

                # 等待Boss2变成可被击杀的状态
                q.append((time.sleep, (boss2_real_wait_time,),
                          "检测到玛格岚死亡或柯尔克出现了, 等待BOSS柯尔特变成可击杀状态"))

                # 启动采集柯尔克图片的线程
                if collect_img_Khalk:
                    q.append((thread_op.run_thread_op, (executor,
                                                        "CollectImgThread",
                                                        (hwnd, "logs/img/Khalk", estimated_kill_boss1_time, 0.1)),
                              "启动采集柯尔克图片的线程"))

                q.append((skill_model.run, (), "播放自定义技能动作"))

                # 检测是否完成任务
                q.append((cv_op.found_task_over, (detector, hwnd, 3, 0.75, collect_img_task_over), "检测-任务是否完成"))

            # 还是发现boss玛格岚
            else:
                # 重新记录准备对boss1释放技能的时间
                q.append((classics_op.set_timer_key_value, (my_timer, "readyHitBossMagram"),
                          "记录准备对boss1释放技能的时间"))
                # 启动采集玛格岚图片的线程
                if collect_img_Magram:
                    q.append((thread_op.run_thread_op, (executor,
                                                        "CollectImgThread",
                                                        (hwnd, "logs/img/Magram", estimated_kill_boss1_time, 0.1)),
                              "启动采集玛格岚图片的线程"))
                # 根据技能使用次数播放
                q.append((skill_model.run, (), "播放自定义技能动作"))

                # 等待BOSS玛格岚倒地动画完成
                q.append((time.sleep, (boss1_dead_action_time,), "等待BOSS玛格岚倒地动画完成"))
                # 检测-BOSS玛格岚是否死亡或柯尔克是否出现
                q.append((cv_op.found_boss_Magram_dead_or_Khalk_appear, (detector, hwnd, 3),
                          "检测-BOSS玛格岚是否死亡或柯尔克是否出现"))

        elif func.__name__ == "found_task_over" and intention == "检测-任务是否完成":
            # 如果首次检测到任务完成的标志
            if rst:
                # 等待任务变成可以呼出小黑的状态
                q.append((time.sleep, (2,), "等待任务变成可以呼出小黑的状态"))
                # 呼出小精灵完成任务
                q.append((classics_op.call_black_wizard_to_finish_task, (), "呼出小精灵完成任务"))
                # 等待一下动画
                q.append((time.sleep, (0.5,), "等待一下动画"))
                # 检测-呼出小精灵完成任务后任务是否真的完成
                q.append((cv_op.found_task_over, (detector, hwnd, 1, 0.5, collect_img_task_over),
                          "检测-呼出小精灵完成任务后任务是否真的完成"))

            # 如果没有首次检测到任务完成的标志
            else:
                # 启动采集柯尔克图片的线程
                if collect_img_Khalk:
                    q.append((thread_op.run_thread_op, (executor,
                                                        "CollectImgThread",
                                                        (hwnd, "logs/img/Khalk", estimated_kill_boss1_time, 0.1)),
                              "启动采集柯尔克图片的线程"))
                # 播放自定义技能动作  TODO 未来配置化
                q.append((skill_model.run, (), "播放自定义技能动作"))
                # 检测-任务是否完成
                q.append((cv_op.found_task_over, (detector, hwnd, 1, 0.5, collect_img_task_over), "检测-任务是否完成"))

        elif func.__name__ == "found_task_over" and intention == "检测-呼出小精灵完成任务后任务是否真的完成":
            # 如果发现完成任务的标识
            if rst:
                # 先关闭被错误呼出的菜单
                q.append((KeyboardSimulate.press_and_release, ("esc",), "关闭因为错误呼出小黑异常导致打开的菜单"))
                # 等待任务变成可以呼出小黑的状态
                q.append((time.sleep, (2,), "等待任务变成可以呼出小黑的状态"))
                # 呼出小精灵完成任务
                q.append((classics_op.call_black_wizard_to_finish_task, (), "呼出小精灵完成任务"))
                # 检测-呼出小精灵完成任务后任务是否真的完成
                q.append(
                    (cv_op.found_task_over, (detector, hwnd, 1, 0.5, collect_img_task_over),
                     "检测-呼出小精灵完成任务后任务是否真的完成"))

            # 如果没有发现说明任务正常提交了
            else:
                # 统计性能指标
                exec_count += 1
                now_at = time.perf_counter()
                cur_cost_min = round((now_at - start_at) / 60)
                efficiency = round(exec_count / ((now_at - start_at) / 3600), 2)
                msg_queue.put(fmmsg.to_str(f"执行 {exec_count} 次，花费 {cur_cost_min} 分钟，平均 {efficiency} 个/小时。"))

                # 重置重试技能次数为0
                skill_model.reset_exec_times()

                # 按T回到召唤地点
                q.append((classics_op.reposition_before_call, (), "按T回到召唤地点"))
                # 打开背包
                q.append((classics_op.open_bag, (), "打开背包"))
                # 找到召唤书并召唤
                q.append((cv_op.use_Pila_Fe_scroll, (detector, hwnd, collect_img_bas_ui), "找到召唤书并召唤"))


def start_merge(sig_dic, sig_mutex, msg_queue, window_title: str, window_class: str, title_height: int, onnx_path: str,
                label_dic_path: str, debug: bool, gui_params):
    from utils.log_utils import Logger

    Logger.set_log_name("action_simulate.log")

    # # 确认是否有程序句柄
    hwnd = FindWindow(window_class, window_title)
    if hwnd == 0:
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/basic.toml 中的 BDO.window_class 是否与游戏窗口名一致",
            level="error"))
        Logger.error("No Found hwnd: BlackDesert!")
        return

    # # 目前检测器
    label_dic = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, label_dic)

    # # 全局变量的加载
    global_var["BDO_window_title_bar_height"] = title_height

    # # 初始化信号量控制方法
    exec_sig = ExecSig(sig_dic, sig_mutex)

    try:
        merge_action(exec_sig, msg_queue, detector, hwnd, gui_params, debug)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        msg_queue.put(fmmsg.to_str("意外退出!请查看日志文件定位错误。", level="error"))
    finally:
        exec_sig.is_stop()
        Logger.shutdown()


def merge_action(exec_sig, msg_queue, detector, hwnd, gui_params, debug: bool):
    msg_queue.put(fmmsg.to_str("开始合球！", level="info"))
    success, to_continue, reason = True, True, ""

    to_continue_get_al_scroll = True

    task_queue = [
        # 打开背包，关闭自动排列
        (classics_op.open_bag, ()),
        (cv_op.bag_auto_sort_off, (hwnd,)),
        (classics_op.close_bag, ()),

        # 从交易所仓库中获取古语进行合成
        (merge_scroll.retrieve_the_scroll_from_the_trading_warehouse,
         (exec_sig, msg_queue, detector, hwnd, debug)),
        (time.sleep, (0.4,)),
    ]

    while len(task_queue) > 0 and success:
        if exec_sig.is_pause():
            time.sleep(2)
            continue
        if exec_sig.is_stop():
            msg_queue.put(fmmsg.to_str("接受到停止请求，停止模拟!", level="info"))
            break

        func, args = task_queue.pop(0)
        rst = func(*args)

        if func.__name__ == "retrieve_the_scroll_from_the_trading_warehouse":
            success, to_continue_merge_al_scroll, _to_continue_get_al_scroll, reason = rst
            to_continue_get_al_scroll = to_continue_get_al_scroll and _to_continue_get_al_scroll

            # 如果需要继续合成古语卷轴
            if to_continue_merge_al_scroll:
                task_queue.append((merge_scroll.merge_scroll, (detector, hwnd, debug)), )

        if func.__name__ == "merge_scroll":
            success, _to_continue_get_al_scroll, reason = rst

            gui_params["startAtCallPlace"] = False
            gui_params["startAtTradingWarehouse"] = True

            to_continue_get_al_scroll = to_continue_get_al_scroll and _to_continue_get_al_scroll
            if to_continue_get_al_scroll:
                task_queue.extend([
                    (merge_scroll.retrieve_the_scroll_from_the_trading_warehouse,
                     (exec_sig, msg_queue, detector, hwnd, debug)),
                    (time.sleep, (0.4,)),
                ])

    if not success:
        msg_queue.put(fmmsg.to_str(reason, level="error"))

    # over
    msg_queue.put(fmmsg.to_str("完成合球！", level="info"))
    return success, to_continue, reason
