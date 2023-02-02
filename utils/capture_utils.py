# -*- coding: utf-8 -*-
"""
@Project : BDOSuffering
@File : capture_utils.py
@Author : SuFIND
@Time : 2022/12/24 16:53
"""
import logging
from ctypes import windll, byref, c_ubyte
from ctypes.wintypes import RECT

import numpy as np
import win32gui

GetDC = windll.user32.GetDC
CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
GetClientRect = windll.user32.GetClientRect
CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
SelectObject = windll.gdi32.SelectObject
BitBlt = windll.gdi32.BitBlt
SRCCOPY = 0x00CC0020
GetBitmapBits = windll.gdi32.GetBitmapBits
DeleteObject = windll.gdi32.DeleteObject
ReleaseDC = windll.user32.ReleaseDC
GetWindowRect = windll.user32.GetWindowRect

# 排除缩放干扰
windll.user32.SetProcessDPIAware()


class WinDCApiCap:
    """
    普通窗口程序截图工具类
    """

    def __init__(self, hwnd):
        self.hwnd = hwnd

    def get_hwnd_screenshot_to_numpy_array(self) -> np.ndarray:
        """
        获取客户区截图
        :return:
        """
        # 获取窗口客户区的大小
        r = RECT()
        GetClientRect(self.hwnd, byref(r))
        width, height = r.right, r.bottom
        # 开始截图
        dc = GetDC(self.hwnd)
        cdc = CreateCompatibleDC(dc)
        bitmap = CreateCompatibleBitmap(dc, width, height)
        SelectObject(cdc, bitmap)
        BitBlt(cdc, 0, 0, width, height, dc, 0, 0, SRCCOPY)
        # 截图是BGRA排列，因此总元素个数需要乘以4
        total_bytes = width * height * 4
        buffer = bytearray(total_bytes)
        byte_array = c_ubyte * total_bytes
        GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
        DeleteObject(bitmap)
        DeleteObject(cdc)
        ReleaseDC(self.hwnd, dc)
        # 返回截图数据为numpy.ndarray
        return np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)

    def is_available(self) -> bool:
        return win32gui.IsWindowEnabled(self.hwnd)


try:
    import d3dshot


    class WinDXApiCap:
        """
        DirectX 窗口程序截图工具类
        用于类似Chrome等DirectX程序截图使用，避免出现黑屏的情况
        """
        d = d3dshot.create(capture_output='numpy')

        def __init__(self, hwnd, display_no=0):
            self.hwnd = hwnd
            self.display_no = display_no

        def get_hwnd_screenshot_to_numpy_array(self) -> np.ndarray:
            pos = win32gui.GetWindowRect(self.hwnd)
            self.d.display = self.d.displays[self.display_no]
            display_position = self.d.display.position
            diff_l_r = display_position["left"]
            diff_t_b = display_position["top"]
            d3dRegion = (pos[0] - diff_l_r, pos[1] - diff_t_b, pos[2] - diff_l_r, pos[3] - diff_t_b)
            return self.d.screenshot(region=d3dRegion)
except ImportError:
    logging.debug("d3dshot is not available!")
