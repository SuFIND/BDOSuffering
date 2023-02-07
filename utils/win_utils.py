import ctypes.wintypes

import win32gui, win32api
from app.init_resource import global_var


def get_bdo_rect(hwnd):
    try:
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
    except WindowsError:
        f = None
    title_height = global_var["BDO_window_title_bar_height"]
    if f:
        rect = ctypes.wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        f(ctypes.wintypes.HWND(hwnd),
          ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return rect.left, rect.top + title_height, rect.right, rect.bottom
    else:
        rect = win32gui.GetWindowRect(hwnd)
        title_height = win32api.GetSystemMetrics(12)
        return rect[0], rect[1] + title_height, rect[2], rect[4]
