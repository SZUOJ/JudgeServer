#!/bin/bash
set -ex

rm -rf /judger/*
mkdir -p /judger/run /judger/spj /log

chown compiler:code /judger/run
chmod 711 /judger/run

chown compiler:spj /judger/spj
chmod 710 /judger/spj

# 限制运行用户读取宿主敏感系统文件（/etc/hosts 在容器启动时会被重新挂载）
for f in /etc/passwd /etc/group /etc/hosts; do
  if [ -e "$f" ]; then
    chmod 640 "$f"
  fi
done


if [ -z "$MAX_WORKER_NUM" ]; then
  CPU_CORE_NUM="$(nproc)"
  export CPU_CORE_NUM
  if [ "$CPU_CORE_NUM" -lt 2 ]; then
    export MAX_WORKER_NUM=2
  else
    export MAX_WORKER_NUM=$CPU_CORE_NUM
  fi
fi

exec .venv/bin/gunicorn server:app -c gunicorn_config.py --time 600
