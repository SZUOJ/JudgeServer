#!/bin/bash

rm -rf /judger/*
mkdir -p /judger/run /judger/spj

chown compiler:code /judger/run
chmod 711 /judger/run

chown compiler:spj /judger/spj
chmod 710 /judger/spj

if [ -z "$MAX_WORKER_NUM" ]; then
  CPU_CORE_NUM=$(grep -c ^processor /proc/cpuinfo)
  export CPU_CORE_NUM
  if [ "$CPU_CORE_NUM" -lt 2 ]; then
    export MAX_WORKER_NUM=2
  else
    export MAX_WORKER_NUM=$((CPU_CORE_NUM / 2))
  fi
fi

exec gunicorn --workers "$MAX_WORKER_NUM" --threads "$MAX_WORKER_NUM" --error-logfile /log/gunicorn.log --time 600 --bind 0.0.0.0:8080 server:app
