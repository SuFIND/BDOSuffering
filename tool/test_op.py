import time
import traceback

import win32gui
import cv2
import logging as Logger
import operation.classics_op as classics_op
import operation.cv_op as cv_op
from app.init_func import init_labels_dic
from utils.capture_utils import WinDCApiCap
from utils.cv_utils import Detector
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect
from utils.ocr_utils import recognize_numpy
from operation.cv_op import get_bag_ui_bbox

from app.init_resource import global_var


class BagCapacity:
    def __init__(self, cur, total):
        self.cur = cur
        self.total = total
        self.free = total - cur

    def set_cur(self, cur):
        self.cur = cur
        self.free = self.total - self.cur

    def add(self, cnt):
        self.cur = self.cur + cnt
        self.free = self.total - self.cur

    def __str__(self):
        return f"{self.cur}/{self.total}"


def get_bag_capacity_by_ocr(win_dc: WinDCApiCap, bag_bbox):
    rst = None
    if win_dc.is_available():
        return rst

    try:
        sc = win_dc.get_hwnd_screenshot_to_numpy_array()
        bg_sc = sc[bag_bbox[1]:bag_bbox[3], bag_bbox[0]:bag_bbox[2]]

        bg_sc_h, bg_sc_w = bg_sc.shape[:2]
        capacity_left = round(bg_sc_w * 0.85)
        capacity_top = round(bg_sc_h * 0.1)
        capacity_bottom = round(bg_sc_h * 0.2)
        capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]
        ocr_rst = recognize_numpy(capacity_sc)
        text = ocr_rst["text"].replace(" ", "")
        cur, total = text.split("/")
        cur = int(cur)
        total = int(total)
        rst = BagCapacity(cur, total)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
    return rst


if __name__ == '__main__':
    for i in [3, 2, 1]:
        time.sleep(1)
        print(i)
    print("start ...")

    # 资源
    labels_dic = init_labels_dic("data/onnx/class_20230206.txt")
    detector = Detector("data/onnx/20230206.onnx", labels_dic)
    window_class = "BlackDesertWindowClass"
    window_title = "黑色沙漠 - 435534"
    # hwnd = win32gui.FindWindow(window_class, window_title)
    # win_dc = WinDCApiCap(hwnd)

    start_at = time.perf_counter()

    # TODO
    global_var["BDO_window_title_bar_height"] = 30
    # bdo_rect = get_bdo_rect(hwnd)
    # bag_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect)

    sc = cv2.imread("draft/images/1674196043322964200.jpg")
    infer_rst = detector.infer(sc)
    bag_bbox = infer_rst["ui$Bag"][0]["bbox"]
    if not bag_bbox:
        exit(0)
    bg_sc = sc[bag_bbox[1]:bag_bbox[3], bag_bbox[0]:bag_bbox[2]]
    # cv2.imshow("bg_sc", bg_sc)
    # cv2.waitKey(0)

    bg_sc_h, bg_sc_w = bg_sc.shape[:2]
    capacity_left = round(bg_sc_w * 0.85)
    capacity_top = round(bg_sc_h * 0.1)
    capacity_bottom = round(bg_sc_h * 0.2)
    capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]
    #
    # cv2.imshow("capacity_sc", capacity_sc)
    # cv2.waitKey(0)

    ocr_rst = recognize_numpy(capacity_sc)
    text = ocr_rst["text"].replace(" ", "")
    cur, total = text.split("/")
    cur = int(cur)
    total = int(total)
    rst = BagCapacity(cur, total)
    print(rst)

    end_at = time.perf_counter()
    print("cost", round(end_at - start_at, 2))
