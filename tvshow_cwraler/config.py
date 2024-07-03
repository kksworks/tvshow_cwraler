"""
default config for tvshow cwraler
"""

import json
import pathlib

CURRENT_DIR = pathlib.Path(__file__).resolve().parent

config_data = {}
# JSON 파일을 읽어와 파이썬 데이터로 로드
try:
    JSON_CONFIG_FILE = str(CURRENT_DIR.joinpath("..").joinpath("config.json"))
    with open(JSON_CONFIG_FILE, "r", encoding="utf-8") as file:
        config_data = json.load(file)
except Exception:
    pass

# 모든 문자열 기준은 소문자로 한다. (소문자로 강제변환후 진행)\

# 유효 파일 확장자 판별기준
VALID_MOVIE_FILE_EXT = ["avi", "mkv", "mp4"]
if "VALID_MOVIE_FILE_EXT" in config_data:
    VALID_MOVIE_FILE_EXT = config_data["VALID_MOVIE_FILE_EXT"]


# 유효 릴그룹
REL_GROUP = ["next", "buldu", "f1rst", "others", "nice", "wanna", "sniper", "webril", "webdl", "webrip"]
if "REL_GROUP" in config_data:
    REL_GROUP = config_data["REL_GROUP"]


# 제목에서 쓰레기 문자열 제거 할 것들 (파일명에 파일정보가 들어있는경우 삭제)
TRASH_FILE_NAME_WORD = [
    "mp4",
    "avi",
    "x.265",
    "x.264",
    "x265",
    "x264",
    "h264",
    "h265",
    "h.264",
    "h.265",
    "web",
    "dl",
    "aac",
    "dts",
    "tvn",
    "mbc",
    "sbs",
    "kbs2",
    "kbs1",
    "jtbc",
    "tv조선",
    "채널a",
]
if "TRASH_FILE_NAME_WORD" in config_data:
    TRASH_FILE_NAME_WORD = config_data["TRASH_FILE_NAME_WORD"]

# 제목에서 쓰레기 문자열 제거 할 것들 (tv show 의 특성상 각 종 특집은 삭제)
TRASH_FILE_NAME_WORD += [
    "첫방송",
    "추석특집",
    "설특집",
    "개국특집",
    "어린이날특집",
    "한글날특집",
    "금토드라마",
    "월화드라마",
    "수목드라마",
    "일일드라마",
    "일일연속극",
    "주말연속극",
    "주말드라마",
    "한국드라마",
    "미국드라마",
    "한국 드라마",
    "뉴스",
    "특선영화",
    "속보",
    "news",
    "NEWS",
]
if "TRASH_FILE_NAME_WORD" in config_data:
    TRASH_FILE_NAME_WORD = config_data["TRASH_FILE_NAME_WORD"]

# file rename suffix
FILE_RENAME_SUFFIX = "kksfixed"
if "FILE_RENAME_SUFFIX" in config_data:
    FILE_RENAME_SUFFIX = config_data["FILE_RENAME_SUFFIX"]

# logger setting

# target db
MODEL_TORRENT_SITE_PARSE_INFO = {
    "mongo_uri": "mongodb+srv://your_mongodb_info",
    "target_db": "tvShowCwraler",
    "target_document": "torrentSiteParseInfo",
}

if "MODEL_TORRENT_SITE_PARSE_INFO" in config_data:
    MODEL_TORRENT_SITE_PARSE_INFO = config_data["MODEL_TORRENT_SITE_PARSE_INFO"]


MODEL_TORRENT_ADDR = {
    "mongo_uri": "mongodb+srv://your_mongodb_info",
    "target_db": "tvShowCwraler",
    "target_document": "torrentMagnetAddr",
}
if "MODEL_TORRENT_ADDR" in config_data:
    MODEL_TORRENT_ADDR = config_data["MODEL_TORRENT_ADDR"]


MODEL_TORRENT_DOWN_MGR = {
    "mongo_uri": "mongodb+srv://your_mongodb_info",
    "target_db": "tvShowCwraler",
    "target_document": "torrentDownMgr",
}
if "MODEL_TORRENT_DOWN_MGR" in config_data:
    MODEL_TORRENT_DOWN_MGR = config_data["MODEL_TORRENT_DOWN_MGR"]


TRANSMISSON_CFG = {
    "id": "your_tm_id",
    "pass": "your_tm_pass",
    "server_ip": "your_tm_server",
    "server_port": 9091,
}
if "TRANSMISSON_CFG" in config_data:
    TRANSMISSON_CFG = config_data["TRANSMISSON_CFG"]
