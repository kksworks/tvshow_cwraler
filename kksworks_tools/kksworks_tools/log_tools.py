#!/usr/bin/env python3
"""
log wrapper tools
"""
import sys
from typing import Optional, Literal, TextIO, Any
import logging
import logging.handlers
import datetime
import pathlib
import inspect

from dataclasses import dataclass


class LogTools:
    """log tools :  python logging wrapping api"""

    @dataclass
    class DebugLevelInfo:
        """mange logger data :"""

        msg_prefix: str
        logging_level: int

    DEBUG = DebugLevelInfo("D", logging.DEBUG)
    INFO = DebugLevelInfo("I", logging.INFO)
    WARN = DebugLevelInfo("W", logging.WARN)
    ERR = DebugLevelInfo("E", logging.ERROR)

    def __init__(
        self,
        loger_name: str,
        log_level=Literal["DEBUG", "INFO", "WARN", "ERROR"],
        default_print_buf: TextIO = sys.stdout,
        print_func_deco: bool = True,
        print_verbos: bool = True,
        logfile_path: Optional[str] = None,
        logfile_size_kb: int = 0,
    ):
        """_summary_

        Args:
            loger_name (str): 로거 이름
            log_level (str): log level ["DEBUG", "INFO", "WARN", "ERROR"].
            default_print_buf (TextIO, optional): default print std output io. Defaults to sys.stdout.
            print_func_deco (bool, optional): print api call . Defaults to True.
            print_verbos (bool, optional): print api detail info. Defaults to True.
            logfile_path (Optional[str], optional): save log file path. Defaults to None.
            logfile_size_kb (int, optional): log file size. Defaults to 0.

        Returns:
            _type_: _description_
        """
        self.loger_name = loger_name
        self.logger = logging.getLogger(self.loger_name)

        self.log_level_info = self._get_log_level_info(log_level)
        self.print_verbos = print_verbos
        self.print_func_deco = print_func_deco

        self.default_print_buf = default_print_buf

        # if exist hander --> skip set handler
        if self.logger.hasHandlers() is True:
            return None

        self.logger.setLevel(self.log_level_info.logging_level)

        # default initialize for logging class..

        # log file setting
        if logfile_size_kb > 0 and logfile_path is not None:
            self.set_log_files(logfile_path, logfile_size_kb)

        self._set_loger_init()

    def _set_loger_init(self) -> None:
        class InfoFilter(logging.Filter):
            def filter(self, record):
                return record.levelno in (logging.DEBUG, logging.INFO, logging.ERROR)

        stdout_handler = logging.StreamHandler(self.default_print_buf)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.addFilter(InfoFilter())
        self.logger.addHandler(stdout_handler)

    def _get_log_level_info(self, log_level=Literal["DEBUG", "INFO", "WARN", "ERROR"]) -> DebugLevelInfo:
        if log_level == "DEBUG":
            return self.DEBUG
        elif log_level == "INFO":
            return self.INFO
        elif log_level == "WARN":
            return self.WARN
        elif log_level == "ERROR":
            return self.ERR
        else:
            return self.DEBUG

    def set_log_verbos(self, print_func_deco: Optional[bool] = None, print_verbos: Optional[bool] = None) -> None:
        """log print 에 대한 verbose 기능을 지원한다.

        - print_func_deco : function trace deco 에 대한 print 여부 결정
        - print_verbos : prefix 에 api 정보 프린트

        Args:
            print_func_deco (bool): function trace deco 에 대한 print 여부.
            print_verbos (bool): prefix 에 api 정보 프린트.
        """
        if print_func_deco is not None:
            self.print_func_deco = print_func_deco
        if print_verbos is not None:
            self.print_verbos = print_verbos

    def set_log_level(self, log_level=Literal["DEBUG", "INFO", "WARN", "ERROR"]) -> None:
        """log level 을 지정한다.
        - "DEBUG", "INFO", "WARN", "ERROR" 만 지원

        Args:
            log_level (str): set log level
        """
        self.log_level_info = self._get_log_level_info(log_level)
        self.logger.setLevel(self.log_level_info.logging_level)

    def set_log_files(self, logfile_path: str, logfile_size_kb: int, replace_hander: bool = True) -> None:
        """log 파일 저장여부 결정

        Args:
            logfile_path (str): 로그파일 저장경로
            logfile_size_kb (int): 로그파일 최대 저장 사이즈
            replace_hander (bool, optional): 기존 로그파일 핸들러를 교체할지 말지 (append 지원). Defaults to True.
        """
        file_max_bytes = 1024 * 1024 * logfile_size_kb

        if replace_hander is True:
            for hdlr in self.logger.handlers[:]:  # remove the existing file handlers
                if isinstance(hdlr, logging.handlers.RotatingFileHandler):
                    self.logger.removeHandler(hdlr)

        self.file_handler = logging.handlers.RotatingFileHandler(logfile_path, maxBytes=file_max_bytes, backupCount=10)
        self.logger.addHandler(self.file_handler)

    def clear_logfile_hanlder(self) -> None:
        """기존 로그파일 핸들러를 모두 삭제"""

        for hdlr in self.logger.handlers[:]:  # remove the existing file handlers
            if isinstance(hdlr, logging.handlers.RotatingFileHandler):
                self.logger.removeHandler(hdlr)

    def _log_msg_prefix(self, log_level_prefix: str) -> str:
        timestamp_str = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        # time and debug level prefix :: ex -> "[220825_104055|hello world|D] - "
        prefix_msg = f"[{timestamp_str}|{self.loger_name}|{log_level_prefix}] - "

        if self.print_verbos is True:
            # call file info :: ex -> "file_name(fine_name_lineno)"
            prefix_msg += str(pathlib.PurePath(inspect.stack()[2].filename).stem)
            prefix_msg += "(" + str(inspect.stack()[2].lineno) + ") | "

            # call api info :: ex -> "api_name()"
            prefix_msg += str(inspect.stack()[2][3]) + "() : "

        return prefix_msg

    # err msg
    def err(self, msg: str) -> None:
        """print err

        Args:
            msg (_type_): _description_
        """
        target_log_level = self.ERR.logging_level
        target_log_prefix = self.ERR.msg_prefix

        if self.log_level_info.logging_level <= target_log_level:
            print_msg = self._log_msg_prefix(target_log_prefix)
            print_msg += str(msg)
            self.logger.error(print_msg)

    def info(self, msg: str) -> None:
        """info print

        Args:
            msg (_type_): message
        """
        target_log_level = self.INFO.logging_level
        target_log_prefix = self.INFO.msg_prefix

        if self.log_level_info.logging_level <= target_log_level:
            print_msg = self._log_msg_prefix(target_log_prefix)
            print_msg += str(msg)
            self.logger.info(print_msg)

    def warn(self, msg: str) -> None:
        """wran print

        Args:
            msg (_type_): message
        """
        target_log_level = self.WARN.logging_level
        target_log_prefix = self.WARN.msg_prefix

        if self.log_level_info.logging_level <= target_log_level:
            print_msg = self._log_msg_prefix(target_log_prefix)
            print_msg += str(msg)
            self.logger.debug(print_msg)

    def dbg(self, msg: str) -> None:
        """debug print

        Args:
            msg (_type_): message
        """
        target_log_level = self.DEBUG.logging_level
        target_log_prefix = self.DEBUG.msg_prefix

        if self.log_level_info.logging_level <= target_log_level:
            print_msg = self._log_msg_prefix(target_log_prefix)
            print_msg += str(msg)
            self.logger.debug(print_msg)

    def func_trace(self, original_function: Any) -> Any:
        """decoration function : trace function call
        - using verbose option

        Args:
            original_function (_type_): internal using

        Returns:
            Any: internal using
        """

        def func_trace(*args, **kwargs):
            """deco function (internal using)"""
            if self.print_func_deco:
                self.info(f"{original_function} call start : {args}")
                return_val = original_function(*args, **kwargs)
                self.info(f"{original_function} call end : {return_val} ")
            else:
                return_val = original_function(*args, **kwargs)

        return func_trace

    def exec_trace(self, print_err: bool = True) -> Optional[dict]:
        """err trace info (print call stack)

        Args:
            print_err (bool, optional): _description_. Defaults to True.

        Returns:
            Optional[str]: _description_
        """
        exc_type, _exc_value, exc_traceback = sys.exc_info()
        try:
            assert exc_traceback is not None
            assert exc_type is not None
            traceback_details = {
                "filename": exc_traceback.tb_frame.f_code.co_filename,
                "function_name": exc_traceback.tb_frame.f_code.co_name,
                "lineno": exc_traceback.tb_lineno,
                "except_type": exc_type.__name__,
            }

            if print_err is True:
                self.err("--- err trace info +++")
                self.err(str(traceback_details))
                self.err(f"editor open link : {traceback_details['filename']}:line {traceback_details['lineno']}")
                # File "/works/services-v3/common_tools/web_tools.py", line 10
                self.err("--- err trace info ---")

            return traceback_details
        except Exception as _e:
            return None


# global log api debug handler
log_api = LogTools("api", log_level="DEBUG")
