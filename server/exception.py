class JudgeServerException(Exception):
    status = 500

    def __init__(self, message):
        super().__init__()
        self.message = message


class CompileError(JudgeServerException):
    """编译错误"""

    status = 400


class CompilerRuntimeError(JudgeServerException):
    """编译器运行异常"""

    pass


class SPJCompileError(JudgeServerException):
    pass


class TokenVerificationFailed(JudgeServerException):
    pass


class JudgeClientError(JudgeServerException):
    pass


class JudgeServiceError(JudgeServerException):
    pass
