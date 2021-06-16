FROM ubuntu:20.04

COPY build/java_policy /etc
RUN export DEBIAN_FRONTEND="noninteractive" && \
    buildDeps='software-properties-common git libtool make cmake python3-dev python3-pip libseccomp-dev' && \
    apt-get update && apt-get install -y python3 python3-pkg-resources gcc g++ $buildDeps && \
    add-apt-repository ppa:openjdk-r/ppa && add-apt-repository ppa:longsleep/golang-backports && apt-get update && \
    apt-get install -y golang-go openjdk-8-jdk && \
    pip3 install -I --no-cache-dir psutil gunicorn flask requests idna && \
    cd /tmp && git clone -b newnew  --depth 1 https://github.com/SZUOJ/Judger && cd Judger && \
    mkdir build && cd build && cmake .. && make && make install && cd ../bindings/Python && python3 setup.py install && \
    apt-get purge -y --auto-remove $buildDeps && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /server && export PYTHONPATH=/server && \
    useradd -u 12001 compiler && useradd -u 12002 code && useradd -u 12003 spj && usermod -a -G code spj

ADD server /server
HEALTHCHECK --interval=5s --retries=3 CMD python3 /server/service.py
WORKDIR /server
RUN gcc -shared -fPIC -o unbuffer.so unbuffer.c
EXPOSE 8080
ENTRYPOINT /server/entrypoint.sh
