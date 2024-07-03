#!/usr/bin/env python3
"""
torrent model
"""
# system modules
import datetime
import json
import pathlib
from typing import Optional, List
from dataclasses import dataclass
from bson.objectid import ObjectId

from tvshow_cwraler.log import log_tool

# ohter user module
from kksworks_tools import db_mongo
from kksworks_tools import mydata_tools


class TorrentDownMgr:
    """
    torrent download manager
    """

    # data define
    @dataclass
    class Data(mydata_tools.MyDataTools):
        """TorrentDownMgr data skel"""

        @dataclass
        class _EpiProcData(mydata_tools.MyDataTools):
            target_epi: Optional[int] = None

        @dataclass
        class _DateProcData(mydata_tools.MyDataTools):
            chk_interval: Optional[int] = None
            target_date: Optional[datetime.datetime] = None

        _id: Optional[ObjectId] = None
        is_run: Optional[bool] = None
        prog_name: Optional[str] = None
        search_keywords: Optional[List[str]] = None
        dn_proc: Optional[str] = None
        dn_target_dir: Optional[str] = None
        max_save_days: Optional[int] = None
        rel_info: Optional[str] = None
        rel_resol: Optional[str] = None
        epi_proc: Optional[_EpiProcData] = None
        date_proc: Optional[_DateProcData] = None

    class Query:
        """TorrentDownMgr data Query form db"""

        def __init__(self, db_ctx: db_mongo.DBMongoTools):
            self.db_ctx = db_ctx

        def _set_json_datas(self, datas: List["TorrentDownMgr.Data"]) -> int:
            return 0

        def get_active_datas(self) -> List["TorrentDownMgr.Data"]:
            """현재 활성화된 리스트만 획득"""
            db_query = {"is_run": True}
            return self.db_ctx.get_datas_model(find_query=db_query)

        def update_datas(self, datas: List["TorrentDownMgr.Data"]) -> int:
            """update data"""
            return self.db_ctx.upsert_datas(datas, "prog_name")

    # pylint: disable=too-few-public-methods
    query: Query

    def __init__(self, db_config: db_mongo.DBconfig):
        self._db_ctx = db_mongo.DBMongoTools(db_config, self.Data)
        self.query = self.Query(self._db_ctx)
        self.data = self.Data


class TorrentMagnetAddr:
    """
    torrent magnet address
    """

    @dataclass
    class Data(mydata_tools.MyDataTools):
        """TorrentMagnetAddr data skel"""

        pri_key: Optional[str]
        pub_date: Optional[datetime.datetime]
        title: Optional[str]

    class Query:
        """TorrentMagnetAddr data Query form db"""

        def __init__(self, db_ctx: db_mongo.DBMongoTools):
            self.db_ctx = db_ctx

        def get_torrent_dates(self, start_date: datetime.datetime, end_date: datetime.datetime):
            """날짜로 데이터 획득"""
            db_query = {"pub_date": {"$lt": end_date, "$gte": start_date}}
            return self.db_ctx.get_datas_model(find_query=db_query)

        def get_torrent_addrs(self, search_keywords: List[str], essential_keyword: str):
            """토렌트 타이틀로 검색"""
            db_search_querys = []
            for _search_keyword in search_keywords:
                _search_keyword = f'.*{_search_keyword.replace(" ", ".*")}.*'
                _search_db_query = {"title": {"$regex": _search_keyword}}
                db_search_querys.append(_search_db_query)
            # 스페이스 및 앞뒤로 ".*" 를 붙여서 모두 쿼리
            db_query = {"$and": [{"$or": db_search_querys}, {"title": {"$regex": essential_keyword, "$options": "i"}}]}
            log_tool.dbg(db_query)
            return self.db_ctx.get_datas_model(db_query)

        def update_datas(self, datas: List["TorrentMagnetAddr.Data"]) -> int:
            """update data"""
            return self.db_ctx.upsert_datas(datas, "pri_key")

    # pylint: disable=too-few-public-methods
    query: Query

    def __init__(self, db_config: db_mongo.DBconfig):
        self._db_ctx = db_mongo.DBMongoTools(db_config, self.Data)
        self.query = self.Query(self._db_ctx)
        self.data = self.Data


class TorrentSiteParseInfo:
    """
    site parse infos
    """

    @dataclass
    class Data(mydata_tools.MyDataTools):
        """TorrentSiteParseInfo data skel"""

        pri_key: Optional[str]
        chk_url: Optional[str]
        is_run: Optional[bool]
        site_name: Optional[List[str]]
        base_url: Optional[str]
        parse_url: Optional[List[str]]

    class Query:
        """TorrentSiteParseInfo data Query form db"""

        def __init__(self, db_ctx: db_mongo.DBMongoTools):
            self.db_ctx = db_ctx

        def get_active_datas(self) -> List["TorrentSiteParseInfo.Data"]:
            """get active data only"""
            db_query = {"is_run": True}
            return self.db_ctx.get_datas_model(find_query=db_query)

        def get_alldata(self) -> List["TorrentSiteParseInfo.Data"]:
            """get all datas"""
            return self.db_ctx.get_datas_model({})

        def update_datas(self, datas: List["TorrentSiteParseInfo.Data"]) -> int:
            """update data"""
            return self.db_ctx.upsert_datas(datas, "pri_key")

    # pylint: disable=too-few-public-methods
    query: Query

    def __init__(self, db_config: db_mongo.DBconfig):
        self._db_ctx = db_mongo.DBMongoTools(db_config, self.Data)
        self.query = self.Query(self._db_ctx)
        self.data = self.Data
