#!/usr/bin/env python3
"""
my data tools
"""

from typing import Type, TypeVar, Optional
from dataclasses import dataclass, asdict, fields
from dacite import from_dict

from .log_tools import log_api

T = TypeVar("T")


@dataclass
class MyDataTools:
    """dataclass wrapper tool"""

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> Optional[T]:
        """dataclass 를 dict 로 변환

        Args:
            cls (Type[T]): inner class
            data (dict): dict data

        Returns:
            T: data class
        """
        try:
            for data_field in fields(cls):
                if data_field.name not in data:
                    data[data_field.name] = None

            return from_dict(cls, data)
        except Exception:
            log_api.exec_trace()
            return None

    def to_dict(self, remove_none_val: bool = False) -> dict:
        """dataclass 형식을 dict 형태로 변환한다.

        Args:
            remove_none_val (bool, optional): none value 들을 없앨지 말지 결정. Defaults to False.

        Returns:
            dict: 변환된 dict
        """

        def remove_none_from_dict(data):
            """dict none data del"""
            if isinstance(data, dict):
                return {k: v for k, v in data.items() if v is not None}
            else:
                return data

        data_dict = asdict(self)
        if remove_none_val:
            data_dict = {k: remove_none_from_dict(v) for k, v in data_dict.items() if v is not None}
        return data_dict

    def update_field(self, update_data: dict) -> bool:
        """
        특정 필드만 업데이트. 해당 인스턴스를 사용할경우 하위 필드들도 업데이트한다.

        >>> update_field({'target_key' : target_val })

        Args:
            update_data (dict): update 할 데이터, dict 형식으로 전달, 타겟 데이터 형식과 맞아야한다.

        Returns:
            bool: update 결과
        """

        try:
            for key, val in update_data.items():
                if hasattr(getattr(self, key), "update_field"):
                    getattr(self, key).update_field(val)
                elif hasattr(self, key):
                    setattr(self, key, val)
            return True
        except Exception:
            return False
