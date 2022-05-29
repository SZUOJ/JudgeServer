import json
import os
import shlex

import judger

from config import COMPILER_GROUP_GID, COMPILER_LOG_PATH, COMPILER_USER_UID
from exception import CompileError, CompilerRuntimeError
from languages import BaseLanguageConfig


class Compiler(object):
    def compile(self, language_config: BaseLanguageConfig, src_path, output_dir):
        command = language_config.compile_command
        exe_path = os.path.join(output_dir, language_config.exe_name)
        command = command.format(src_path=src_path, exe_dir=output_dir, exe_path=exe_path)
        compiler_out = os.path.join(output_dir, "compiler.out")
        _command = shlex.split(command)

        os.chdir(output_dir)
        env = language_config.env
        env.append("PATH=" + os.getenv("PATH"))
        result = judger.run(max_cpu_time=language_config.max_cpu_time,
                            max_real_time=language_config.max_real_time,
                            max_memory=language_config.max_memory,
                            max_stack=128 * 1024 * 1024,
                            max_output_size=20 * 1024 * 1024,
                            max_process_number=judger.UNLIMITED,
                            exe_path=_command[0],
                            # /dev/null is best, but in some system, this will call ioctl system call
                            input_path=src_path,
                            output_path=compiler_out,
                            error_path=compiler_out,
                            args=_command[1::],
                            env=env,
                            log_path=COMPILER_LOG_PATH,
                            seccomp_rule_name=None,
                            uid=COMPILER_USER_UID,
                            gid=COMPILER_GROUP_GID)

        if result["result"] != judger.RESULT_SUCCESS:
            if os.path.exists(compiler_out):
                with open(compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    os.remove(compiler_out)
                    if error:
                        raise CompileError(error)
            raise CompilerRuntimeError("Compiler runtime error, info: %s" % json.dumps(result))
        else:
            os.remove(compiler_out)
            return exe_path
