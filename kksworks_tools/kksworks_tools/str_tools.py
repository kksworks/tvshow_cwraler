#!/usr/bin/env python3
from typing import Union, List, Optional
import re
import datetime
import string
import random

from .log_tools import log_api


def time_conv(conv_target: Union[str, datetime.datetime]) -> Optional[datetime.datetime]:
    """일반 string 형태를 datetime 으로 변환

    - 자유로운 string 형식을 입력하더라도 변환
    - 단 일관적인 변환을 위해서 datetime 인자도 받아드릴수있다 -> bypass return

    Args:
        conv_target (Union[str, datetime.datetime]): 변환하고자하는 date str

    Returns:
        datetime.datetime: convert datetime
    """

    # if isinstance(conv_target, datetime.datetime):
    #     return conv_target
    today_str_patterns = ["오늘", "today"]
    time_patterns = [
        "%m-%d",
        "%m.%d",
        "%m/%d",
        "%H:%M",
        "%H:%M:%S",
        "%Y/%m",
        "%Y%m%d",
        "%Y/%m/%d",
        "%y/%m/%d",
        "%Y-%m-%d",
        "%y-%m-%d",
        "%y%m%d",
        "%y.%m.%d",
        "%Y%m%d",
        "%Y.%m.%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d_%H:%M:%S",
        "%Y-%m-%d-%p-%I:%M",
        "%w %m %d %Y %H:%M:%S",
        "%a %b %d %Y %H:%M:%S",
    ]

    try:
        assert conv_target is not None
        if isinstance(conv_target, datetime.datetime):
            return conv_target

        today_date = datetime.datetime.today().date()
        conv_date = None

        # check today pattern
        for _chk_pattern in today_str_patterns:
            if conv_target.find(_chk_pattern) >= 0:
                return datetime.datetime.today()

        # covert str to datetime pattern
        for _chk_pattern in time_patterns:
            try:
                conv_date = datetime.datetime.strptime(conv_target, _chk_pattern)
            except Exception:
                pass
            finally:
                continue

        if conv_date is None:
            return conv_date

        # date time 에서 날짜 정보만 없을경우
        if conv_date.year == 1900 and conv_date.month == 1 and conv_date.day == 1:
            conv_date = conv_date.replace(year=today_date.year, month=today_date.month, day=today_date.day)
        # date time 에서 년도 정보만 없을경우
        elif conv_date.year == 1900:
            conv_date = conv_date.replace(year=today_date.year)

        return conv_date

    except Exception:
        log_api.exec_trace()
        return None


def replace_spaces_char(input_str: str, replace_str: str) -> str:
    """연속적인 space (공백)을 변환한다.

    Args:
        input_str (str): input string
        replace_str (str): 변환하고자 하는 문자열

    Returns:
        str: return string
    """
    return re.sub(r"(\ {1,100})", replace_str, input_str)


def replace_etc_char(input_str: str, replace_str: str) -> str:
    """한글, 영어, 숫자를 제외한 모든 문자 수정

    Args:
        input_str (str): input string
        replace_str (str): 변환하고자 하는 문자열

    Returns:
        str: return string
    """
    pattern = r"[^a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ가-힣]"
    return re.sub(pattern, replace_str, input_str)


def get_valid_str_token(input_str: str) -> List[str]:
    """한글, 영어, 숫자만 꺼낸다 토큰형태로

    Args:
        input_str (str): input string

    Returns:
        _type_: string list
    """
    replace_str = replace_etc_char(input_str, " ")
    replace_str = replace_spaces_char(replace_str, " ")
    return replace_str.split(" ")


def replace_newline_string(input_str: str, replace_str: str) -> str:
    """new line 문자열을 수정한다.

    Args:
        input_str (str): input string
        replace_str (str): 변환하고자 하는 문자열

    Returns:
        str: return string
    """
    pattern = r"[\r\n]"
    return re.sub(pattern, replace_str, input_str)


def get_number_string(input_str: str) -> List[str]:
    """숫자만 꺼낸다. 이때 소숫점까지 지원하기위해서 . 까지 포함한 숫자만꺼냄 (list 형태)
    - 연속적인 숫자만꺼낸다.

    Args:
        input_str (str): input string

    Returns:
        _type_: return string
    """
    find_pattern = r"\d+\.\d+|\d+"
    return re.findall(find_pattern, input_str)


def conv_kor_currency_bill(input_number: Union[str, int, float]) -> str:
    """일반 원화 숫자를 억원으로 변환한다

    Args:
        input_number (Union[str, int, float]): input number

    Returns:
        str: _description_
    """
    if isinstance(input_number, str):
        input_number = input_number.replace(",", "")

    conv_num = float(input_number) / 100000000
    return f"{conv_num:.1f} 억원"


def random_generator(size: int = 6) -> str:
    """random string generate

    Args:
        size (int, optional): random string len. Defaults to 6.

    Returns:
        str: random string
    """
    random_chars = string.ascii_letters + string.digits
    return "".join(random.choice(random_chars) for _ in range(size))
