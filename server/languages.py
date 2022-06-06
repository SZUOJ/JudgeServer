# coding=utf-8
from __future__ import unicode_literals

import platform
from typing import Literal, Optional, Type, TypedDict

from utils import ProblemIOMode

py_version = ''.join(platform.python_version().split('.')[:2])

default_env = ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]

C_STDS = {'c89', 'c90', 'c99', 'c11', 'c17', 'c18',
          'gnu89', 'gnu90', 'gnu99', 'gnu11', 'gnu17', 'gnu18'}
CPP_STDS = {'c++98', 'c++03', 'c++11', 'c++14', 'c++17', 'c++20', 'c++23',
            'gnu++98', 'gnu++03', 'gnu++11', 'gnu++14', 'gnu++17', 'gnu++20',
            'gnu++23'}


class OptionType(TypedDict, total=False):
    version: Optional[str]  # C/C++ 语言标准，如 C11, C++11 等
    enable_asan: bool  # 是否使用 Address Sanitizer (越界检查)，默认关闭
    enable_lsan: bool  # 是否使用 Leak Sanitizer (内存泄漏检查)，默认关闭


class BaseLanguageConfig:
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        self.options = options or {}
        self.src_name = None
        self.exe_name = None
        self.max_cpu_time = 10000  # 最大编译占用 CPU 时间
        self.max_real_time = 20000  # 最大编译占用真实时间
        self.max_memory = 1024 * 1024 * 1024  # 最大编译占用内存
        self._compile_command = None
        self._execute_command = None
        self._seccomp_rule: str = 'general'
        self._env: list[str] = default_env
        self.memory_limit_check_only = 0  # 是否仅检查内存限制，默认 0 不检查，1 检查
        self.compiled = True  # 是否编译型语言

        self.io_mode = io_mode
        assert self.io_mode in {ProblemIOMode.standard, ProblemIOMode.file}
        self.enable_asan = self.options.get('enable_asan', False)
        self.enable_lsan = self.options.get('enable_lsan', False)

    @property
    def compile_command(self) -> str:
        return self._compile_command

    @property
    def execute_command(self) -> str:
        return self._execute_command

    @property
    def seccomp_rule(self) -> str:
        return self._seccomp_rule

    @property
    def env(self) -> list[str]:
        return self._env


class CConfig(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'main.c'
        self.exe_name = 'main'
        self.max_cpu_time = 3000
        self.max_real_time = 10000
        self.max_memory = 256 * 1024 * 1024
        self._execute_command = '{exe_path}'
        self.compiler = '/usr/bin/gcc'
        self.std = self.options.get('version', 'c11').lower() or 'c11'
        if self.enable_asan:
            self.memory_limit_check_only = 1

    @property
    def compile_command(self) -> str:
        if isinstance(self, CppConfig):
            assert self.std in CPP_STDS, f"Unsupported C++ standard: {self.std}"
        elif isinstance(self, CConfig):
            assert self.std in C_STDS, f"Unsupported C standard: {self.std}"
        else:
            raise RuntimeError("compile_command validation error")

        params = ['-std=' + self.std]
        if self.enable_asan:
            params.append('-O1 -fsanitize=address -fno-omit-frame-pointer')
        else:
            params.append('-O2')

        command = [self.compiler, ' -DONLINE_JUDGE -w ', *params, ' -fmax-errors=3 {src_path} -lm -o {exe_path}']
        command = ' '.join(command)
        return command

    @property
    def seccomp_rule(self) -> str:
        if self.enable_asan:
            return 'c_cpp_asan'
        return {
            ProblemIOMode.standard: 'c_cpp',
            ProblemIOMode.file: 'c_cpp_file_io'
        }[self.io_mode]

    @property
    def env(self) -> list[str]:
        if self.enable_lsan:
            return default_env
        return default_env + ['ASAN_OPTIONS=detect_leaks=0']


class CppConfig(CConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'main.cpp'
        self.max_cpu_time = 10000
        self.max_real_time = 20000
        self.max_memory = 1024 * 1024 * 1024

        self.compiler = '/usr/bin/g++'
        self.std = self.options.get('version', 'c++14').lower() or 'c++14'


class JavaConfig(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'Main.java'
        self.exe_name = 'Main'
        self.max_cpu_time = 5000
        self.max_real_time = 10000
        self.max_memory = -1  # 不限制
        self._compile_command = '/usr/bin/javac {src_path} -d {exe_dir} -encoding UTF8'
        self._execute_command = '/usr/bin/java -cp {exe_dir} -XX:MaxRAM={max_memory}k -Djava.security.manager ' \
                                '-Dfile.encoding=UTF-8 -Djava.security.policy==/etc/java_policy ' \
                                '-Djava.awt.headless=true Main'


class Py3Config(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'main.py'
        self.exe_name = 'main.py'
        self.max_cpu_time = 3000
        self.max_real_time = 10000
        self.max_memory = 128 * 1024 * 1024
        self._compile_command = '/usr/bin/python3 -m py_compile {src_path}'
        self._execute_command = '/usr/bin/python3 {exe_path}'
        self._env = default_env + ['PYTHONIOENCODING=utf-8']
        self.compiled = False


class GoConfig(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'main.go'
        self.exe_name = 'main'
        self.max_cpu_time = 3000
        self.max_real_time = 5000
        self.max_memory = 1024 * 1024 * 1024
        self._compile_command = '/usr/bin/go build -o {exe_path} {src_path}'
        self._execute_command = '{exe_path}'
        self._seccomp_rule = 'golang'
        # 降低内存占用
        self._env = default_env + ['GODEBUG=madvdontneed=1', 'GOCACHE=/tmp', 'GOPATH=/tmp/go']

        self.memory_limit_check_only = 1


class PHPConfig(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'solution.php'
        self.exe_name = 'solution.php'
        self._execute_command = '/usr/bin/php {exe_path}'
        self._env = default_env
        self.memory_limit_check_only = 1
        self.compiled = False
        self._seccomp_rule = ''  # 不使用 seccomp


class JSConfig(BaseLanguageConfig):
    def __init__(self, options: Optional[OptionType] = None,
                 io_mode: Optional[Literal['stdio', 'file']] = ProblemIOMode.standard):
        super().__init__(options, io_mode)
        self.src_name = 'solution.js'
        self.exe_name = 'solution.js'
        self._execute_command = '/usr/bin/node {exe_path}'
        self._env = default_env + ["NO_COLOR=true"]
        self._seccomp_rule = 'node'
        self.memory_limit_check_only = 1
        self.compiled = False


c_lang_spj_compile = {
    "src_name": "spj-{spj_version}.c",
    "exe_name": "spj-{spj_version}",
    "max_cpu_time": 3000,
    "max_real_time": 5000,
    "max_memory": 1024 * 1024 * 1024,
    "compile_command": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c99 {src_path} -lm -o {exe_path}"
}

c_lang_spj_config = {
    "exe_name": "spj-{spj_version}",
    "command": "{exe_path} {in_file_path} {user_out_file_path}",
    "seccomp_rule": "c_cpp"
}

cpp_lang_spj_compile = {
    "src_name": "spj-{spj_version}.cpp",
    "exe_name": "spj-{spj_version}",
    "max_cpu_time": 10000,
    "max_real_time": 20000,
    "max_memory": 1024 * 1024 * 1024,
    "compile_command": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++14 {src_path} -lm -o {exe_path}"
}

cpp_lang_spj_config = {
    "exe_name": "spj-{spj_version}",
    "command": "{exe_path} {in_file_path} {user_out_file_path}",
    "seccomp_rule": "c_cpp"
}

lang_map: dict[str, Type[BaseLanguageConfig]] = {
    'c': CConfig,
    'cpp': CppConfig,
    'java': JavaConfig,
    'py': Py3Config,
    'go': GoConfig,
    'php': PHPConfig,
    'js': JSConfig,
}
if __name__ == '__main__':
    print(CppConfig().compile_command)
