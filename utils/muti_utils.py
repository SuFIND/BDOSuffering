import time
from threading import Thread


class FormatMsg:
    def __init__(self, source):
        self.source = source

    def to_str(self, msg, level="info", ):
        return f"msg::{level}${self.source}${msg}"


class CanStopThread():
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    # 这是一个末班，请继承并重写次方法
    # def run(self):
    #     while self._running:
    #         time.sleep(5)
