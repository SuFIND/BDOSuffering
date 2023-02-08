# -*- coding: utf-8 -*-
import os
import time
import cv2
import numpy as np
import operation.classics_op as classics_op
from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect
from utils.ocr_utils import recognize_numpy
import operation.cv_op as cv_op


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
    class _BagCapacity:
        def __init__(self, free, total):
            self.free = free
            self.total = total

    rst = _BagCapacity(0, 0)
    sc = win_dc.get_hwnd_screenshot_to_numpy_array()
    bg_sc = sc[bag_bbox[0]:bag_bbox[2], bag_bbox[1]:bag_bbox[3]]
