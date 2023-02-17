# -*- coding: utf-8 -*-
import os
import re
import time
import cv2
import numpy as np
import traceback

import operation.classics_op as classics_op
from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import MouseSimulate, KeyboardSimulate
from utils.win_utils import get_bdo_rect
from utils.cv_utils import Detector, is_pos_can_be_considered_the_same
from utils.muti_utils import FormatMsg
from utils.ocr_utils import recognize_numpy
from utils.log_utils import Logger
import operation.cv_op as cv_op
from utils.ocr_utils import get_bag_capacity_by_tesseract_ocr

fmmsg = FormatMsg(source="模拟动作")


def get_merge_button_by_temple(win_dc: WinDCApiCap, client_rect) -> list[tuple]:
    rst = []
    if not win_dc.is_available():
        return rst
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/mergeButton.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        rst.append([cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2])
    return rst


def use_merge_button(win_dc: WinDCApiCap, client_rect, limit_bbox=(-9999, -9999, 9999, 9990)) -> None:
    # 识别是否有合成的小icon
    merge_button_poses = get_merge_button_by_temple(win_dc, client_rect)

    while len(merge_button_poses) > 0:
        icon_pos = merge_button_poses.pop()
        if not limit_bbox[0] < icon_pos[0] < limit_bbox[2] \
                or not limit_bbox[1] < icon_pos[1] < limit_bbox[3]:
            continue
        MouseSimulate.move(icon_pos[0], icon_pos[1])
        MouseSimulate.click()
        time.sleep(0.1)
        _ = get_merge_button_by_temple(win_dc, client_rect)
        merge_button_poses.extend(_)


def get_bag_capacity_by_ocr(win_dc: WinDCApiCap, bag_bbox):
    """
    OCR获取当前背包容积
    :param win_dc: 
    :param bag_bbox: 
    :return: 
    """
    rst = None, None
    if not win_dc.is_available():
        return rst

    try:
        sc = win_dc.get_hwnd_screenshot_to_numpy_array()
        bg_sc = sc[bag_bbox[1]:bag_bbox[3], bag_bbox[0]:bag_bbox[2]]

        bg_sc_h, bg_sc_w = bg_sc.shape[:2]
        # 利用超参数比例获取背包空间相关的图片，减少ocr获取的信息
        capacity_left = round(bg_sc_w * 0.8125)
        capacity_top = round(bg_sc_h * 0.1)
        capacity_bottom = round(bg_sc_h * 0.2)
        capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]

        # 使用英语减少错误识别数字的可能
        ocr_rst = recognize_numpy(capacity_sc, lang="en-US")
        text = ocr_rst["text"]
        clear_text = ""
        for char in text:
            if char not in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "/"}:
                continue
            clear_text += char

        # 利用正则便于cur和total都能获取
        r = re.match(r"(?P<cur>\d+)/(?P<total>\d+)", clear_text)
        if r is not None:
            _ = r.groupdict()
            cur, total = _["cur"], _["total"]
            cur = int(cur)
            total = int(total)
            rst = cur, total
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
    return rst


def get_trading_warehouse_button_pos(win_dc: WinDCApiCap, bdo_rect):
    """
    获取和鲁西比恩坤对话后进入交易所UI后打开交易所仓库按钮的位置
    :param win_dc: 
    :param bdo_rect: 
    :return: 
    """
    if not win_dc.is_available():
        return
    cur_windows_left, cur_windows_top, _, _ = bdo_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/marketManagementButton.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 5, cur_windows_top + pt_top + 5
    return None


def got_trading_warehouse_ui_bbox(detector: Detector, win_dc, bdo_rect, retry: int, debug=False):
    """
    从模型推理结果中获取交易所仓库UI的位置
    :param detector: 
    :param win_dc: 
    :param bdo_rect: 
    :param retry: 
    :param debug: 
    :return: 
    """
    c_left, c_top, _, _ = bdo_rect
    for i in range(retry + 1):
        img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/TradingWarehouse")
        infer_rst = detector.infer(img)
        if "ui$Trading Warehouse" not in infer_rst:
            continue

        bbox_tup = infer_rst["ui$Trading Warehouse"][0]["bbox"]
        return bbox_tup[0] + c_left, bbox_tup[1] + c_top, bbox_tup[2] + c_left, bbox_tup[3] + c_top


def got_trading_warehouse_and_bag_ui_bbox(detector: Detector, win_dc, bdo_rect, retry: int, debug=False):
    """
    从模型推理结果中获取交易所仓库UI和背包Ui的位置
    :param detector: 
    :param win_dc: 
    :param bdo_rect: 
    :param retry: 
    :param debug: 
    :return: 
    """
    c_left, c_top, _, _ = bdo_rect
    bag_bbox = None
    trading_warehouse_bbox = None
    bag_bbox_abs = None
    trading_warehouse_bbox_abs = None
    for i in range(retry + 1):
        if bag_bbox is not None and trading_warehouse_bbox is not None:
            break

        img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/TradingWarehouseAndBag")
        infer_rst = detector.infer(img)
        if "ui$Trading Warehouse" in infer_rst and trading_warehouse_bbox is None:
            bbox = infer_rst["ui$Trading Warehouse"][0]["bbox"]
            trading_warehouse_bbox = bbox[0], bbox[1], bbox[2], bbox[3]
            trading_warehouse_bbox_abs = bbox[0] + c_left, bbox[1] + c_top, bbox[2] + c_left, bbox[3] + c_top
        if "ui$Bag" in infer_rst and bag_bbox is None:
            bbox = infer_rst["ui$Bag"][0]["bbox"]
            bag_bbox = bbox[0], bbox[1], bbox[2], bbox[3]
            bag_bbox_abs = bbox[0] + c_left, bbox[1] + c_top, bbox[2] + c_left, bbox[3] + c_top

    return bag_bbox, bag_bbox_abs, trading_warehouse_bbox, trading_warehouse_bbox_abs


def get_scroll_written_in_ancient_language_poses_by_temple(win_dc: WinDCApiCap, client_rect) -> list:
    """
    用过模版匹配找到古语召唤卷轴的中心点位置
    :param win_dc:
    :param client_rect:
    :return:
    """
    if not win_dc.is_available():
        return []
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/ScrollWrittenInAncientLanguage_1.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    poses = []
    for pt_left, pt_top in zip(*loc[::-1]):
        poses.append((cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2))
    return poses


def get_scroll_written_in_ancient_language_poses_by_model(detector, win_dc: WinDCApiCap, bdo_rect: list[int],
                                                          debug=False) -> list:
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug,
                                                    save_dir="logs/img/ScrollWrittenInAncientLanguage")
    infer_rst = detector.infer(img)
    if "item$Scroll Written in Ancient Language" not in infer_rst:
        return []

    bbox_tups = infer_rst["item$Scroll Written in Ancient Language"]
    poses = []
    for bbox_obj in bbox_tups:
        bbox_tup = bbox_obj["bbox"]
        poses.append(((bbox_tup[0] + bbox_tup[2]) / 2 + c_left, (bbox_tup[1] + bbox_tup[3]) / 2 + c_top))
    return poses


def get_scroll_written_in_ancient_language_pos_in_custom_bbox(win_dc: WinDCApiCap,
                                                              client_rect,
                                                              bbox) -> [None, tuple]:
    """
    用过模版匹配找到位于交易所仓库的古语召唤卷轴的位置
    :param win_dc:
    :param client_rect:
    :param bbox: 指定的框框
    :return:
    """
    rst = None
    item_poses = get_scroll_written_in_ancient_language_poses_by_temple(win_dc, client_rect)
    for pos in item_poses:
        # 如果不在交易仓库的UI范围内则舍弃
        if not bbox[0] < pos[0] < bbox[2] \
                or not bbox[1] < pos[1] < bbox[3]:
            continue
        rst = pos
        break
    return rst


def get_scroll_written_in_ancient_language_poses_in_custom_bbox(detector,
                                                                win_dc: WinDCApiCap,
                                                                client_rect,
                                                                bbox) -> list:
    """
    用过模版匹配找到位于交易所仓库的古语召唤卷轴的位置
    :param detector:
    :param win_dc:
    :param client_rect:
    :param bbox: 指定的框框
    :return:
    """
    poses = []
    # 优先使用AI
    item_poses = get_scroll_written_in_ancient_language_poses_by_model(detector, win_dc, client_rect)
    if len(item_poses) < 1:
        item_poses = get_scroll_written_in_ancient_language_poses_by_temple(win_dc, client_rect)

    for pos in item_poses:
        # 如果不在交易仓库的UI范围内则舍弃
        if not bbox[0] < pos[0] < bbox[2] \
                or not bbox[1] < pos[1] < bbox[3]:
            continue
        poses.append(pos)
    return poses


def get_scroll_written_in_ancient_language_avg_bbox_size(detector: Detector,
                                                         win_dc: WinDCApiCap,
                                                         default=(45, 45)):
    img = win_dc.get_hwnd_screenshot_to_numpy_array()
    infer_rst = detector.infer(img)
    if "item$Scroll Written in Ancient Language" not in infer_rst:
        return default

    bbox_tups = infer_rst["item$Scroll Written in Ancient Language"]
    ws = []
    hs = []
    cnt = 0
    for bbox_obj in bbox_tups:
        bbox_tup = bbox_obj["bbox"]

        ws.append(bbox_tup[2] - bbox_tup[0])
        hs.append(bbox_tup[3] - bbox_tup[1])
        cnt += 1

    total_ws = 0
    total_hs = 0
    for one in ws:
        total_ws += one
    for one in hs:
        total_hs += one
    avg_ws = max(total_ws // cnt, default[0])
    avg_hs = max(total_hs / cnt, default[1])
    return avg_ws, avg_hs


def auto_take_back_ancient_lang_scroll(detector,
                                       win_dc: WinDCApiCap,
                                       client_rect,
                                       debug=False):
    success = False
    done = False
    reason = ""

    # 每次滚轮向下移动四个格子
    wheel_step = 4
    # 交易所的UI支持滚轮向下滚动多少次
    max_wheel_step = 80

    # step 1 识别出背包和仓库交易所的UI的位置
    bag_bbox, bog_abs_bbox, tw_bbox, tw_abs_bbox = \
        got_trading_warehouse_and_bag_ui_bbox(detector, win_dc, client_rect, retry=2, debug=debug)

    # step 2 计算出用于悬停在UI内和UI外的绝对值坐标
    into_tw_bbox_pos = (tw_abs_bbox[0] + tw_abs_bbox[2]) / 2, (
            tw_abs_bbox[1] + tw_abs_bbox[3]) / 2
    out_to_tw_bbox_pos = tw_abs_bbox[0] - 50, tw_abs_bbox[1] - 50

    # step 3 ocr出背包的容量
    cur_space, total_space = get_bag_capacity_by_tesseract_ocr(win_dc, bag_bbox)
    if None in [cur_space, total_space]:
        reason = "ocr无法获取背包容量"
        # ocr 识别失败
        return success, done, reason

    # step 4 计算20个20个的获取需要取多少次，10个10个的取需要取多少次
    real_can_use_space = total_space - cur_space - 5
    each_20_step = real_can_use_space // 20
    each_10_step = (real_can_use_space - 20 * each_20_step) // 10
    each_5_step = (real_can_use_space - 20 * each_20_step - 10 * each_10_step) // 5

    # step 5 在交易所仓库UI中寻找目标"用古语记录的卷轴”
    target_pos = None
    for _ in range(0, max_wheel_step + 1, wheel_step):
        target_pos = get_scroll_written_in_ancient_language_pos_in_custom_bbox(win_dc,
                                                                               client_rect,
                                                                               tw_abs_bbox)
        # 说明了找到了在交易所仓库UI的古语卷轴
        if target_pos is not None:
            break

        # 否则继续向下滚动，看看古语是不是在交易所里比较后面的地方
        MouseSimulate.move(into_tw_bbox_pos[0], into_tw_bbox_pos[1], duration=0.1)
        for __ in range(wheel_step):
            MouseSimulate.wheel(-100)
        MouseSimulate.move(out_to_tw_bbox_pos[0], out_to_tw_bbox_pos[1])

    # 如果此时古语卷轴还是找不到，说明交易仓库中已经没有卷轴，需要提醒补充
    if target_pos is None:
        reason = "交易所卷轴不足，请及时补充卷轴"
        success = True
        done = True
        return success, done, reason

    for _ in range(each_20_step):
        MouseSimulate.move(target_pos[0], target_pos[1], duration=0.1)
        MouseSimulate.click(MouseSimulate.RIGHT)
        KeyboardSimulate.press_and_release("F")
        KeyboardSimulate.press_and_release("return")
        time.sleep(0.5)

    for _ in range(each_10_step):
        MouseSimulate.move(target_pos[0], target_pos[1], duration=0.1)
        MouseSimulate.click(MouseSimulate.RIGHT)
        KeyboardSimulate.press_and_release("1")
        KeyboardSimulate.press_and_release("0")
        KeyboardSimulate.press_and_release("return")
        time.sleep(0.5)

    for _ in range(each_5_step):
        MouseSimulate.move(target_pos[0], target_pos[1], duration=0.1)
        MouseSimulate.click(MouseSimulate.RIGHT)
        KeyboardSimulate.press_and_release("5")
        KeyboardSimulate.press_and_release("return")
        time.sleep(0.5)
    success = True
    done = True
    return success, done, reason


def retrieve_the_scroll_from_the_trading_warehouse(sig_mutex, sig_dic, msg_queue, detector: Detector, hwnd,
                                                   debug=False):
    """
    从交易所取回当前背包下可容纳的最大安全数量的古语卷轴
    """
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    q = [
        (KeyboardSimulate.press_and_release, ("R",), "按下R与鲁西比恩坤对胡"),
        (time.sleep, (0.5,), "动画0.5s"),
        (KeyboardSimulate.press_and_release, ("2",), "按下2进入交易所仓库UI"),
        (time.sleep, (0.5,), "动画0.5s"),
        (get_trading_warehouse_button_pos, (win_dc, bdo_rect,), "是否找到交易所按钮"),
    ]
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
        rst = func(*args)
        msg_queue.put(fmmsg.to_str(intention, level="debug"))

        if func.__name__ == "get_trading_warehouse_button_pos":
            # 如果获取不到按钮“交易所仓库”的坐标
            if rst is None:
                q.extend([
                    (KeyboardSimulate.press_and_release, ("esc",), "退出交易所UI"),
                    (KeyboardSimulate.press_and_release, ("2",), "按下2进入交易所仓库UI"),
                    (time.sleep, (0.5,), "动画0.5s"),
                    (get_trading_warehouse_button_pos, (win_dc, bdo_rect,), "是否找到交易所按钮"),
                ])

            # 如果获取到按钮“交易所仓库”的坐标
            else:
                q.extend([
                    (MouseSimulate.move, (rst[0], rst[1], True, 0.1), "鼠标移动到`交易所仓库`按钮上"),
                    (MouseSimulate.click, (), "点击鼠标左键"),
                    (time.sleep, (0.5,), "动画0.5s"),
                    (auto_take_back_ancient_lang_scroll, (detector, win_dc, bdo_rect, debug),
                     "自动从交易所仓库中拿去卷轴"),  # TODO 这个op有reason最好处理一下
                    (KeyboardSimulate.press_and_release, ("esc",), "退出交易所仓库与背包Ui"),
                    (KeyboardSimulate.press_and_release, ("esc",), "退出交易所UI"),
                    (KeyboardSimulate.press_and_release, ("esc",), "退出与鲁西比恩坤的对话UI"),
                ])
        if func.__name__ == "auto_take_back_ancient_lang_scroll":
            success, done, reason = rst
            success_str = "成功" if success else "失败"
            suffix = f"，{reason}" if reason else ""
            info_str = f"从交易所取得古语卷轴{success_str}" + suffix
            msg_queue.put(fmmsg.to_str(info_str))


def merge_scroll(detector: Detector, hwnd, debug=False):
    success = False
    to_continue = True
    reason = ""

    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    # 打开背包
    classics_op.open_bag()

    # 等待1s让动画结束
    time.sleep(1)

    bag_bbox = cv_op.get_bag_ui_bbox(detector, win_dc, bdo_rect, debug)
    bag_bbox_no_abs = cv_op.get_bag_ui_bbox(detector, win_dc, [0, 0, 0, 0], debug)

    if bag_bbox is None:
        to_continue = False
        reason = "无法识别背包UI"
        return success, to_continue, reason

    bag_left, bag_top, bag_right, bag_bottom = bag_bbox
    into_bag_pos = round((bag_right + bag_left) / 2), round((bag_top + bag_bottom) / 2)
    out_to_bag_pos = bag_left - 30, bag_top - 30

    # 超参数
    step = 3    # 滚轮往下探索的步数
    duration = 0.01     # 鼠标仿真移动的速度

    # 自有变量
    cur_step = 0
    max_step = 16
    ancient_lang_icon_size = None
    col_space_width = None  # 背包列宽
    row_space_height = None  # 背包行高
    while cur_step <= max_step:
        # 先移动到UI外避免对古语卷轴识别的干扰
        MouseSimulate.move(out_to_bag_pos[0], out_to_bag_pos[1])
        # 使用合成按钮合成卷轴
        use_merge_button(win_dc, bdo_rect, bag_bbox)

        # 初始化设置滚轮还不能向下滑动
        can_wheel_down = False
        while not can_wheel_down:
            # 识别目前截图，得到的所有古语卷轴的位置
            item_poses = get_scroll_written_in_ancient_language_poses_in_custom_bbox(detector, win_dc, bdo_rect,
                                                                                     bag_bbox)

            # 等比例计算出可拖拽区域的位置
            work_area_bbox = cv_op.get_bag_work_area_ui_bbox(bag_bbox, bdo_rect, debug)

            # 如果视野内找不到古语卷轴，则允许鼠标执行向下的滚轮
            if len(item_poses) == 0:
                can_wheel_down = True
                break

            # 如果没有计算出过古语卷轴的图标大小则计算
            if ancient_lang_icon_size is None:
                ancient_lang_icon_size = get_scroll_written_in_ancient_language_avg_bbox_size(detector, win_dc)
                col_space_width = round(ancient_lang_icon_size[0] * 0.18)
                row_space_height = round(ancient_lang_icon_size[1] * 0.22)

            # 如果古语的数量大于0，小于5的话，移动到可拖拽区域的最下方
            if 0 < len(item_poses) < 5:
                # 计算出第一张古语卷轴该拖拽到那个位置
                drag_to_pos_x = work_area_bbox[0] + col_space_width*1. + ancient_lang_icon_size[0] // 2
                drag_to_pos_y = work_area_bbox[3] - row_space_height - ancient_lang_icon_size[1] // 2

                # 先推断出所有多出来的古语可能放置的位置
                tgt_poses = []
                for i in range(len(item_poses)):
                    tgt_poses.append([
                        drag_to_pos_x + i * (col_space_width + ancient_lang_icon_size[0]),
                        drag_to_pos_y
                    ])

                # 相似相容处理，避免出现古语在目标位置上，但仍然需要替换的情况
                real_need_to_drag_poses_group = []
                while len(item_poses) > 0:
                    item_pos = item_poses.pop()
                    to_pop_idx = None
                    for tgt_idx, tgt_pos in enumerate(tgt_poses):
                        if not is_pos_can_be_considered_the_same(item_pos, tgt_pos,
                                                                 [ancient_lang_icon_size[0] // 2,
                                                                  ancient_lang_icon_size[1] // 2]):
                            continue
                        to_pop_idx = tgt_idx
                        break

                    # 抛出不需要移动目的地的坐标
                    if to_pop_idx is not None:
                        tgt_poses.pop(to_pop_idx)
                        continue

                    # 否则把该点进行记录，为其分配一个目标坐标，稍后进行移动
                    real_need_to_drag_poses_group.append((item_pos, tgt_poses.pop()))

                # 模拟拖拽
                for src_pos, tgt_pos in real_need_to_drag_poses_group:
                    MouseSimulate.drag(src_pos[0], src_pos[1], tgt_pos[0], tgt_pos[1], duration=duration)
                    MouseSimulate.click()

                can_wheel_down = True
                break

            # 如果剩余的古语卷轴的数量大于5张
            if len(item_poses) >= 5:
                # 先计算出用于合成卷轴的5个点
                pos_1_x = work_area_bbox[0] + col_space_width * 2 + round(1.5 * ancient_lang_icon_size[0])
                pos_1_y = work_area_bbox[1] + row_space_height + ancient_lang_icon_size[1] // 2

                pos_2_x = pos_1_x - col_space_width - ancient_lang_icon_size[0]
                pos_2_y = pos_1_y + row_space_height + ancient_lang_icon_size[1]

                pos_3_x = pos_1_x
                pos_3_y = pos_1_y + row_space_height + ancient_lang_icon_size[1]

                pos_4_x = pos_1_x + col_space_width + ancient_lang_icon_size[0]
                pos_4_y = pos_1_y + row_space_height + ancient_lang_icon_size[1]

                pos_5_x = pos_1_x
                pos_5_y = pos_3_y + row_space_height + ancient_lang_icon_size[1]

                prev = 0
                cur = 5
                while True:
                    # 说明当前也的古语数量不再支持合成了，跳出循环
                    if len(item_poses) < 5:
                        break

                    cur_poses = [item_poses.pop(0) for _ in range(5)]
                    tgt_poses = [(pos_1_x, pos_1_y), (pos_2_x, pos_2_y), (pos_3_x, pos_3_y), (pos_4_x, pos_4_y),
                                 (pos_5_x, pos_5_y)]

                    # 相似相容处理，避免出现古语在目标位置上，但仍然需要替换的情况
                    real_need_to_drag_poses_group = []
                    while len(cur_poses) > 0:
                        item_pos = cur_poses.pop()
                        to_pop_idx = None
                        for tgt_idx, tgt_pos in enumerate(tgt_poses):
                            if not is_pos_can_be_considered_the_same(item_pos, tgt_pos,
                                                                     [ancient_lang_icon_size[0] // 2,
                                                                      ancient_lang_icon_size[1] // 2]):
                                continue
                            to_pop_idx = tgt_idx
                            break

                        # 抛出不需要移动目的地的坐标
                        if to_pop_idx is not None:
                            tgt_poses.pop(to_pop_idx)
                            continue

                        # 否则把该点进行记录，为其分配一个目标坐标，稍后进行移动
                        real_need_to_drag_poses_group.append((item_pos, tgt_poses.pop()))

                    for src_pos, tgt_pos in real_need_to_drag_poses_group:
                        MouseSimulate.drag(src_pos[0], src_pos[1], tgt_pos[0], tgt_pos[1], duration=duration)
                        MouseSimulate.click()

                    time.sleep(0.2)
                    # 合成卷轴
                    use_merge_button(win_dc, bdo_rect, bag_bbox)
                    prev += 5
                    cur += 5

        # 否则鼠标移动回背包内，滚轮往下滑动看看是否有其他合成图标
        MouseSimulate.move(into_bag_pos[0], into_bag_pos[1], duration=duration)
        for i in range(step):
            MouseSimulate.wheel(-100)
        MouseSimulate.move(out_to_bag_pos[0], out_to_bag_pos[1])
        cur_step += step

    # ocr 一下当前背包的容量，判断是否需要进一步对话
    cur_space, total_space = get_bag_capacity_by_tesseract_ocr(win_dc, bag_bbox_no_abs)
    if None in [cur_space, total_space]:
        reason = "ocr无法获取背包容量"

    if total_space - cur_space < 10:
        to_continue = False

    # 关闭背包并结束
    classics_op.close_bag()

    return success, to_continue, reason
