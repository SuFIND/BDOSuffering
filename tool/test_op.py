import queue
import time
import traceback
import re
from threading import Lock

import win32con
import win32gui
import cv2
import logging as Logger
import operation.classics_op as classics_op
import operation.cv_op as cv_op
from app.init_func import init_labels_dic
from utils.capture_utils import WinDCApiCap
from utils.cv_utils import Detector, color_threshold
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect
from utils.ocr_utils import recognize_numpy
from operation.cv_op import get_bag_ui_bbox
from operation.merge_scroll import retrieve_the_scroll_from_the_trading_warehouse

from app.init_resource import global_var


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
        rst = cur, total
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
    return rst


def get_bag_capacity_by_tesseract_ocr(win_dc: WinDCApiCap, bag_bbox):
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
        color_coverted = cv2.cvtColor(capacity_sc, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(color_coverted)
        string = pytesseract.image_to_string(pil_image, lang="eng",
                                             config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789/")
        r = re.match(r"(?P<cur>\d+)/(?P<total>\d+)", string)
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


if __name__ == '__main__':
    for i in [3, 2, 1]:
        time.sleep(1)
        print(i)
    print("start ...")

    # 资源
    labels_dic = init_labels_dic("data/onnx/class_20230206.txt")
    detector = Detector("data/onnx/20230206.onnx", labels_dic)
    window_class = "BlackDesertWindowClass"
    window_title = "黑色沙漠 - 435839"
    hwnd = win32gui.FindWindow(window_class, window_title)
    win_dc = WinDCApiCap(hwnd)

    start_at = time.perf_counter()

    # TODO
    msg_queue = queue.Queue()
    sig_mutex = Lock()
    sig_dic = dict()
    sig_dic.update({"stop": False, "pause": False, "start": False})
    global_var["BDO_window_title_bar_height"] = 30
    bdo_rect = get_bdo_rect(hwnd)
    bag_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect)

    # sc = cv2.imread("draft/ocr_demo4.jpg")

    retrieve_the_scroll_from_the_trading_warehouse(sig_mutex, sig_dic, msg_queue, detector, hwnd)

    # t_img = detector.test(win_dc.get_hwnd_screenshot_to_numpy_array(), min_score=0.3)
    # cv2.imshow("t_img", t_img)
    # cv2.waitKey(0)

    end_at = time.perf_counter()
    print("cost", round(end_at - start_at, 2))
