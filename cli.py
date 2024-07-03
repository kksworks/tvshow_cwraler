#!/usr/bin/python

"""
tvshow cwlarer cli interface
"""

import sys
import pathlib
import click

from kksworks_tools.kksworks_tools.log_tools import LogTools

# set paths (for cli)
WORKING_PATH = str(pathlib.Path(__file__).resolve().parent)
sys.path.append(WORKING_PATH)

log_tool = LogTools("tvshow_cralwer", log_level="DEBUG")

from tvshow_cwraler import api


@click.group()
def tvshow():
    """click group"""


@tvshow.command(name="tvshow-dn")
def tvshow_cli_tvshow_dn():
    """tvshow download (query from db)"""

    log_tool.dbg("[cli] tvshow_dn ++")
    try:

        # 1. 기존 폴더 정리
        api.torrent_chk_files()
        # 2. 토렌트 파일 다운로드
        while True:
            # 여러개 다운로드 반복실행
            dn_cnt = api.tvshow_torrent_dn()
            if dn_cnt <= 0:
                break

    except Exception:
        log_tool.exec_trace()

    log_tool.dbg("[cli] tvshow_dn ++")


@tvshow.command(name="cwral-site-infos")
def tvshow_cli__cwral_site_infos():
    """site info cwral form web"""

    log_tool.dbg("[cli] cwral_site_infos ++")
    try:
        api.cwral_torrent_site_infos()
    except Exception:
        log_tool.exec_trace()

    log_tool.dbg("[cli] cwral_site_infos --")


@tvshow.command(name="cwral-tvshow")
@click.argument("start_page", type=int)
@click.argument("max_page", type=int)
def tvshow_cli__cwral_tvshow(start_page: int, max_page: int):
    """cwral tvshow magnet address (web cwral)"""

    log_tool.dbg("[cli] cwral_tvshow ++")
    try:
        api.cwral_tvshow(start_page, max_page, False)
    except Exception:
        log_tool.exec_trace()

    log_tool.dbg("[cli] cwral_tvshow --")


@tvshow.command(name="cwral-tvshow-force")
@click.argument("start_page", type=int)
@click.argument("max_page", type=int)
def tvshow_cli__cwral_tvshow_force(start_page: int, max_page: int):
    """cwral tvshow magnet address (web cwral)"""

    log_tool.dbg("[cli] cwral_tvshow force ++")
    try:
        api.cwral_tvshow(start_page, max_page, True)
    except Exception:
        log_tool.exec_trace()

    log_tool.dbg("[cli] cwral_tvshow force --")


@tvshow.command(name="chk-files")
def tvshow_cli__chk_files():
    """chk files (torent folders)"""

    log_tool.dbg("[cli] chk_files ++")
    try:
        api.torrent_chk_files()
    except Exception:
        log_tool.exec_trace()
    log_tool.dbg("[cli] chk_files --")


if __name__ == "__main__":
    tvshow()
