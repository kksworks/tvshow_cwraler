tvshow cwraler cli ..

## 주의사항

본 프로그램을 제대로 사용하기 위해서는 각종 설정이 필요합니다.

불법적인? 사용을 할 가능성? 으로.. 관련 설정들은 따로 배포하지 않습니다. (배포 요청도 받지 않습니다.)

## 본 프로그램소개

- python 기반의 cli 프로그램입니다.
  - 모든 동작은 cli 기반으로 동작. (ui 없음 추후 web 기반으로 지원예정.. 스터디중..)
- 토렌트 사이트에서 마그넷주소를 크롤링하여 db 화합니다.
- 크롤링한 db 에서 한국 tv show 를 다운로드합니다. (transmission-deamon 이용)
- tvshow 관리
  - 에피소드 형식 다운로드, 날짜기반다온르도 지원
  - 최대 저장날짜 확인
  - 파일이름 자동수정 : 각 tvshow 파일마다 각각의 이름형식이 다른경우 일관성유지

## how to install (using native env)

ubuntu 20.04 기준으로 작성, docker 를 이용할 경우 다른 가이드를 참고합니다.

### pre-requirement

- mongo db server
  - 각 필요데이터들은 mongdb 쿼리 기준으로 작성
  - pymongo 를 이용하며, db uri 를 사용하므로 외부 서버로 동작시켜도 됨
  - 다른 google 의 guide 를 참고하여 mongodb setting 합니다.
- transmission deamon / cli
  - 토렌트 다운로드를 위한 토렌트 클라이언트
  - `transmission cli` 를 이용하기 때문에 외부 서버형태로 동작 가능
  - local install : `apt-get install transmission-cli transmission-deamon`
- tool install
  - `apt-get install -y python3 python3-pip git`

### repo clone

먼저 본 repo 를 clone 합니다.

```
git clone git@github.com:kksworks/tvshow_cwraler.git
```

본 프로젝트는 <https://github.com/kksworks/kksworks_tools> 를 이용합니다. `kksworks_tools` 는 submodule 형태로 관리되며, 다음의 명령어로 sub module 을 갖고옵니다.

```
git submodule update --init kksworks_tools 
```

### python module install

필요 python module 을 install 합니다.

- `pip install -r requirements.txt`

## how to install (using docker)

기존 설정되어있는 docker 설정파일을 이용하여 동작합니다.

### docker build / run

다음 두개의 파일을 host 에 다운로드합니다.

- [docker/Dockerfile](docker/Dockerfile)
- [docker/docker-compose.yml](docker/docker-compose.yml)

- `docker-compose.yml` 파일을 host 설정에 맞게 설정후에 다음의 명령어를 이용하여 `build` / `run` 합니다.

```sh
docker compose build
docker compose up -d
```

참고로 `docker-compose.yml` 에서 `config.json` 을 연결하여 동작에 필요한 설정을 합니다.

## 개인 config 설정

## how to run

`cli.py` 를 실행하여 각종 기능을 실행합니다.

```sh
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  click group

Options:
  --help  Show this message and exit.

Commands:
  chk-files         chk files (torent folders)
  cwral-site-infos  site info cwral form web
  cwral-tvshow      cwral tvshow magnet address (web cwral)
  tvshow-dn         tvshow download (query from db)
```

- `chk-files` : 각 토렌트 경로의 파일들을 파싱하여 정리합니다.
  - 다운로드 한 파일들에 대한 일관적인 파일명 유지
  - 각종 광고 문자열삭제
  - 하위 폴더 삭제
- `cwral-site-infos` : 크롤링할 토렌트 서버정보를 얻어옵니다.
- `cwral-tvshow` : 각 토렌트 사이트에서 마그넷 주소를 크롤링 합니다.
  - 크롤링한 데이터는 target mongodb 로 업데이트합니다.
- `tvshow-dn` :  tv show 를 다운로드합니다.

> 일반 사용자는 `tvshow-dn` 을 이용합니다.

각 동작들은 모두 db 에 데이터가있어야 동작을 합니다. db 구조 및 config 구조는 따로 설명하지 않습니다 ㅠ

### cli 실행 (using docker)

docker 를 이용하여 실행할경우 다음과같이 실행 합니다.

```
sudo docker exec -it tvshow_cwraler tvshow-dn
```

## tvshow download config

각 tv show down config 는 다음과 같은 구조를 가집니다.

```json
{
  "_id": {
    "$oid": "62cfb9b5a600ece66263b7e2"
  },
  "date_proc": {
    "chk_interval": 7,
    "target_date": {
      "$date": "2022-07-22T00:00:00.000Z"
    }
  },
  "dn_proc": "epi",
  "dn_target_dir": "/mnt/ext_5T_0/media_pub/TV - 예능/나 혼자 산다/",
  "epi_proc": {
    "target_epi": 545
  },
  "is_run": true,
  "max_save_days": 180,
  "prog_name": "나 혼자 산다",
  "rel_info": "*",
  "rel_resol": "*",
  "pri_key": null
}
```

- `dn_proc` : 다운로드 방법을 정합니다.
  - value : `epi` | `date`
    - epi : 에피소드 기반 다운로드 실행합니다. tvshow 의 경우 각 회차는 필수적으로 존재하므로 에피소드를 기반으로 자동 순차 증가 시키면서 다운로드 하게 됩니다. --> `epi_proc` 정보를 참조합니다.
    - date : 날짜 기반으로 다운로드를 실행합니다. 각 tvshow 는 날짜 정보를 포함하므로 interval 을 증가시키면서 다운로드 합니다. --> `date_proc` 정보를 참조합니다.
- `dn_target_dir` : 다운로드할 파일을 저장할 경로입니다.
  - value : `string`
  - docker 내에서 실행할경우 컨테이너기준으로 경로를 지정합니다.
- `max_save_days` : 최대 저장할 일자
  - value : `int`
  - 오래된 tvshow 는 삭제하기 위함
- `rel_info` : 특정 릴그룹을 지정하여 다운로드
  - value : `string`
  - `*` : 모든 릴그룹
- `rel_resol` : 특정 해상도를 지정하여 다운로드
  - value : `1080p` | `720p` (string 형식)

...

다운로드 방법 상세설정

- `date_proc` : date 기반 다운로드 설정
  - `chk_interval` : 체크할 인터벌, 7 로 설정할경우 7일마다 체크
  - `target_date` : 다음 검색할 타겟 날짜
- `epi_proc` : 에피소드 기반 다운로드 설정
  - `target_epi` : 다음 검색할 에피소드