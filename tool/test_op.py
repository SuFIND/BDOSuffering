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
from operation.cv_op import get_bag_ui_bbox
from operation.v2 import start_merge

from app.init_resource import global_var

if __name__ == '__main__':
    for i in [3, 2, 1]:
        time.sleep(1)
        print(i)
    print("start ...")

    # 资源
    # labels_dic = init_labels_dic("data/onnx/class_20230206.txt")
    # detector = Detector("data/onnx/20230206.onnx", labels_dic)
    window_class = "BlackDesertWindowClass"
    window_title = "黑色沙漠 - 436751"
    # hwnd = win32gui.FindWindow(window_class, window_title)
    # win_dc = WinDCApiCap(hwnd)

    start_at = time.perf_counter()

    sig_dic = {"start": True, "stop": False, "pause": False}
    l = Lock()
    msg_queue=queue.Queue()

    start_merge(
        sig_dic=sig_dic,
        sig_mutex=l,
        msg_queue=msg_queue,
        window_title=window_title,
        window_class=window_class,
        title_height=30,
        onnx_path="data/onnx/20230215.onnx",
        label_dic_path="data/onnx/class_20230215.txt",
        debug=False,
        gui_params={}
    )

    end_at = time.perf_counter()
    print("cost", round(end_at - start_at, 2))
