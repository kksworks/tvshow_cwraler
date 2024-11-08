#!/usr/bin/python
"""tvshow cwalewr module"""
# system module
import pathlib
import shutil
import os
import glob
import datetime
from urllib.parse import urlparse, urljoin

# user module
from kksworks_tools import file_tools
from kksworks_tools import db_mongo

# this module
from tvshow_cwraler import config
from tvshow_cwraler import cwral
from tvshow_cwraler import tools
from tvshow_cwraler import log

from tvshow_cwraler.model import TorrentSiteParseInfo
from tvshow_cwraler.model import TorrentMagnetAddr
from tvshow_cwraler.model import TorrentDownMgr


def rename_tvshow_files(target_path: str, target_title: str) -> None:
    """폴더를 검사하여, 이름에 맞게, tvshow의 파일이름을 업데이트한다.

    - 해당 폴더는 depth 가 1 으로 가정한다. depth 가 1만 검사
    Args:
        target_path (str): 검사할 최상위 폴더
    """
    tvshow_infos = tools.get_tvshow_files(target_path)
    for tvshow_info in tvshow_infos:
        try:
            assert tvshow_info.title is not None
            assert tvshow_info.ab_file_path is not None

            if tvshow_info.title.find(config.FILE_RENAME_SUFFIX) >= 0:
                # log.log_tool.dbg(f"{tvshow_info['ab_file_path']} is already fixed")
                continue
            # tvshow_info.title = tvshow_info.title.split("kksfixed")[0]

            target_file_name = tools.gen_tvshow_full_rename(tvshow_info, target_title)

            target_folder = str(pathlib.PurePath(tvshow_info.ab_file_path).parent)
            log.log_tool.dbg(f"file fix : {tvshow_info.ab_file_path} -> {target_file_name}")
            shutil.move(
                tvshow_info.ab_file_path,
                file_tools.join_path(target_folder, target_file_name),
            )
        except Exception:
            log.log_tool.exec_trace()
            continue


def remove_sub_folder(target_path: str, _chk_sub_folder: bool = False) -> None:
    """쓸때없는 서브폴더쪽 파일들 삭제. 영상파일만 타겟 폴더로 옮긴다.

    - 최상위 폴더는 detpth 가 1이 라고 가정한다. 하위 모든폴더는 영상파일만 target path 로 옮긴다.

    Args:
        target_path (str): 검사할 최상위 폴더
        _chk_sub_folder (bool, optional): 내부 변수 (수정불가). Defaults to False.
    """
    full_file_path = ""
    for file_info in os.listdir(target_path):
        full_file_path = os.path.join(str(target_path), str(file_info))
        if os.path.isdir(full_file_path):
            remove_sub_folder(full_file_path, True)

    # move folder
    if _chk_sub_folder:
        glob_patterns = [f"*.{_file_ext}" for _file_ext in config.VALID_MOVIE_FILE_EXT]
        for _glob_pattern in glob_patterns:
            for file_name in glob.glob(str(target_path) + "/" + _glob_pattern):
                try:
                    log.log_tool.dbg(f"move file : {file_name} to ../")
                    shutil.move(file_name, os.path.join(target_path, "../"))
                except Exception:
                    pass

        log.log_tool.dbg(f"remove folder : {target_path}")
        shutil.rmtree(target_path, ignore_errors=True)


def clear_old_tvshow_files(target_path: str, last_days: int) -> None:
    """타겟폴더에서 오래된 파일을 삭제한다.

    - depth 는 1이라고 가정한다.

    Args:
        target_path (str): 타겟 폴더
        last_days (int): day 가 지난 파일에 대해서 삭제
    """
    tvshow_infos = tools.get_tvshow_files(target_path)
    del_target_date = datetime.datetime.today() - datetime.timedelta(days=last_days)

    for tvshow_info in tvshow_infos:
        try:
            assert tvshow_info.date is not None
            assert tvshow_info.ab_file_path is not None
            if tvshow_info.date < del_target_date:
                log.log_tool.dbg(f"remove file : {tvshow_info.ab_file_path}")
                os.remove(tvshow_info.ab_file_path)
        except Exception:
            log.log_tool.exec_trace()
            continue


def cwral_torrent_site_infos():
    """site info 를 업데이트한다.

    - 쿼리 모델 : TorrentSiteParseInfo
    """

    db_config = db_mongo.DBconfig(
        config.MODEL_TORRENT_SITE_PARSE_INFO["target_db"],
        config.MODEL_TORRENT_SITE_PARSE_INFO["target_document"],
        config.MODEL_TORRENT_SITE_PARSE_INFO["mongo_uri"],
    )
    site_info_model = TorrentSiteParseInfo(db_config)
    query_data = site_info_model.query.get_active_datas()

    # update query datas
    if cwral.cwral_torrent_site_info(query_data) > 0:
        site_info_model.query.update_datas(query_data)
    else:
        log.log_tool.dbg("no query datas")

    # update datas


def cwral_tvshow(start_page: int, max_page: int, force_cwral: bool):
    """토렌트 사이트에서 tv show 관련 마그넷을 모두 크롤링

    Args:
        max_page (int): 사이트에서 페이지를 몇개를 크롤링할것인가
    """
    db_cfg_stie_parse = db_mongo.DBconfig(
        config.MODEL_TORRENT_SITE_PARSE_INFO["target_db"],
        config.MODEL_TORRENT_SITE_PARSE_INFO["target_document"],
        config.MODEL_TORRENT_SITE_PARSE_INFO["mongo_uri"],
    )

    db_cfg_magnet_addr = db_mongo.DBconfig(
        config.MODEL_TORRENT_ADDR["target_db"],
        config.MODEL_TORRENT_ADDR["target_document"],
        config.MODEL_TORRENT_ADDR["mongo_uri"],
    )

    # 현재 활성화 된 사이트 정보만 획득
    site_lists = TorrentSiteParseInfo(db_cfg_stie_parse).query.get_active_datas()

    for site_info in site_lists:
        # 사이트 정보 확인
        if site_info.base_url is None or len(site_info.base_url) == 0:
            continue

        for parse_url in site_info.parse_url:
            for _page in range(start_page, max_page + 1):
                # site parse url 형식은 string format 을 따른다.
                target_url = urljoin(site_info.base_url, parse_url) % _page

                # 토렌트 마그넷 정보를 크롤링한다.
                cwral_datas = cwral.get_bbs_contents(target_url)

                # 1개도 없다면 잘못된 사이트정보. 크롤링 멈춤
                if len(cwral_datas) <= 0:
                    log.log_tool.warn(f"no magnet dawta : no parse pages -> {site_info.base_url}")
                    break

                # 업데이트할 마그넷 정보가 없다면, 이미 크롤링 완료한 페이지이므로 크롤링 멈춤
                update_cnt = TorrentMagnetAddr(db_cfg_magnet_addr).query.update_datas(cwral_datas)

                if force_cwral is not True and update_cnt <= 0:
                    log.log_tool.warn(f"no update data : stop cwraling -> {site_info.base_url}")
                    break

                log.log_tool.dbg(f"[cli] cwral_tvshow --> update count : {update_cnt}")


def torrent_chk_files(remove_old_files: bool = True, remove_sub_folder_files: bool = True, rename_file_names: bool = True):
    db_cfg_dn_mgr = db_mongo.DBconfig(
        config.MODEL_TORRENT_DOWN_MGR["target_db"],
        config.MODEL_TORRENT_DOWN_MGR["target_document"],
        config.MODEL_TORRENT_DOWN_MGR["mongo_uri"],
    )

    is_need_to_update = False
    dn_mgr_datas = TorrentDownMgr(db_cfg_dn_mgr).query.get_active_datas()
    for dn_mgr_data in dn_mgr_datas:
        try:
            assert dn_mgr_data.prog_name is not None

            # 1. 먼저 폴더를 정리한다.
            if remove_sub_folder_files is True:
                remove_sub_folder(dn_mgr_data.dn_target_dir)

            # 2. 오래된 파일들을 정리한다.
            if remove_old_files is True and dn_mgr_data.max_save_days > 0:
                clear_old_tvshow_files(dn_mgr_data.dn_target_dir, dn_mgr_data.max_save_days)

            # 3. rename 한다.
            if rename_file_names is True:
                rename_tvshow_files(dn_mgr_data.dn_target_dir, dn_mgr_data.prog_name)

            # 3. 기존 폴더파일들을 확인한다.
            torrent_infos = tools.get_tvshow_files(dn_mgr_data.dn_target_dir)
            epi_infos = [torrent_info.episode_num for torrent_info in torrent_infos]
            date_infos = [torrent_info.date for torrent_info in torrent_infos]

            if dn_mgr_data.dn_proc == "epi":
                assert dn_mgr_data.epi_proc is not None
                assert dn_mgr_data.epi_proc.target_epi is not None
                # epi check and skip next target
                while dn_mgr_data.epi_proc.target_epi in epi_infos:
                    dn_mgr_data.epi_proc.target_epi += 1
                    is_need_to_update = True

            elif dn_mgr_data.dn_proc == "date":
                assert dn_mgr_data.date_proc is not None
                assert dn_mgr_data.date_proc.target_date is not None
                assert dn_mgr_data.date_proc.chk_interval is not None
                # date check and skip next target
                while dn_mgr_data.date_proc.target_date in date_infos:
                    dn_mgr_data.date_proc.target_date += datetime.timedelta(dn_mgr_data.date_proc.chk_interval)
                    is_need_to_update = True
        except Exception:
            continue

    # update datas
    if is_need_to_update:
        TorrentDownMgr(db_cfg_dn_mgr).query.update_datas(dn_mgr_datas)


def tvshow_torrent_dn() -> int:
    """torrent 다운로드를 한다.

    - 각 db 에서 정보를 갖고와서 마그넷추가

    Returns:
        int: 마그넷 추가한 데이터 갯수
    """
    # 먼저 파일시스템에서 기존 파일들이 있는지 확인한다.
    torrent_chk_files()

    dn_cnt = 0

    db_cfg_dn_mgr = db_mongo.DBconfig(
        config.MODEL_TORRENT_DOWN_MGR["target_db"],
        config.MODEL_TORRENT_DOWN_MGR["target_document"],
        config.MODEL_TORRENT_DOWN_MGR["mongo_uri"],
    )

    db_cfg_magnet_addr = db_mongo.DBconfig(
        config.MODEL_TORRENT_ADDR["target_db"],
        config.MODEL_TORRENT_ADDR["target_document"],
        config.MODEL_TORRENT_ADDR["mongo_uri"],
    )

    dn_mgr_datas = TorrentDownMgr(db_cfg_dn_mgr).query.get_active_datas()

    for dn_mgr_data in dn_mgr_datas:
        try:
            assert dn_mgr_data.prog_name is not None
            assert dn_mgr_data.search_keywords is not None
            assert len(dn_mgr_data.search_keywords) > 0
            log.log_tool.dbg(f"torrent_dn try dn : {dn_mgr_data.prog_name}")
            log.log_tool.dbg(f" -> search_keywords : {dn_mgr_data.search_keywords}")

            # gen base search query
            search_keywords = dn_mgr_data.search_keywords
            essential_keyword = ""
            # search_query = ".*" + dn_mgr_data.prog_name.replace(" ", ".") + ".*"

            # gen search query
            if dn_mgr_data.dn_proc == "epi":
                assert dn_mgr_data.epi_proc is not None
                assert dn_mgr_data.epi_proc.target_epi is not None
                essential_keyword = f"e{dn_mgr_data.epi_proc.target_epi:03d}"
            elif dn_mgr_data.dn_proc == "date":
                assert dn_mgr_data.date_proc is not None
                assert dn_mgr_data.date_proc.target_date is not None
                essential_keyword = f"{dn_mgr_data.date_proc.target_date.strftime('%y%m%d')}"

            # query to db
            for query_data in TorrentMagnetAddr(db_cfg_magnet_addr).query.get_torrent_addrs(search_keywords, essential_keyword):
                tvshow_info = tools.get_tvshow_info_from_string(query_data.title)
                # check file infos

                # resol check
                is_chk_resol = False
                if dn_mgr_data.rel_resol == "*":
                    is_chk_resol = True
                elif tvshow_info.resol == dn_mgr_data.rel_resol:
                    is_chk_resol = True
                else:
                    is_chk_resol = False

                # rel group check
                is_chk_rel = False
                if dn_mgr_data.rel_info == "*":
                    is_chk_rel = True
                elif tvshow_info.rel_group == dn_mgr_data.rel_info:
                    is_chk_rel = True
                else:
                    is_chk_rel = False

                if is_chk_rel is not True or is_chk_resol is not True:
                    log.log_tool.warn(f"skip target video infos ... chk_rel {is_chk_rel} / chk_resol {is_chk_resol}")
                    continue

                # log.log_tool.err(str(tvshow_info))

                ############# epi proc
                if dn_mgr_data.dn_proc == "epi":
                    for _epi_num in tvshow_info.episode_num:
                        if _epi_num == dn_mgr_data.epi_proc.target_epi:
                            cli_res = tools.run_transmission_dn_cli(query_data.pri_key, dn_mgr_data.dn_target_dir)
                            if cli_res:
                                log.log_tool.dbg(f"transmission cli add success : {dn_mgr_data.prog_name} - epi : {dn_mgr_data.epi_proc.target_epi}")
                                dn_mgr_data.epi_proc.target_epi += 1
                                dn_cnt += 1
                            else:
                                log.log_tool.err(f"transmission cli add error : {dn_mgr_data.prog_name} - epi : {dn_mgr_data.epi_proc.target_epi}")
                ############# date proc
                elif dn_mgr_data.dn_proc == "date":
                    if tvshow_info.date == dn_mgr_data.date_proc.target_date:
                        cli_res = tools.run_transmission_dn_cli(query_data.pri_key, dn_mgr_data.dn_target_dir)
                        if cli_res:
                            log.log_tool.dbg(f"transmission cli add success :  {dn_mgr_data.prog_name} - date : {dn_mgr_data.date_proc.target_date}")
                            dn_mgr_data.date_proc.target_date += datetime.timedelta(dn_mgr_data.date_proc.chk_interval)
                            dn_cnt += 1
                        else:
                            log.log_tool.err("transmission cli add error : {dn_mgr_data.prog_name} - date : {dn_mgr_data.date_proc.target_date}")

        except Exception:
            continue

    log.log_tool.dbg(f"transmission dn count {dn_cnt} ")
    if dn_cnt > 0:
        TorrentDownMgr(db_cfg_dn_mgr).query.update_datas(dn_mgr_datas)

    return dn_cnt


if __name__ == "__main__":
    print("main")
