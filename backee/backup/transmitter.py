import logging
import subprocess
import re
import os

from typing import Optional, Tuple

from paramiko import SSHClient, AutoAddPolicy

from backee.model.servers import SshBackupServer
from backee.model.items import BackupItem, FilesBackupItem
from backee.model.rotation_strategy import RotationStrategy
from backee.backup import constants


log = logging.getLogger(__name__)


class Transmitter(object):
    pass


class SshTransmitter(Transmitter):
    def __init__(
        self,
        server: SshBackupServer,
        ssh_client: SSHClient = None,
        deps: Tuple[str] = ("rsync",),
    ):
        self.__server = server

        self.__wildcard_check = re.compile("([*?[])")

        self.__check_deps(deps)

        if ssh_client is None:
            self.ssh = SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        else:
            self.ssh = ssh_client

    def is_remote_dir_exist(self, path: str) -> bool:
        log.debug(f"check existence of {path}")
        exists = self.__execute_ssh_command(
            f"if [ -d '{path}' ]; then echo true; else echo false; fi;"
        )
        return exists == "true"

    def create_dir(self, path: str) -> None:
        log.debug(f"create directory: {path}")
        result = self.__execute_ssh_command(f"mkdir -p '{path}'; echo $?")
        if result != "0":
            raise OSError(f"cannot create directory {path}")

    def remove_remote_dir_if_exists(self, path: str) -> None:
        if self.is_remote_dir_exist(path):
            self.remove_remote_dirs(
                (path),
            )

    def remove_remote_dirs(self, dirs_paths: Tuple[str]) -> None:
        log.debug("remove directories %s", {dirs_paths})
        remove_command = (
            "items=("
            + " ".join(f'"{item}"' for item in dirs_paths)
            + '); for item in ${items[*]}; do rm -rf "$item"; done'
        )
        result = self.__execute_ssh_command(f"{remove_command}; echo $?")
        if result != "0":
            raise OSError(f"cannot remove directories {dirs_paths}")

    def check_temp_dirs(self, backup_dir_path: str, temp_dir_suffix: str) -> bool:
        log.debug(f"checking for temp dirs in {backup_dir_path}")

        result = self.__execute_ssh_command(
            f"find '{backup_dir_path}' -mindepth 1 -maxdepth 1 -type d -name '*{temp_dir_suffix}' | wc -l"
        )

        if result != "0":
            log.error(f"some temp dirs are in {backup_dir_path}")

    def check_links_dir(
        self,
        server_root_dir_path: str,
        links_dir_path: str,
        temp_dir_suffix: str,
    ) -> None:
        """
        Check if links directory exists and recreate if not.
        Last backup will be used to link to.
        """
        log.debug("check links directory")

        if self.is_remote_dir_exist(links_dir_path):
            log.debug("links directory exists")
            return

        log.debug("links directory not found, create a new one")

        last_backup_dir = self.__get_last_backup_dir(
            server_root_dir_path, temp_dir_suffix
        )
        if not last_backup_dir:
            log.debug("backup dir for re-linking is not found")
            return

        log.debug(f"found last backup dir: {last_backup_dir}")
        if self.recreate_links_dir(last_backup_dir, links_dir_path):
            log.debug("links dir re-created")
        else:
            log.debug("cannot re-create links dir")

    def __get_last_backup_dir(
        self, server_root_dir_path: str, temp_dir_suffix: str
    ) -> Optional[str]:
        log.debug(f"looking for last backup dir in {server_root_dir_path}")

        command = (
            f"find '{server_root_dir_path}' -mindepth 1 -maxdepth 1 "
            "-type d ! -name '*{temp_dir_suffix}' "
            "| sort -t- -k1 | tail -1"
        )
        last_backup_dir = self.__execute_ssh_command(command)

        return last_backup_dir

    def recreate_links_dir(self, last_backup_dir: str, links_dir_path: str) -> None:
        log.debug(f"re-link '{last_backup_dir}' to '{links_dir_path}'")
        result = self.__execute_ssh_command(
            f"rm -f '{links_dir_path}' && ln -s '{last_backup_dir}' '{links_dir_path}'; echo $?"
        )
        if result != "0":
            raise OSError(
                f"Cannot re-link directory {last_backup_dir} to {links_dir_path}"
            )

    def rename_dir(self, prev_name: str, new_name: str) -> None:
        log.debug(f"rename {prev_name} to {new_name}")
        result = self.__execute_ssh_command(f"mv '{prev_name}' '{new_name}'; echo $?")
        if result != "0":
            raise OSError(f"Cannot rename directory {prev_name} to {new_name}")

    def __path_exists(self, path: str, excludes: bool) -> bool:
        if self.__wildcard_check.search(path) is not None:
            log.debug("skipping existence check for path with wildcards: %s", path)
            return True
        elif not os.path.exists(path):
            if excludes:
                log.error("excludes item does not exist: %s", path)
            else:
                log.error("file backup item does not exist: %s", path)
            return False

        return True

    def transmit(
        self, links_dir_path: str, item: FilesBackupItem, remote_path: str
    ) -> None:
        link_options = self.__get_link_dir_options(links_dir_path)
        ssh_optons = self.__get_rsync_ssh_options()
        excludes = " ".join(
            f'--exclude "{s}"' for s in item.excludes if self.__path_exists(s, True)
        )
        includes = " ".join(
            f'"{s}"' for s in item.includes if self.__path_exists(s, False)
        )

        rsync_cmd = (
            f"rsync --archive --progress --compress {ssh_optons} "
            f"--verbose --human-readable --relative {link_options} "
            f"{excludes} "
            f"{includes} "
            f"{self.__server.username}@{self.__server.hostname}:{remote_path}"
        )

        with subprocess.Popen(
            rsync_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ) as rsync_proc:
            for line in rsync_proc.stdout:
                log.debug(line.rstrip())

            self.__verify_exit_code(rsync_proc, remote_path)

    def __get_link_dir_options(self, links_dir_path: str) -> str:
        if self.is_remote_dir_exist(links_dir_path):
            log.debug("links dir found")
            return "--link-dest=" + links_dir_path
        else:
            log.debug("links dir not found")
            return ""

    def __get_rsync_ssh_options(self) -> str:
        options = f'--rsh="ssh -p {self.__server.port}'
        if self.__server.key_path:
            options += f" -i '{self.__server.key_path}'"
        options += ' -o StrictHostKeyChecking=no"'
        return options

    def get_backup_names_sorted(self, server_root_dir_path: str) -> Tuple[str]:
        find_dirs = f"find {server_root_dir_path} -mindepth 1 -maxdepth 1 -type d | sort -t- -k1"
        return tuple(self.__execute_ssh_command(find_dirs).split("\n"))

    def verify_backup(self, item: FilesBackupItem, remote_path: str) -> bool:
        log.debug("verifing backup")

        ssh_optons = self.__get_rsync_ssh_options()
        excludes = " ".join(f'--exclude "{s}"' for s in item.excludes)
        includes = " ".join(f'"{s}"' for s in item.includes)

        rsync_cmd = (
            "rsync --archive --verbose --hard-links --progress "
            f"--itemize-changes --dry-run --compress --relative {ssh_optons} "
            f"{excludes} "
            f"{includes} "
            f"{self.__server.username}@{self.__server.hostname}:{remote_path}"
        )

        no_errors = True
        with subprocess.Popen(
            rsync_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ) as rsync_proc:
            error_pattern = "^[<>]"
            warn_pattern = "^\."
            # skip warning for directories if their timestamp changed since backup
            false_positive = (".d..t",)
            for line in rsync_proc.stdout:
                fmt_line = line.rstrip()
                if (
                    re.findall(warn_pattern, fmt_line)
                    or re.findall(error_pattern, fmt_line)
                ) and not fmt_line.startswith(false_positive):
                    no_errors = False
                    log.debug("%s is different", fmt_line)
                    break

            self.__verify_exit_code(rsync_proc, remote_path)

        return no_errors

    def get_transfer_file_size(
        self, links_dir_path: str, item: FilesBackupItem, remote_path: str
    ) -> int:
        """
        Get size of items in bytes that need to be transfered.
        """
        link_options = self.__get_link_dir_options(links_dir_path)
        ssh_optons = self.__get_rsync_ssh_options()
        excludes = " ".join(f'--exclude "{s}"' for s in item.excludes)
        includes = " ".join(f'"{s}"' for s in item.includes)

        rsync_cmd = (
            "rsync --archive --stats --compress "
            f" --dry-run --relative {ssh_optons} {link_options} "
            f"{excludes} "
            f"{includes} "
            f"{self.__server.username}@{self.__server.hostname}:{remote_path}"
        )

        transfer_size = 0
        with subprocess.Popen(
            rsync_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ) as rsync_proc:
            line_start = "Total transferred file size: "
            for line in rsync_proc.stdout:
                fmt_line = line.rstrip()
                log.debug(fmt_line)
                if line_start in fmt_line:
                    transfer_size = int(re.search("\d+", fmt_line).group())
                    log.debug("transfer size is %i bytes", transfer_size)
                    break

            self.__verify_exit_code(rsync_proc, remote_path)

        return transfer_size

    def __verify_exit_code(
        self, rsync_proc: subprocess.Popen, remote_path: str
    ) -> None:
        """
        Verify rsync exit code and raises exception if process finished with an error

        Raises:
            OSError: if exit code is not RSYNC_STATUS_SOURCE_VANISHED or RSYNC_STATUS_SUCCESS
        """
        exit_code = rsync_proc.wait()
        if exit_code == constants.RSYNC_STATUS_SOURCE_VANISHED:
            stderr = "\n".join(map(lambda s: s.rstrip(), rsync_proc.stderr.readlines()))
            log.warning(
                "source item vanished before rsync was able to copy it over: %s",
                stderr,
            )
        elif exit_code != constants.RSYNC_STATUS_SUCCESS:
            stderr = "\n".join(map(lambda s: s.rstrip(), rsync_proc.stderr.readlines()))
            log.error(
                "rsync finished with non-zero exit code %i and stderr: %s",
                exit_code,
                stderr,
            )
            raise OSError(f"Cannot transfer to {remote_path}")

    def get_disk_space_available(self, remote_path: str) -> int:
        """
        Return available disk space in bytes.
        """
        cmd = f"df -P -B1 {remote_path} | awk 'NR==2 {{print $4}}'"
        return int(self.__execute_ssh_command(cmd))

    def __execute_ssh_command(self, command: str) -> str:
        """
        Executes SSH command on the server.

        Arguments:
          command (str): sh command to execute on remote.

        Returns:
          str: stdout of command.

        Raises:
            OSError: if stderr is not empty.
        """
        self.__ensure_connection()

        _, stdout, stderr = self.ssh.exec_command(command)

        stderr = "\n".join(map(lambda s: s.rstrip(), stderr.readlines()))
        if stderr:
            raise OSError(f"stderr is not empty: '{stderr}'")

        return "\n".join(map(lambda s: s.rstrip(), stdout.readlines()))

    def __is_connected(self) -> bool:
        return (
            self.ssh.get_transport() is not None
            and self.ssh.get_transport().is_active()
        )

    def __ensure_connection(self) -> None:
        if not self.__is_connected():
            self.ssh.connect(
                hostname=self.__server.hostname,
                port=self.__server.port,
                username=self.__server.username,
                key_filename=self.__server.key_path,
                look_for_keys=self.__server.key_path is None,
            )

    def __check_deps(self, deps: Tuple[str]) -> None:
        """
        Check that deps, passed as arguments are available and raise an excpetion if not.
        """
        for dep in deps:
            cmd = f"hash {dep}"
            with subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
            ) as proc:
                exit_code = proc.wait()
                if exit_code != 0:
                    raise OSError(f"{dep} is not installed, but required")
