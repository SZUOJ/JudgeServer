import hashlib
import json
import os
import re
import shlex
import shutil
from multiprocessing import Pool
from typing import Tuple

import judger
import psutil

from config import JUDGER_RUN_LOG_PATH, MAX_READ_BYTES, MAX_RESP_BYTES, RUN_GROUP_GID, RUN_USER_UID, SPJ_EXE_DIR, \
    SPJ_GROUP_GID, SPJ_USER_UID
from exception import JudgeClientError
from languages import BaseLanguageConfig
from utils import ProblemIOMode

SPJ_WA = 1
SPJ_AC = 0
SPJ_ERROR = -1


def _run(instance, test_case_file_id):
    return instance._judge_one(test_case_file_id)


class JudgeClient(object):
    def __init__(self, language_config: BaseLanguageConfig, exe_path, max_cpu_time, max_memory, test_case_dir,
                 submission_dir, spj_version, spj_config, io_mode, output=False):
        self._language_config = language_config
        self._exe_path = exe_path
        self._max_cpu_time = max_cpu_time
        self._max_memory = max_memory
        self._max_real_time = self._max_cpu_time * 3
        self._test_case_dir = test_case_dir
        self._submission_dir = submission_dir

        self._pool = Pool(processes=psutil.cpu_count())
        self._test_case_info = self._load_test_case_info()

        self._spj_version = spj_version
        self._spj_config = spj_config
        self._output = output
        self._io_mode = io_mode

        if self._spj_version and self._spj_config:
            self._spj_exe = os.path.join(SPJ_EXE_DIR,
                                         self._spj_config["exe_name"].format(spj_version=self._spj_version))
            if not os.path.exists(self._spj_exe):
                raise JudgeClientError("spj exe not found")

    def _load_test_case_info(self):
        try:
            with open(os.path.join(self._test_case_dir, "info")) as f:
                return json.load(f)
        except IOError:
            raise JudgeClientError("Test case not found")
        except ValueError:
            raise JudgeClientError("Bad test case config")

    def _get_test_case_file_info(self, test_case_file_id):
        return self._test_case_info["test_cases"][test_case_file_id]

    def _compare_output(self, test_case_file_id, user_output_file) -> Tuple[str, int]:
        """比较输出md5

        :param test_case_file_id:
        :param user_output_file:
        :return: md5和答案状态
        """
        with open(user_output_file, "rb") as f:
            output_str = f.read(MAX_READ_BYTES)
        stripped_output = re.sub(pattern=rb"\s", repl=b"", string=output_str)  # 去除所有空字符

        output_md5 = hashlib.md5(output_str.rstrip()).hexdigest()
        stripped_output_md5 = hashlib.md5(stripped_output).hexdigest()

        test_case_file_info = self._get_test_case_file_info(test_case_file_id)

        if output_md5 == test_case_file_info["output_md5"]:
            return output_md5, judger.RESULT_SUCCESS
        elif stripped_output_md5 == test_case_file_info["stripped_output_md5"]:
            return output_md5, judger.RESULT_PRESENTATION_ERROR
        else:
            return output_md5, judger.RESULT_WRONG_ANSWER

    def _spj(self, in_file_path, user_out_file_path):
        os.chown(self._submission_dir, SPJ_USER_UID, 0)
        os.chown(user_out_file_path, SPJ_USER_UID, 0)
        os.chmod(user_out_file_path, 0o740)
        command = self._spj_config["command"].format(exe_path=self._spj_exe,
                                                     in_file_path=in_file_path,
                                                     user_out_file_path=user_out_file_path)
        command = shlex.split(command)
        seccomp_rule_name = self._spj_config["seccomp_rule"]
        result = judger.run(max_cpu_time=self._max_cpu_time * 3,
                            max_real_time=self._max_cpu_time * 9,
                            max_memory=self._max_memory * 3,
                            max_stack=128 * 1024 * 1024,
                            max_output_size=1024 * 1024 * 1024,
                            max_process_number=judger.UNLIMITED,
                            exe_path=command[0],
                            input_path=in_file_path,
                            output_path="/tmp/spj.out",
                            error_path="/tmp/spj.out",
                            args=command[1::],
                            env=["PATH=" + os.environ.get("PATH", "")],
                            log_path=JUDGER_RUN_LOG_PATH,
                            seccomp_rule_name=seccomp_rule_name,
                            uid=SPJ_USER_UID,
                            gid=SPJ_GROUP_GID)

        if result["result"] == judger.RESULT_SUCCESS or \
                (result["result"] == judger.RESULT_RUNTIME_ERROR and
                 result["exit_code"] in [SPJ_WA, SPJ_ERROR] and result["signal"] == 0):
            return result["exit_code"]
        else:
            return SPJ_ERROR

    def _judge_one(self, test_case_file_id):
        test_case_info = self._get_test_case_file_info(test_case_file_id)
        in_file = os.path.join(self._test_case_dir, test_case_info["input_name"])

        if self._io_mode["io_mode"] == ProblemIOMode.file:
            user_output_dir = os.path.join(self._submission_dir, str(test_case_file_id))
            os.mkdir(user_output_dir)
            os.chown(user_output_dir, RUN_USER_UID, RUN_GROUP_GID)
            os.chmod(user_output_dir, 0o711)
            os.chdir(user_output_dir)
            # todo check permission
            user_output_file = os.path.join(user_output_dir, self._io_mode["output"])
            real_user_output_file = os.path.join(user_output_dir, "stdio.txt")
            shutil.copyfile(in_file, os.path.join(user_output_dir, self._io_mode["input"]))
            kwargs = {"input_path": in_file, "output_path": real_user_output_file, "error_path": real_user_output_file}
        else:
            real_user_output_file = user_output_file = os.path.join(self._submission_dir, test_case_file_id + ".out")
            kwargs = {"input_path": in_file, "output_path": real_user_output_file, "error_path": real_user_output_file}

        command = self._language_config.execute_command.format(exe_path=self._exe_path,
                                                               exe_dir=os.path.dirname(self._exe_path))
        command = shlex.split(command)
        env = ["PATH=" + os.environ.get("PATH", "")] + self._language_config.env

        seccomp_rule = self._language_config.seccomp_rule

        run_result = judger.run(max_cpu_time=self._max_cpu_time,
                                max_real_time=self._max_real_time,
                                max_memory=self._max_memory,
                                max_stack=128 * 1024 * 1024,
                                max_output_size=max(test_case_info.get("output_size", 0) * 2, 1024 * 1024 * 16),
                                max_process_number=judger.UNLIMITED,
                                exe_path=command[0],
                                args=command[1::],
                                env=env,
                                log_path=JUDGER_RUN_LOG_PATH,
                                seccomp_rule_name=seccomp_rule,
                                uid=RUN_USER_UID,
                                gid=RUN_GROUP_GID,
                                memory_limit_check_only=self._language_config.memory_limit_check_only,
                                **kwargs)
        run_result["test_case"] = test_case_file_id

        # if progress exited normally, then we should check output result
        run_result["output_md5"] = None
        run_result["output"] = None
        if run_result["result"] == judger.RESULT_SUCCESS:
            if not os.path.exists(user_output_file):
                run_result["result"] = judger.RESULT_WRONG_ANSWER
            else:
                if self._test_case_info.get("spj"):
                    if not self._spj_config or not self._spj_version:
                        raise JudgeClientError("spj_config or spj_version not set")

                    spj_result = self._spj(in_file_path=in_file, user_out_file_path=user_output_file)

                    if spj_result == SPJ_WA:
                        run_result["result"] = judger.RESULT_WRONG_ANSWER
                    elif spj_result == SPJ_ERROR:
                        run_result["result"] = judger.RESULT_SYSTEM_ERROR
                        run_result["error"] = judger.ERROR_SPJ_ERROR
                else:
                    run_result["output_md5"], run_result["result"] = self._compare_output(test_case_file_id,
                                                                                          user_output_file)

        if self._output:
            try:
                with open(user_output_file, "rb") as f:
                    temp_output = f.read(MAX_RESP_BYTES).decode("utf-8", errors="backslashreplace")
                    run_result["output"] = re.sub(r'\u0000', '', temp_output)  # 去除\0
            except Exception:
                pass

        return run_result

    def run(self):
        tmp_result = []
        result = []
        for test_case_file_id, _ in self._test_case_info["test_cases"].items():
            tmp_result.append(self._pool.apply_async(_run, (self, test_case_file_id)))
        self._pool.close()
        self._pool.join()
        for item in tmp_result:
            # exception will be raised, when get() is called
            # # http://stackoverflow.com/questions/22094852/how-to-catch-exceptions-in-workers-in-multiprocessing
            result.append(item.get())
        return result

    def __getstate__(self):
        # http://stackoverflow.com/questions/25382455/python-notimplementederror-pool-objects-cannot-be-passed-between-processes
        self_dict = self.__dict__.copy()
        del self_dict["_pool"]
        return self_dict
