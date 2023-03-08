import os
import logging.handlers


class Logger:
    # 初始化日志模块
    logging.basicConfig()
    _logger = logging.getLogger("app")
    _logger.setLevel(logging.INFO)
    _log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(_log_dir):
        os.mkdir(_log_dir)
    _timeFileHandler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(_log_dir, "BDOWingman.log"),
        when='midnight',
        interval=1,
        backupCount=7,
        encoding="utf8",
    )
    _timeFileHandler.suffix = "%Y-%m-%d_%H-%M-%S.log"
    _formatter = logging.Formatter('%(asctime)s|%(name)s | %(levelname)s | %(message)s')
    _timeFileHandler.setFormatter(_formatter)
    _logger.addHandler(_timeFileHandler)

    @classmethod
    def set_log_name(cls, name):
        # 先写在原有的loggerHandler
        cls._logger.removeHandler(cls._timeFileHandler)

        cls._timeFileHandler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(cls._log_dir, name),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding="utf8",
        )
        cls._timeFileHandler.suffix = "%Y-%m-%d.log"
        cls._formatter = logging.Formatter('%(asctime)s|%(name)s | %(levelname)s | %(message)s')
        cls._timeFileHandler.setFormatter(cls._formatter)
        cls._logger.addHandler(cls._timeFileHandler)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        cls._logger.error(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        cls._logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        cls._logger.warning(msg, *args, **kwargs)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        cls._logger.debug(msg, *args, **kwargs)

    @classmethod
    def shutdown(cls):
        logging.shutdown()
