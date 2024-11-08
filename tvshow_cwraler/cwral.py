"""
torrnt bbs cwraler
"""

# system modules
import re
from typing import List, Optional
from bs4 import BeautifulSoup

# user module
from kksworks_tools import web_tools

# this module
from tvshow_cwraler import tools
from tvshow_cwraler import log
from tvshow_cwraler.model import TorrentMagnetAddr
from tvshow_cwraler.model import TorrentSiteParseInfo

## setting
CFG_MAGNET_HASH_LEN = 40
CFG_CHK_TITLE_MIN_LENGTH = 10
CFG_CWRAL_HISTORY_URL: List[str] = []


def _chk_valid_title(title_str: str) -> Optional[tools.TvShowFileInfo]:
    valid_title_str = ""

    try:
        # 문자열이 개행문자로 나눠져있는경우가 많다.
        # 각 개행문자들의 최소길이를 체크.
        for one_str in re.split("\r|\n", title_str):
            if len(one_str) > CFG_CHK_TITLE_MIN_LENGTH:
                valid_title_str = one_str
                break

        # 찾지못할경우 None 리턴
        if valid_title_str == "":
            return None

        # clear string...
        valid_title_str = valid_title_str.replace("\n", "")
        valid_title_str = valid_title_str.replace("\r", "")
        valid_title_str = valid_title_str.replace("\t", "")

        # get tv show string
        tvshow_info = tools.get_tvshow_info_from_string(valid_title_str)
        assert tvshow_info.episode_num is not None
        assert tvshow_info.resol is not None
        # 날짜 없는 tv show 들 도있다. (web 드라마. 디즈니, 넷플릭스)
        # assert tvshow_info.date is not None

        return tvshow_info
    except Exception:
        return None


def _parse_torrent_links(bs4_obj: BeautifulSoup, page_url: str) -> List[TorrentMagnetAddr.Data]:

    # get base url
    base_url_with_schme, base_url_host_name = web_tools.get_base_url(page_url)

    torrent_infos = []

    # 해당 웹페이지의 모든 링크를 획득
    for a_tag in bs4_obj.findAll("a"):
        try:
            # attr check
            try:
                target_url = str(a_tag.attrs["href"])
                link_text = str(a_tag.text)
            except Exception:
                continue

            # url 획득 (정상 url 획득)
            if web_tools.chk_valid_url(target_url) is False:
                target_url = web_tools.url_join(base_url_with_schme, target_url)

            # 정상적인 url 확인 (광고 skip)
            if web_tools.chk_valid_url(target_url) is False:
                # log.log_tool.warn(f"invalid url string case 1: {target_url}")
                continue

            # 간혹 https / http 가 다른경우도있다.
            if target_url.find(base_url_host_name) <= 0:
                # log.log_tool.warn(f"invalid url string case 2: {target_url} / {base_url_host_name}")
                continue

            # parse title
            tvshow_info = _chk_valid_title(link_text)
            if tvshow_info is None:
                # log.log_tool.warn(f"cannot parse title: {link_text}")
                continue

            # 해당 타겟 url 에서 마그넷 주소 파싱하기 magnet addr get
            magnet_hash_str = _get_margnet_hash_str(target_url, 0)
            if magnet_hash_str is None or len(magnet_hash_str) != CFG_MAGNET_HASH_LEN:
                # log.log_tool.warn(f"cannot pase hash str : {magnet_hash_str}")
                continue

            _torrent_title = tools.gen_tvshow_full_name(tvshow_info)
            _torrent_date = tvshow_info.date

            torrent_mganet_addr_data = TorrentMagnetAddr.Data(pri_key=magnet_hash_str, title=_torrent_title, pub_date=_torrent_date)

            log.log_tool.dbg("get magnet success..")
            log.log_tool.dbg(f"  - {tvshow_info.original_input}")
            log.log_tool.dbg(f"  - {torrent_mganet_addr_data.title}")
            log.log_tool.dbg(f"  - {torrent_mganet_addr_data.pri_key}")

            # log.log_tool.dbg(torrent_mganet_addr_data)
            torrent_infos.append(torrent_mganet_addr_data)
        except Exception:
            log.log_tool.exec_trace()
            continue
    return torrent_infos


# url 에서 마그넷 주소 추출
def _get_margnet_hash_str(target_url: Optional[str] = None, depth_cnt: int = 0) -> Optional[str]:
    # global CFG_CWRAL_HISTORY_URL
    assert target_url is not None

    # 한번 체크한것들은 다시 체크하지 않는다.
    if target_url in CFG_CWRAL_HISTORY_URL:
        return None

    # iframe 에 대한 재귀 함수호출은 3depth 까지만 한다.
    if depth_cnt > 3:
        log.log_tool.err("max iframe depth... skip..")
        return None

    # cwral skip 저장용
    CFG_CWRAL_HISTORY_URL.append(target_url)
    # log.log_tool.dbg(f" get magnet from url (iframe : {depth_cnt}): {target_url}")

    try:
        resp_val = web_tools.req_url("GET", url=target_url, timeout=10)
        bs4_obj = resp_val.bs4_obj
    except Exception:
        log.log_tool.err("url parse fail.. (req error) : " + target_url)
        return None

    # input attr contents magnet
    assert bs4_obj is not None

    # magnet 주소 파싱 : input 에 있는경우..
    get_values = bs4_obj.find_all("input")
    for get_value in get_values:
        magnet_link = str(get_value.get("value"))
        if magnet_link.find("magnet") >= 0:
            return magnet_link.replace("magnet:?xt=urn:", "").replace("btih:", "")

    # magnet 주소 파싱 : 버튼에 있는경우..
    get_values = bs4_obj.find_all("button")
    for get_value in get_values:
        magnet_link = str(get_value.get("onclick"))
        if magnet_link.find("magnet_link(") >= 0:
            return magnet_link[13:-3]

    # magnet 주소 파싱 : 단순 노멀링크로 있는경우..
    get_links = bs4_obj.find_all("a")
    for get_link in get_links:
        # case 0 : normal link
        magnet_link = str(get_link.get("href"))
        if (magnet_link.find("magnet") >= 0) and (magnet_link.find("magnet:?xt=urn:") >= 0):
            return magnet_link.replace("magnet:?xt=urn:", "").replace("btih:", "")

        # case 1 : other link
        link_text = str(get_link)
        if link_text.find("magnet:?xt=urn:btih:") >= 0:
            start_idx = link_text.find("magnet:?xt=urn:btih:")
            magnet_link = link_text[start_idx : 60 + start_idx]
            return magnet_link.replace("magnet:?xt=urn:", "").replace("btih:", "")

        # case 3 : magnet other link..
        link_text = str(get_link.text).lower()
        if link_text.find("magnet") >= 0:
            sub_page_link = str(get_link.get("href"))
            assert sub_page_link is not None
            return _get_margnet_hash_str(sub_page_link, depth_cnt + 1)

    # magnet 주소 파싱 : iframe 으로 다른 페이지 링크
    ifrmame_tags = bs4_obj.find_all("iframe")
    for ifrmame_tag in ifrmame_tags:
        log.log_tool.dbg("iframe enter....")
        ifrmame_src = str(ifrmame_tag.get("src"))
        return _get_margnet_hash_str(ifrmame_src, depth_cnt + 1)

    log.log_tool.err("url parse fail.. (not found magnet addr) : " + target_url)
    return None


def get_bbs_contents(target_url: str) -> List[TorrentMagnetAddr.Data]:
    """bbs content cwraling"""

    try:
        log.log_tool.dbg(f"parse start :: {target_url}")
        resp_val = web_tools.req_url("GET", target_url, decode_type="utf-8")
        assert resp_val.resp_code == 200
        assert resp_val.bs4_obj is not None

        return _parse_torrent_links(resp_val.bs4_obj, target_url)
    except Exception:
        log.log_tool.exec_trace()
        return []


def chk_torrent_site_info(site_str: str, max_chk_cnt: int) -> str:
    for _idx in range(1, max_chk_cnt):
        req_resp = web_tools.req_url("GET", site_str)
        if req_resp.resp_code == 200:
            return site_str

        # Define the pattern to match the numbers in the URL
        pattern = re.compile(r"(\d+)")

        # Find the current number in the URL
        match = pattern.search(site_str)
        if not match:
            print("No number found in the URL.")
            return ""

        # Extract the number as an integer
        current_number = int(match.group(0))

        site_str = pattern.sub(str(current_number + _idx), site_str)

    return ""


def cwral_torrent_site_info(
    site_parser_datas: List[TorrentSiteParseInfo.Data],
) -> int:
    """torrent url 을 만든다"""
    update_cnt = 0

    for site_parser_data in site_parser_datas:
        try:
            assert site_parser_data.chk_url is not None
            assert site_parser_data.is_run is True
            assert site_parser_data.site_name is not None

            # 1. get base site parse cwral
            req_resp = web_tools.req_url("GET", site_parser_data.chk_url)

            # 2. check result
            assert req_resp.resp_code == 200
            assert req_resp.bs4_obj is not None

            # 모든 텍스트를 다 갖고온다.
            # 텍스트의 내용이 곧 url 의 내용이라고 판단
            all_texts = req_resp.bs4_obj.find_all(text=True, recursive=True)
            for one_text in all_texts:
                one_text = re.sub(r"\s+", "", str(one_text))
                for site_name in site_parser_data.site_name:
                    if one_text.find(site_name) >= 0 and one_text.find("http") >= 0:
                        site_parser_data.base_url = chk_torrent_site_info(one_text, 10)
                        if site_parser_data.base_url == "":
                            site_parser_data.is_run = False
                        log.log_tool.info(site_parser_data)
                        update_cnt += 1
        except Exception:
            log.log_tool.err(f"cwral site fail : {site_parser_data}")
            continue

    log.log_tool.dbg(f"update count {update_cnt}")
    return update_cnt


TMP_MAGNET_TRACKER_LIST: List[str] = []


def torrent_get_magnet_tracker_list() -> List[str]:
    """get torrent tracker list"""

    # using last data (cached)
    global TMP_MAGNET_TRACKER_LIST
    if len(TMP_MAGNET_TRACKER_LIST) > 0:
        return TMP_MAGNET_TRACKER_LIST

    try:
        target_url = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt"
        web_res = web_tools.req_url("GET", target_url, decode_type="utf-8")
        tracker_lists = web_res.html_contents

        assert tracker_lists is not None
        for one_tracker in tracker_lists.split("\n"):
            try:
                if one_tracker.find("udp://") >= 0 or one_tracker.find("http://") >= 0 or one_tracker.find("https://") >= 0:
                    one_tracker = one_tracker.replace("\r", "")
                    one_tracker = one_tracker.replace("\n", "")
                    TMP_MAGNET_TRACKER_LIST.append(one_tracker)
            except Exception:
                continue

        return TMP_MAGNET_TRACKER_LIST
    except Exception:
        return TMP_MAGNET_TRACKER_LIST
