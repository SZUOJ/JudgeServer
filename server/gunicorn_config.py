import os

bind = "0.0.0.0:8080"
error_logfile = "/log/gunicorn.log"
workers = int(int(os.getenv("MAX_WORKER_NUM", default=2)) / 2)
threads = 4
