# -*- coding: utf-8 -*-
import os
import re
import time
import cv2
import numpy as np
import traceback
import operation.classics_op as classics_op
from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect
from utils.cv_utils import Detector
from utils.muti_utils import FormatMsg
from utils.ocr_utils import recognize_numpy
from utils.log_utils import Logger
import operation.cv_op as cv_op

fmmsg = FormatMsg(source="模拟动作")


def get_merge_button_by_temple(win_dc: WinDCApiCap, client_rect) -> [tuple, None]:
    if not win_dc.is_available():
        return None
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/mergeButton.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2


def merge_scroll_written_in_ancient_language(detector, hwnd, debug=False):
    """
    合并古语卷轴
    :param detector:
    :param hwnd:
    :param debug:
    :return:
    """
    # 背包的可拖拽区域
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)
    bag_bbox = cv_op.get_bag_ui_bbox(detector, win_dc, bdo_rect, debug=debug)

    if bag_bbox is None:
        return False

    bag_left, bag_top, bag_right, bag_bottom = bag_bbox
    into_bag_pos = round((bag_right + bag_left) / 2), round((bag_top + bag_bottom) / 2)
    out_to_bag_pos = bag_left - 30, bag_top - 30
    # TODO 接入 Windows OCR， 请参考WinRT

    # 先扫描背包中可以直接合成的卷轴
    # # 先移动到UI外避免对古语卷轴识别的干扰
    ms.move(out_to_bag_pos[0], out_to_bag_pos[1])

    step = 4
    cur_step = 0
    max_step = 16
    while cur_step <= max_step:
        # 识别是否有合成的小icon
        merge_button_pos = get_merge_button_by_temple(win_dc, bdo_rect)

        # 如果有，则移动鼠标到小icon上，并点击合成
        if merge_button_pos is not None:
            ms.move(merge_button_pos[0], merge_button_pos[1], duration=0.1)
            ms.click()

        # 否则鼠标移动回背包内，滚轮往下滑动看看是否有其他合成图标
        else:
            ms.move(into_bag_pos[0], into_bag_pos[1], duration=0.1)
            for i in range(step):
                ms.wheel(-100)
            cur_step += step

    pass


def get_bag_capacity_by_ocr(win_dc: WinDCApiCap, bag_bbox):
    rst = None
    if win_dc.is_available():
        return rst

    try:
        sc = win_dc.get_hwnd_screenshot_to_numpy_array()
        bg_sc = sc[bag_bbox[1]:bag_bbox[3], bag_bbox[0]:bag_bbox[2]]

        bg_sc_h, bg_sc_w = bg_sc.shape[:2]
        capacity_left = round(bg_sc_w * 0.8125)
        capacity_top = round(bg_sc_h * 0.1)
        capacity_bottom = round(bg_sc_h * 0.2)
        capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]

        ocr_rst = recognize_numpy(capacity_sc, lang="en-US")
        text = ocr_rst["text"]
        clear_text = ""
        for char in text:
            if char not in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "/"}:
                continue
            clear_text += char

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


def get_market_management_gps_pos(win_dc: WinDCApiCap, bdo_rect):
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
    c_left, c_top, _, _ = bdo_rect
    for i in range(retry + 1):
        img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/TradingWarehouse")
        infer_rst = detector.infer(img)
        if "ui$Trading Warehouse" not in infer_rst:
            continue

        bbox_tup = infer_rst["ui$Trading Warehouse"][0]["bbox"]
        return bbox_tup[0] + c_left, bbox_tup[1] + c_top, bbox_tup[2] + c_left, bbox_tup[3] + c_top


def got_trading_warehouse_and_bag_ui_bbox(detector: Detector, win_dc, bdo_rect, retry: int, debug=False):
    c_left, c_top, _, _ = bdo_rect
    bag_bbox = None
    trading_warehouse_bbox = None
    for i in range(retry + 1):
        if bag_bbox is not None and trading_warehouse_bbox is not None:
            break

        img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/TradingWarehouseAndBag")
        infer_rst = detector.infer(img)
        if "ui$Trading Warehouse" in infer_rst and trading_warehouse_bbox is None:
            bbox = infer_rst["ui$Trading Warehouse"][0]["bbox"]
            trading_warehouse_bbox = bbox[0] + c_left, bbox[1] + c_top, bbox[2] + c_left, bbox[3] + c_top
        if "ui$Bag" in infer_rst and bag_bbox is None:
            bbox = infer_rst["ui$Bag"][0]["bbox"]
            bag_bbox = bbox[0] + c_left, bbox[1] + c_top, bbox[2] + c_left, bbox[3] + c_top

    return bag_bbox, trading_warehouse_bbox


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
    template = cv2.imread("data/temple/ScrollWrittenInAncientLanguage.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    poses = []
    for pt_left, pt_top in zip(*loc[::-1]):
        poses.append((cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2))
    return poses


def get_scroll_written_in_ancient_language_pos_which_one_belong_trading_warehouse_by_temple(win_dc: WinDCApiCap,
                                                                                            client_rect,
                                                                                            trading_warehouse_bbox) -> list:
    """
    用过模版匹配找到位于交易所仓库的古语召唤卷轴的位置
    :param win_dc:
    :param client_rect:
    :param trading_warehouse_bbox:
    :return:
    """
    rst = None
    item_poses = get_scroll_written_in_ancient_language_poses_by_temple(win_dc, client_rect)
    for pos in item_poses:
        # 如果不在交易仓库的UI范围内则舍弃
        if not trading_warehouse_bbox[0] < pos[0] < trading_warehouse_bbox[2] \
                or not trading_warehouse_bbox[1] < pos[1] < trading_warehouse_bbox[3]:
            continue
        rst = pos
        break
    return rst


def retrieve_the_scroll_from_the_trading_warehouse(sig_mutex, sig_dic, msg_queue, detector: Detector, hwnd,
                                                   debug=False):
    """
    从交易所取回当前背包下可容纳的最大安全数量的古语卷轴
    """
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    cur_step = 0
    max_step = 0
    bag_bbox = None
    trading_warehouse_bbox = None
    ancient_language_scroll_wheel_cur_step = 0
    ancient_language_scroll_wheel_max_step = 32
    into_trading_warehouse_bbox_pos = None
    out_to_trading_warehouse_bbox_pos = None

    q = [
        (kb.press_and_release, ("R",), "按下R与鲁西比恩坤对胡"),
        (time.sleep, (0.5,), "动画0.5s"),
        (kb.press_and_release, ("2",), "按下2进入交易所仓库UI"),
        (time.sleep, (0.5,), "动画0.5s"),
        (get_market_management_gps_pos, (win_dc, bdo_rect,), "是否找到交易所按钮"),
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

        if func.__name__ == "get_market_management_gps_pos":
            # 如果获取不到按钮“交易所仓库”的坐标
            if rst is None:
                q.extend([
                    (kb.press_and_release, ("esc",), "退出交易所UI"),
                    (kb.press_and_release, ("2",), "按下2进入交易所仓库UI"),
                    (time.sleep, (0.5,), "动画0.5s"),
                    (get_market_management_gps_pos, (win_dc, bdo_rect,), "是否找到交易所按钮"),
                ])

            # 如果获取到按钮“交易所仓库”的坐标
            else:
                q.extend([
                    (ms.move, (rst[0], rst[1], 0.1), "鼠标移动到`交易所仓库`按钮上"),
                    (ms.click, (), "点击鼠标左键"),
                    (time.sleep, (0.5,), "动画0.5s"),
                    (got_trading_warehouse_and_bag_ui_bbox, (detector, win_dc, bdo_rect, 2, debug),
                     "是否找到交易仓库和背包的UI"),
                ])

        # 目标检测-交易仓库和背包UI
        elif func.__name__ == "got_trading_warehouse_and_bag_ui_bbox":
            bag_bbox, trading_warehouse_bbox = rst

            # 如果找不到背包或者交易仓库的UI
            if bag_bbox is None or trading_warehouse_bbox is None:
                q.extend([
                    (kb.press_and_release, ("esc",), "退出交易所UI"),
                    (kb.press_and_release, ("2",), "按下2进入交易所仓库UI"),
                    (time.sleep, (0.5,), "动画0.5s"),
                    (get_market_management_gps_pos, (win_dc, bdo_rect,), "是否找到交易所按钮"),
                ])

            # 如果背包的UI和交易所的UI都找到了
            else:
                into_trading_warehouse_bbox_pos = (trading_warehouse_bbox[0] + trading_warehouse_bbox[2]) / 2, (trading_warehouse_bbox[1] + trading_warehouse_bbox[3]) / 2
                out_to_trading_warehouse_bbox_pos = trading_warehouse_bbox[0] - 50, trading_warehouse_bbox[1] - 50

                q.extend([
                    (get_bag_capacity_by_ocr, (detector, bag_bbox), "获取背包的空间情况"),
                ])

        # 获取背包的空间情况
        elif func.__name__ == "get_bag_capacity_by_ocr":
            cur, total = rst
            # 如果OCR无法支持识别背包容量
            if cur is None or total is None:
                q.extend([
                    (kb.press_and_release, ("esc",), "退出交易所仓库与背包Ui"),
                    (kb.press_and_release, ("esc",), "退出与鲁西比恩坤的对话UI"),
                ])
                msg_queue.put(fmmsg.to_str("OCR无法成功识别背包容量", level="error"))

            else:
                max_step = (total - cur) // 20
                q.extend([
                    (ms.move, (out_to_trading_warehouse_bbox_pos[0], out_to_trading_warehouse_bbox_pos[1], 0.1), "鼠标移到到交易仓库UI外，防止干扰识别古语卷轴"),
                    (get_scroll_written_in_ancient_language_pos_which_one_belong_trading_warehouse_by_temple, (win_dc, bdo_rect, trading_warehouse_bbox), "找到在交易所仓库内存放的古语的坐标位置"),
                ])

        elif func.__name__ == "get_scroll_written_in_ancient_language_pos_which_one_belong_trading_warehouse_by_temple":
            wheel_step = 4
            if rst is None and ancient_language_scroll_wheel_cur_step <= ancient_language_scroll_wheel_max_step:
                q.append((ms.move, (into_trading_warehouse_bbox_pos[0], into_trading_warehouse_bbox_pos[1], 0.1), "鼠标移到到交易仓库UI外，防止干扰识别古语卷轴"))
                for i in range(wheel_step):
                    q.append((ms.wheel, (-100, ), "向下滚动"))
                q.extend([
                    (ms.move, (out_to_trading_warehouse_bbox_pos[0], out_to_trading_warehouse_bbox_pos[1], 0.1),
                     "鼠标移到到交易仓库UI外，防止干扰识别古语卷轴"),
                    (get_scroll_written_in_ancient_language_pos_which_one_belong_trading_warehouse_by_temple, (win_dc, bdo_rect, trading_warehouse_bbox), "找到在交易所仓库内存放的古语的坐标位置"),
                ])
            if rst is None and ancient_language_scroll_wheel_cur_step > ancient_language_scroll_wheel_max_step:
                q.extend([
                    (kb.press_and_release, ("esc",), "退出交易所仓库与背包Ui"),
                    (kb.press_and_release, ("esc",), "退出与鲁西比恩坤的对话UI"),
                ])
                msg_queue.put(fmmsg.to_str('找不到更多的”用古语记录的卷轴“，请及时向交易仓库不愁卷轴！', level="info"))

            elif rst is not None and cur_step < max_step:
                q.extend([
                    (ms.move, (rst[0], rst[1], 0.1), "鼠标移到到古语卷轴上"),
                    (time.sleep, (0.5,), "等待动画0.5s"),
                    (ms.click, (ms.RIGHT, ), "鼠标右键准备把物品移动到背包"),
                    (time.sleep, (0.5,), "等待动画0.5s"),
                    (kb.press_and_release, ("F",), "填写最大数量20"),
                    (ms.move, (out_to_trading_warehouse_bbox_pos[0], out_to_trading_warehouse_bbox_pos[1], 0.1),
                     "鼠标移到到交易仓库UI外，防止干扰识别古语卷轴"),
                    (get_scroll_written_in_ancient_language_pos_which_one_belong_trading_warehouse_by_temple,
                     (win_dc, bdo_rect, trading_warehouse_bbox), "找到在交易所仓库内存放的古语的坐标位置"),
                ])
                cur_step += 1
            else:
                # 说明完成了从交易仓库到背包的物品转移，正常置空队列即可
                pass