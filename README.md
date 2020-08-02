# JudgeServer

[Document](http://opensource.qduoj.com/)

API示例

- Request POST
```json
{
    "language": "py",
    "src": "import re",
    "max_cpu_time": 3000,
    "max_memory": 33554432,
    "test_case_id": "test",
    "output": "False"
}
```

- Response

result为Judger的判题结果。
```json
{
    "err": null,
    "data": [
        {
            "cpu_time": 18,
            "real_time": 19,
            "memory": 8769536,
            "signal": 0,
            "exit_code": 1,
            "error": 0,
            "result": 4,
            "test_case": "1",
            "output_md5": null,
            "output": "Traceback (most recent call last):\n  File \"/judger/run/6c553f72a28b4e7e88b02dadf2d9b352/solution.py\", line 1, in <module>\nModuleNotFoundError: No module named 'r'\n"
        }
    ]
}
```
