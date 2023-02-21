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

if __name__ == '__main__':
    for i in [3, 2, 1]:
        time.sleep(1)
        print(i)
    print("start ...")

    # 资源
    # labels_dic = init_labels_dic("data/onnx/class_20230206.txt")
    # detector = Detector("data/onnx/20230206.onnx", labels_dic)
    # window_class = "BlackDesertWindowClass"
    # window_title = "黑色沙漠 - 435839"
    # hwnd = win32gui.FindWindow(window_class, window_title)
    # win_dc = WinDCApiCap(hwnd)

    start_at = time.perf_counter()

    classics_op.skill_action()

    end_at = time.perf_counter()
    print("cost", round(end_at - start_at, 2))
