# JudgeServer

[Document](http://docs.onlinejudge.me/)

API示例

- Request POST
```json
{
    "language": "py",
    "src": "import re\nprint(\"666\")",
    "max_cpu_time": 3000,
    "max_memory": 33554432,
    "test_case_id": "test",
    "output": false
}
```

- Response

result为Judger的判题结果。
```json
{
    "err": null,
    "data": [
        {
            "cpu_time": 30,
            "real_time": 30,
            "memory": 9691136,
            "signal": 0,
            "exit_code": 0,
            "error": 0,
            "result": -1,
            "test_case": "1",
            "output_md5": "fae0b27c451c728867a567e8c1bb4e53",
            "output": null
        }
    ]
}
```