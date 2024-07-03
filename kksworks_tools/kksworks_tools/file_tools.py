#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""file manage apis"""

import os
import shutil
import pathlib
import hashlib

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FileInfo:
    """file info"""

    file_name: str
    file_ext: str
    is_file: bool
    is_dir: bool
    file_size: int
    file_full_name: str
    abpath_full: str
    abpath_folder: str


def join_path(*args) -> str:
    """path join"""
    path = ""
    for arg in args:
        path = str(pathlib.PurePath(path, arg))
    return path


def is_file_exist(target_path: str) -> bool:
    """file exist check"""
    try:
        return pathlib.Path(target_path).is_file()
    except Exception:
        return False


def is_folder_exist(target_path: str) -> bool:
    """is folder exist"""
    # pathlib.Path(target_path).mkdir(exist_ok=True, parents=True)
    return pathlib.Path(target_path).is_dir()


def get_file_size(file_path: str) -> int:
    """get file size"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return -1


def touch_file(*args) -> None:
    """touch file if folder not exist mk dir"""
    target_file_full_path = join_path(*args)
    folder_path = pathlib.Path(target_file_full_path).resolve().parent
    pathlib.Path(folder_path).mkdir(exist_ok=True, parents=True)
    pathlib.Path(target_file_full_path).touch()


def delete_file(target_path) -> None:
    """delete file"""
    try:
        pathlib.Path(target_path).unlink()
        return None
    except Exception:
        return None


def get_current_file_path(target_path) -> str:
    """get current file path"""
    return str(pathlib.Path(target_path).resolve().parent)


def get_file_info(target_path: str) -> Optional[FileInfo]:
    """file info"""
    try:
        file_name = str(pathlib.PurePath(target_path).stem)
        file_ext = str(pathlib.PurePath(target_path).suffix)
        abpath_full = str(pathlib.PurePath(str(pathlib.Path(target_path).resolve())))
        return FileInfo(
            file_name=file_name,
            file_ext=file_ext,
            is_file=pathlib.Path(target_path).is_file(),
            is_dir=pathlib.Path(target_path).is_dir(),
            file_size=get_file_size(target_path),
            file_full_name=file_name + file_ext,
            abpath_full=abpath_full,
            abpath_folder=str(pathlib.PurePath(abpath_full).parent),
        )
    except Exception:
        return None


def get_fileinfo_from_folder(target_path: str, file_patterns: List[str], exclude_paths: Optional[List[str]] = None) -> List[FileInfo]:
    """file infos"""
    file_info_list = []

    # default exclude
    # if exclude_paths is None:
    #     exclude_paths = [".git"]

    for _file_pattern in file_patterns:
        for file_name in pathlib.Path(target_path).glob("**/" + _file_pattern):
            file_info = get_file_info(str(file_name))
            if file_info is None:
                continue

            # filter skip files
            if exclude_paths is not None and len(exclude_paths) > 0:
                for exclude_path in exclude_paths:
                    if file_info.abpath_full.find(exclude_path) < 0:
                        file_info_list.append(file_info)
            else:
                file_info_list.append(file_info)

    return file_info_list


def file_move(src_path: str, dst_path: str) -> None:
    """file move"""
    try:
        shutil.copy(src_path, dst_path)
        return None
    except Exception:
        return None


def get_dir_list(target_path: str) -> List[str]:
    """get dir file lists"""
    dir_list = []

    if pathlib.Path(target_path).is_dir() is False:
        return []

    for _one_file in pathlib.Path(target_path).iterdir():
        if _one_file.is_dir():
            dir_list.append(str(_one_file))

    return dir_list


def get_file_md5_hash(target_path: str) -> str:
    """get file md5 hash string"""
    if is_file_exist(target_path) is False:
        return ""

    try:
        with open(target_path, "rb") as f_file:
            data = f_file.read()
            return str(hashlib.md5(data).hexdigest())
    except Exception:
        return ""
