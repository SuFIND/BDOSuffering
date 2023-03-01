# -*- coding: utf-8 -*-
# 线程op，专门用于存放一些需要多线程处理的op
import importlib
import time

import pythoncom

from utils.capture_utils import WinDCApiCap
from utils.muti_utils import CanStopThread
from operation.cv_op import collect_client_img


class CollectImgThread(CanStopThread):
    def run(self, hwnd, save_dir: str, duration: float, intervals: float):
        pythoncom.CoInitialize()
        start_at = time.perf_counter()
        win_dc = WinDCApiCap(hwnd)
        while self._running:
            try:
                now = time.perf_counter()
                # 采集任务常规结束
                if now - start_at > duration:
                    self.terminate()
                    break
                # 采集游戏画面
                collect_client_img(win_dc, save_dir)
                # 睡眠一段间隔事件
                time.sleep(intervals)
            except Exception as e:
                break

        pythoncom.CoUninitialize()


def run_thread_op(executor, op_name, args):
    op_model = importlib.import_module("operation.thread_op")
    op = getattr(op_model, op_name)
    op_obj = op()
    executor.submit(op_obj.run, *args)

