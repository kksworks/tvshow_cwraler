
FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update

# locale for korean
RUN apt-get install -y language-pack-ko language-pack-ko-base
RUN apt-get -y install locales
RUN localedef -f UTF-8 -i ko_KR ko_KR.UTF-8
RUN locale-gen ko_KR.UTF-8
RUN locale-gen en_US.UTF-8

# env 가 안되서 다음과같이 강제설정
RUN echo "LANG=ko_KR.UTF-8" >> /etc/environment
RUN echo "LANGUAGE=ko_KR:ko:en_GB:en" >> /etc/environment
RUN echo "LC_ALL=ko_KR.UTF-8" >> /etc/environment
RUN echo "PYTHONIOENCODING=utf8" >> /etc/environment

# install packages
RUN apt-get install -y python3 python3-pip git transmission-cli
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN mkdir /works
RUN git clone -b 1.0 --single-branch https://github.com/kksworks/tvshow_cwraler.git /works && cd /works && git submodule update --init kksworks_tools 
RUN cd /works && pip install -r requirements.txt
RUN cp -rf /works/config.json.sample /works/config.json
ENV PATH="${PATH}:/works"
WORKDIR /works
