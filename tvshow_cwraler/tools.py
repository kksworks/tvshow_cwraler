#!/usr/bin/python
"""file magnager apis"""

# system modules
import pathlib
import datetime
import re
import subprocess
from typing import List, Optional, Tuple
from dataclasses import dataclass

# user module
from kksworks_tools import file_tools
from kksworks_tools import str_tools

# this module
from tvshow_cwraler import log
from tvshow_cwraler import cwral
from tvshow_cwraler import config
from tvshow_cwraler.model import TorrentDownMgr


@dataclass
class TvShowFileInfo:
    """
    TvShowFileInfo data
    """

    title: Optional[str]
    original_input: Optional[str]
    rel_group: Optional[str]
    resol: Optional[str]
    file_ext: Optional[str]
    episode_num: Optional[List[int]]
    season_num: Optional[int]
    date: Optional[datetime.datetime]
    ab_file_path: Optional[str]


def _get_tvshow_episode_str(input_str: str) -> Tuple[str, int]:
    """문자열에서 에피소드데이터를 꺼낸다."""
    # pylint: disable=anomalous-backslash-in-string
    epi_str = ""

    # 형식은 다음과같다.
    #  - e000 + 특수문자들... (숫자길이는 1~5까지)
    #  - e1- / e01_ / E1123.
    #  - 구분자문자 : -, ., /, [, ], (, ) , 공백, \, _,
    # prefix : e, ep (대소문자포함)
    #   - 숫자 1~5자리
    episode_prefix_patterns = ["[eE]", "[eE][pP]"]
    episode_spilt_pattern = "[-.\ \\\/\[\]\(\)\<\>_]"

    for _episode_prefix_pattern in episode_prefix_patterns:
        find_pattern = f"{_episode_prefix_pattern}\\d{{1,5}}{episode_spilt_pattern}"
        texts = re.findall(find_pattern, input_str)
        if (texts is not None) and (len(texts) > 0):
            for text in texts:
                epi_str = text
            break

        find_pattern = f"{episode_spilt_pattern}{_episode_prefix_pattern}\\d{{1,5}}{episode_spilt_pattern}"
        texts = re.findall(find_pattern, input_str)
        if (texts is not None) and (len(texts) > 0):
            for text in texts:
                epi_str = text
            break

        find_pattern = f"{episode_spilt_pattern}{_episode_prefix_pattern}{episode_spilt_pattern}\\d{{1,5}}{episode_spilt_pattern}"
        texts = re.findall(find_pattern, input_str)
        if (texts is not None) and (len(texts) > 0):
            for text in texts:
                epi_str = text
            break

    # "e.xxx" 형식이 있으므로, . 을 삭제한다.
    _tmp_episode_str = epi_str.replace(".", "")
    epi_int = int(str_tools.get_number_string(_tmp_episode_str)[0])
    return epi_str, epi_int


def _get_tvshow_date_str(input_str: str) -> Tuple[str, datetime.datetime]:
    """tvshow date string"""
    # pylint: disable=anomalous-backslash-in-string

    # 유효한 문자열만 얻어온다.
    # 여기까지왔으면 특수문자는 없으며, 각 단어별 구분자는 ' ' 이다.

    # 시간데이터를 얻기위해 연속된 숫자만 필터링한다.
    # 단, 특수문제 제거로인해 스페이스가 끼어들어있을수있으니 스페이스를 감안하여 필터링한다.
    # 연속된 숫자 혹은 'yyyy mm dd' 형식으로 필터링
    find_patterns = ["(\d+)", "(\d+\ \d+\ \d+\ )"]

    for find_pattern in find_patterns:
        try:
            find_results = re.findall(find_pattern, input_str)
            for find_result in find_results:
                if len(find_result) == 6:
                    return find_result, datetime.datetime.strptime(find_result, "%y%m%d")
                elif len(find_result) == 8:
                    return find_result, datetime.datetime.strptime(find_result, "%Y%m%d")
        except Exception:
            continue
    return None, None


def _get_tvshow_season_str(input_str: str) -> Tuple[str, int]:
    """tvshow date string"""
    # pylint: disable=anomalous-backslash-in-string

    find_patterns = ["(s\d+)", "(시즌\d+)"]

    for find_pattern in find_patterns:
        try:
            season_str = re.findall(find_pattern, input_str)[0]
            season_int = int(str_tools.get_number_string(season_str)[0])
            return season_str, season_int
        except Exception:
            continue

    return None, None


def _get_tvshow_resol_str(input_str: str) -> Tuple[str, int]:
    """해상도 정보 획득"""
    # pylint: disable=anomalous-backslash-in-string

    # 연속된 숫자 + p 만 필터링한다.
    # 즉 2040p 1070p 이런식으로만..
    find_patterns = ["(\d+p)"]

    for find_pattern in find_patterns:
        try:
            resol_str = re.findall(find_pattern, input_str)[0]
            resol_int = int(str_tools.get_number_string(resol_str)[0])
            return resol_str, resol_int
        except Exception:
            continue

    return None, None


def _clear_words(target_str: str, clear_words: List[str]) -> str:
    for _word in clear_words:
        target_str = target_str.replace(_word, " ")
    return target_str


def get_tvshow_files(target_path: str) -> List[TvShowFileInfo]:
    """
    타겟 폴더에서 동영상정보들을 모두 획득한다.
    """
    tvshow_infos = []
    glob_patterns = [f"*.{_file_ext}" for _file_ext in config.VALID_MOVIE_FILE_EXT]

    file_lists = file_tools.get_fileinfo_from_folder(target_path, glob_patterns)

    for file_list in file_lists:
        tvshow_info = get_tvshow_info_from_string(file_list.file_full_name)
        tvshow_info.ab_file_path = file_list.abpath_full
        tvshow_infos.append(tvshow_info)

    return tvshow_infos


def gen_tvshow_full_name(tvshow_info: TvShowFileInfo) -> str:
    """gen tvshow file name"""

    try:
        # if tvshow_info.resol is None:
        #     tvshow_info.resol = "None"
        # if tvshow_info.rel_group is None:
        #     tvshow_info.rel_group = "None"
        # if tvshow_info.episode_num is None:
        #     tvshow_info.episode_num = 0

        tvshow_info.title = tvshow_info.title.rstrip()
        tvshow_info.title = tvshow_info.title.lstrip()

        tvshow_full_name = f"{tvshow_info.title}"

        # gen season
        if tvshow_info.season_num > 0:
            tvshow_full_name += f".s{tvshow_info.season_num:02d}"

        # gen episode
        for _epi_num in tvshow_info.episode_num:
            tvshow_full_name += f".e{_epi_num:03d}"

        if tvshow_info.date is not None:
            tvshow_full_name += f".{tvshow_info.date.strftime('%Y%m%d')}"

        if tvshow_info.resol is not None:
            tvshow_full_name += f".{tvshow_info.resol}"

        if tvshow_info.rel_group is not None:
            tvshow_full_name += f".{tvshow_info.rel_group}"

        return tvshow_full_name
    except Exception:
        return tvshow_info.original_input


def gen_tvshow_full_rename(tvshow_info: TvShowFileInfo, target_title: str) -> str:
    """gen tvshow file name"""

    try:
        # if tvshow_info.resol is None:
        #     tvshow_info.resol = "None"
        # if tvshow_info.rel_group is None:
        #     tvshow_info.rel_group = "None"
        # if tvshow_info.episode_num is None:
        #     tvshow_info.episode_num = 0

        tvshow_full_name = f"{target_title}"

        # gen season
        # 파일명에는 시즌정보를 넣을필요가 없을듯 (어차피 폴더로 분류할테니?)
        # if tvshow_info.season_num > 0:
        #     tvshow_full_name += f".s{tvshow_info.season_num:02d}"

        # gen episode
        for _epi_num in tvshow_info.episode_num:
            tvshow_full_name += f".e{_epi_num:03d}"

        if tvshow_info.date is not None:
            tvshow_full_name += f".{tvshow_info.date.strftime('%Y%m%d')}"

        if tvshow_info.resol is not None:
            tvshow_full_name += f".{tvshow_info.resol}"

        if tvshow_info.rel_group is not None:
            tvshow_full_name += f".{tvshow_info.rel_group}"

        suffix_str = f"-{config.FILE_RENAME_SUFFIX}-{str_tools.random_generator()}"
        tvshow_full_name += suffix_str

        if tvshow_info.ab_file_path is not None:
            file_ext = str(pathlib.PurePath(tvshow_info.ab_file_path).suffix)
            tvshow_full_name += f".{file_ext}"

        return tvshow_full_name
    except Exception:
        return tvshow_info.title + f".{file_ext}"


def file_exist_chk(torrent_mgr: TorrentDownMgr.Data) -> None:
    """
    기존 파일이 있는지 확인을한다.

    실제로 기존 매니징정보에서 해당 파일이 있다면 스킵을 하도록한다. 데이터를 내부적으로 업데이트 하게된다.
    """
    need_update_flag = True
    assert torrent_mgr.dn_target_dir is not None

    torrent_infos = get_tvshow_files(torrent_mgr.dn_target_dir)

    while need_update_flag:
        need_update_flag = False
        for torrent_info in torrent_infos:
            if torrent_mgr.dn_proc == "epi":
                assert torrent_mgr.epi_proc is not None
                assert torrent_mgr.epi_proc.target_epi is not None
                for _epi_num in torrent_info.episode_num:
                    if _epi_num == torrent_mgr.epi_proc.target_epi:
                        torrent_mgr.epi_proc.target_epi += 1
                        need_update_flag = True
            elif torrent_mgr.dn_proc == "date":
                assert torrent_mgr.date_proc is not None
                assert torrent_mgr.date_proc.target_date is not None
                assert torrent_mgr.date_proc.chk_interval is not None
                if torrent_info.date == torrent_mgr.date_proc.target_date:
                    torrent_mgr.date_proc.target_date += datetime.timedelta(torrent_mgr.date_proc.chk_interval)
                    need_update_flag = True


def get_tvshow_info_from_string(title_str: str) -> TvShowFileInfo:
    """get tvshow info"""

    tvshow_info = TvShowFileInfo(
        title=None,
        original_input=title_str,
        rel_group=None,
        resol=None,
        file_ext=None,
        episode_num=[],
        season_num=None,
        date=None,
        ab_file_path=None,
    )

    # 편의를 위해서 소문자로 모두 바꾼후 시작한다.
    title_str = title_str.lower()
    title_str = str_tools.replace_etc_char(title_str, " ")

    # 연속적인 스페이스를 제거한다.
    title_str = str_tools.replace_spaces_char(title_str, " ")

    # 1. 확장자 획득
    try:
        _tmp_tok = title_str.split(".")[-1]
        if _tmp_tok in config.VALID_MOVIE_FILE_EXT:
            tvshow_info.file_ext = _tmp_tok
        title_str = _clear_words(title_str, config.VALID_MOVIE_FILE_EXT)
    except Exception:
        tvshow_info.file_ext = None

    # 2. 릴그룹 획득
    try:
        for chk_str in config.REL_GROUP:
            if title_str.find(chk_str) >= 0:
                tvshow_info.rel_group = chk_str
                break
        title_str = _clear_words(title_str, config.REL_GROUP)
    except Exception:
        tvshow_info.rel_group = None

    # 3. 에피소드 획득
    try:
        while True:
            episode_str, episode_int = _get_tvshow_episode_str(title_str)
            tvshow_info.episode_num.append(episode_int)
            title_str = _clear_words(title_str, [episode_str])
    except Exception:
        pass

    if len(tvshow_info.episode_num) == 0:
        tvshow_info.episode_num = None
    else:
        tvshow_info.episode_num.sort()

    # 3. 시즌 획득
    try:
        season_str, season_int = _get_tvshow_season_str(title_str)
        tvshow_info.season_num = season_int
        title_str = _clear_words(title_str, [season_str])
    except Exception:
        tvshow_info.season_num = 0

    # 4. 날짜 획득 및 datetime 으로 변환
    try:
        date_str, tvshow_date = _get_tvshow_date_str(title_str)
        assert tvshow_date is not None
        tvshow_info.date = tvshow_date
        title_str = _clear_words(title_str, [date_str])
    except Exception:
        tvshow_info.date = None

    # 5. 해상도 획득
    try:
        resol_str, _resol_int = _get_tvshow_resol_str(title_str)
        tvshow_info.resol = resol_str
        title_str = _clear_words(title_str, [resol_str])
    except Exception:
        tvshow_info.resol = None

    # 쓰래기 문자제거
    # 쓸때없는 문자들 제거
    title_str = _clear_words(title_str, config.TRASH_FILE_NAME_WORD)
    title_str = str_tools.replace_etc_char(title_str, " ")
    title_str = str_tools.replace_spaces_char(title_str, " ")

    tvshow_info.title = title_str.strip()

    return tvshow_info


def run_transmission_dn_cli(magnet_addr: str, dn_path: str, use_tracker: bool = True) -> bool:
    """magnet add"""
    tm_id = config.TRANSMISSON_CFG["id"]
    tm_pass = config.TRANSMISSON_CFG["pass"]

    # test code :: magnet_addr = "magnet:?xt=urn:btih:d5736343341e57a2ad4b9a0513ba4a6a96d73b85"
    tm_remote_ip = config.TRANSMISSON_CFG["server_ip"]
    tm_remote_port = config.TRANSMISSON_CFG["server_port"]

    if magnet_addr.find("magnet:?xt=urn:btih:") < 0:
        magnet_addr = "magnet:?xt=urn:btih:" + magnet_addr

    # using tracker
    if use_tracker is True:
        tracker_list = cwral.torrent_get_magnet_tracker_list()
        for one_tracker in tracker_list:
            magnet_addr += f"&tr={one_tracker}"

    runcmd = f'transmission-remote {tm_remote_ip}:{tm_remote_port} --auth {tm_id}:{tm_pass} --add "{magnet_addr}" '
    if dn_path is not None:
        try:
            pathlib.Path(dn_path).mkdir(exist_ok=True, parents=True)
            runcmd += f' --download-dir "{dn_path}"'
        except Exception:
            runcmd = ""

    # log.log_tool.dbg(f'magnet add cmd : {runcmd}')
    with subprocess.Popen(runcmd, stdout=subprocess.PIPE, shell=True) as proc_res:
        try:
            assert proc_res is not None
            assert proc_res.stdout is not None
            process_ret = str(proc_res.stdout.read())
            log.log_tool.dbg(f"  -> magnet add cmd results : {process_ret}")

            if "success" in process_ret:
                return True
            else:
                return False
        except Exception:
            return False
