import time

import win32gui

import operation.classics_op as classics_op
import operation.cv_op as cv_op
from app.init_func import init_labels_dic
from utils.capture_utils import WinDCApiCap
from utils.cv_utils import Detector
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect

if __name__ == '__main__':
    for i in [3, 2, 1]:
        time.sleep(1)
        print(i)
    print("start ...")

    # 资源
    labels_dic = init_labels_dic("data/onnx/class_20230206.txt")
    detector = Detector("data/onnx/20220201.onnx", labels_dic)
    window_class = "BlackDesertWindowClass"
    window_title = "黑色沙漠 - 435534"
    hwnd = win32gui.FindWindow(window_class, window_title)

    start_at = time.perf_counter()

    # TODO

    classics_op.reset_viewer()
    time.sleep(1)
    classics_op.into_action_state()
    time.sleep(2)
    classics_op.reposition_after_call()

    end_at = time.perf_counter()
    print("cost", round(end_at - start_at, 2))
