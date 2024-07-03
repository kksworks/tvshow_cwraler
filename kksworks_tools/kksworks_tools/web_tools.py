#!/usr/bin/env python3
"""web tools """
from typing import Optional, Literal, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import urllib3
import requests
from bs4 import BeautifulSoup


# disabled secure wran
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class WebReqRes:
    """web request results"""

    resp_code: Optional[int]
    bs4_obj: Optional[BeautifulSoup]
    html_contents: Optional[str]


DEFAULT_REQ_HEADER = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh;q=0.5,zh-CN;q=0.4,zh-TW;q=0.3",
}

DEFAULT_BS_PARSER = "lxml"  # html.parser or lxml


def chk_valid_url(url_str: str) -> bool:
    """url 형식이 정상적 형태인지 확인

    Args:
        url_str (str): target url

    Returns:
        bool: valid check results
    """

    try:
        result = urlparse(url_str)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_base_url(url_str: str) -> Tuple[str, str]:
    """base url 확인

    Args:
        url_str (str): full url string

    Returns:
        Optional[str]: base url 획득. 만약 invalid 형태라면 None 으로 리턴
    """
    try:
        url_parse = urlparse(url_str)
        assert url_parse.scheme is not None
        assert url_parse.hostname is not None
        return str(url_parse.scheme + "://" + url_parse.hostname), url_parse.hostname
    except Exception as _except_reason:
        return '', ''


def url_join(*args) -> str:
    """url join. 각 url 을 합친다.

    Returns:
        str: join 결과
    """
    path = ""
    for arg in args:
        path = urljoin(path, arg)
    return str(path)


def req_url(
    req_type: Literal["GET", "POST"],
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    decode_type: Literal["utf-8"] = "utf-8",
    data: Optional[dict] = None,
    session: Optional[requests.Session] = None,
    use_proxy: bool = False,
    timeout: int = 120,
    retry_cnt: int = 10,
) -> WebReqRes:
    """web request

    Args:
        req_type (Literal[GET, POST]): req type - GET or POST
        url (str): 파싱 url
        headers (Optional[dict], optional): 특별한 req header dict. 없을경우 default 사용
        params (Optional[dict], optional): pram 따로 전달
        decode_type (Literal["utf-8", optional): decoding type (default utf-8)
        data (Optional[dict], optional): data 따로전달. Defaults to None.
        session (Optional[requests.Session], optional): 세션 따로전달. 기존세션 유지용. Defaults to None.
        use_proxy (bool, optional): proxy 사용여부 (구현중). Defaults to False.
        timeout (int, optional): timeout sec. Defaults to 120.
        retry_cnt (int, optional): retry count. Defaults to 10.

    Raises:
        ValueError: _description_

    Returns:
        WebReqRes: ret req results
    """
    # get header...
    if headers is None:
        headers = DEFAULT_REQ_HEADER

    # get cookies from session
    cookies = None
    if session is not None:
        cookies = session.cookies.get_dict()

    # intt req res
    req_res = WebReqRes(resp_code=None, bs4_obj=None, html_contents=None)

    while retry_cnt > 0:
        proxy_info = None

        if use_proxy is True:
            # proxty function not implement yet
            proxy_info = None

        try:
            # request get..
            if req_type == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    proxies=proxy_info,
                    cookies=cookies,
                    verify=False,
                    timeout=timeout,
                )
            elif req_type == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    proxies=proxy_info,
                    cookies=cookies,
                    data=data,
                    verify=False,
                    timeout=timeout,
                )
            else:
                raise ValueError("not implementation")

            req_res.resp_code = response.status_code

            if response.status_code == 200:
                html_contents_text = response.content
                # return to contents :
                #  - decode_type : 'utf8' / 'cp1250'
                if decode_type is not None:
                    convert_str = html_contents_text.decode(decode_type)
                else:
                    convert_str = str(html_contents_text)

                req_res.html_contents = convert_str
                req_res.bs4_obj = BeautifulSoup(convert_str, DEFAULT_BS_PARSER)
                break
        except Exception:  # somtihg error
            # clear last values
            req_res.bs4_obj = None
            req_res.resp_code = None
            req_res.html_contents = None
        finally:
            retry_cnt -= 1

    return req_res
