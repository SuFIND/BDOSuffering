class OverSig(Exception):
    """正常结束"""
    pass


class StopSig(Exception):
    """停止信号"""
    pass


class FormatMsg:
    def __init__(self, source):
        self.source = source

    def to_str(self, msg, level="info", ):
        return f"{level}${self.source}${msg}"
