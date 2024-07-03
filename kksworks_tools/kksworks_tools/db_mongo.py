"""
data adaptor for mongodb
"""

from dataclasses import dataclass
from typing import Optional, List, Union, Any
from pymongo import MongoClient, UpdateOne


from .mydata_tools import MyDataTools
from .log_tools import log_api


@dataclass
class DBconfig:
    """db config info"""

    target_db: str
    target_document: str
    mongo_svr_cfg_uri: str


class DBMongoTools:
    """
    monbo db wrapper tools
    """

    def __init__(self, mongodb_config: DBconfig, my_model: MyDataTools):
        self.mongodb_config = mongodb_config
        self.my_model = my_model

    def _get_mongo_clnt(self):
        return MongoClient(self.mongodb_config.mongo_svr_cfg_uri)[self.mongodb_config.target_db][self.mongodb_config.target_document]

    def get_config(self) -> DBconfig:
        """get config"""
        return self.mongodb_config

    def upsert_datas(self, datas: Any, pri_key: str) -> int:
        """
        userert : 있으면 업데이트, 없으면 insert 한다.

        - datas 는 dict 혹은 기존 MyDataTools 을 이용한다.
        - upsert 특성상 priv key 가 필수이다

        Args:
            datas (Union[List[dict], List[MyDataTools]]): datas
            pri_key (str): upsert priv key

        Returns:
            int: query 성공 count
        """
        need_to_update_cnt = 0
        update_cnt = 0
        try:
            mongodb_clnt = self._get_mongo_clnt()
            updates_query = []

            # gen query
            for _data in datas:
                # 1. MyDataTools need to convert dict
                if isinstance(_data, MyDataTools):
                    _data = _data.to_dict()

                # 2. instance check
                assert isinstance(_data, dict)

                # 3. priv key check
                assert isinstance(pri_key, str)
                assert pri_key in _data.keys()

                # 4. upset query gen
                target_key = {pri_key: _data[pri_key]}
                target_data = {"$set": _data}
                updates_query.append(UpdateOne(target_key, target_data, upsert=True))

                need_to_update_cnt += 1

            # check query count
            if need_to_update_cnt <= 0:
                return 0

            # query run
            result = mongodb_clnt.bulk_write(updates_query)
            update_cnt = result.inserted_count + result.modified_count + result.upserted_count
        except Exception:
            log_api.exec_trace()
            raise
        finally:
            pass

        return update_cnt

    def insert_datas(self, datas: List[Union[dict, MyDataTools]], _pri_key: Optional[str] = None) -> int:
        """데이터를 입력한다. 여러 데이터를 위해서 list dict 형태로 인자받는다.

        - mongo db는 pri_key는 실제 사용하지 않는다. (다른 db 와의 호환성을 위해서 priv key 남겨둔다.)

        Args:
            datas (List[Union[dict, MyDataTools]]): insert datas
            _pri_key (Optional[str], optional): pri_key 미사용. Defaults to None.

        Returns:
            int: query 성공 count
        """

        # mongo db do not using pri_key in inert query
        _pri_key = None

        need_to_update_cnt = 0
        update_cnt = 0
        try:
            mongodb_clnt = self._get_mongo_clnt()
            updates_query = []

            for _data in datas:
                # 1. MyDataTools need to convert dict
                if isinstance(_data, MyDataTools):
                    _data = _data.to_dict()

                # 2. instance check
                assert isinstance(_data, dict)

                # 3. gen query
                updates_query.append(_data)
                need_to_update_cnt += 1

            # check query count
            if need_to_update_cnt <= 0:
                update_cnt = 0
                assert True, "no query datas"

            result = mongodb_clnt.insert_many(updates_query)
            update_cnt = len(result.inserted_ids)

        except Exception:
            log_api.exec_trace()
            raise
        finally:
            pass

        return update_cnt

    def get_datas_dict(
        self,
        find_query: Optional[dict] = None,
        sort_query: Optional[dict] = None,
        limit_count: Optional[int] = None,
    ) -> List[dict]:
        """
        mongodb의 실제 쿼리를 한다. dict list 로 반환.
        """

        try:
            mongodb_clnt = self._get_mongo_clnt()
            # find query
            db_cursor = mongodb_clnt.find(find_query)

            # sort query
            if sort_query is not None:
                for item, value in sort_query.items():
                    db_cursor = db_cursor.sort(item, value)
            if limit_count is not None:
                db_cursor = db_cursor.limit(limit_count)

            dict_datas = list(db_cursor)
            return dict_datas

        except Exception:
            log_api.exec_trace()
            return []

    def get_datas_model(
        self,
        find_query: Optional[dict] = None,
        sort_query: Optional[dict] = None,
        limit_count: Optional[int] = None,
    ) -> List[MyDataTools]:
        """
        mongodb의 실제 쿼리를 한다. model list 로 반환.
        """
        model_datas = []
        for _data in self.get_datas_dict(find_query, sort_query, limit_count):
            _conv_model = self.my_model.from_dict(_data)
            if _conv_model is not None:
                model_datas.append(_conv_model)
        return model_datas

    def rename_doc_field(self, rename_src: str, rename_target: str):
        """
        document 의 특정 필드의 이름을 전체 변경
        """
        mongo_clnt = self._get_mongo_clnt()
        mongo_clnt.update_many({}, {"$rename": {rename_src: rename_target}})

    def del_doc_field(self, field_name):
        """
        document 의 특정 필드를 전체 삭제
        """
        mongo_clnt = self._get_mongo_clnt()
        mongo_clnt.update_many({}, {"$unset": {field_name: ""}})

    def del_documents(self, del_query: dict):
        """
        해당 document 삭제
        """
        mongo_clnt = self._get_mongo_clnt()
        mongo_clnt.delete_one(del_query)
