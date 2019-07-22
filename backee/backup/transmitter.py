import os
import time
import logging
import subprocess
from typing import Optional

from abc import ABC, abstractmethod

from paramiko import SSHClient, AutoAddPolicy

from backee.model.servers import SshBackupServer
from backee.model.items import BackupItem, FilesBackupItem


log = logging.getLogger(__name__)


class Transmitter(ABC):

    @abstractmethod
    def transmit(self, item: BackupItem):
        pass


class SshTransmitter(Transmitter):

    def __init__(self, server: SshBackupServer):
        self.__server = server

        self.ssh = SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())

    def transmit(self, item: BackupItem):
        if isinstance(item, FilesBackupItem):
            self.__transmit_files(item)
        else:
            log.info(f"unsupported backup item: {item.name}")

    def __transmit_files(self, item: FilesBackupItem):
        log.debug(f'backing up {item.name} to {self.__server.name}')

        server_root_dir_path = os.path.join(
            self.__server.location, item.name, '')
        backup_dir_name = f'backup_{time.strftime("%Y-%m-%d-%H-%M")}'
        backup_dir_path = os.path.join(
            server_root_dir_path, backup_dir_name, '')
        temp_dir_suffix = '-incomplete'
        temp_dir_name = backup_dir_name + temp_dir_suffix
        temp_dir_path = os.path.join(server_root_dir_path, temp_dir_name, '')
        links_dir_path = os.path.join(server_root_dir_path, 'current')

        if not self.__is_remote_dir_exist(server_root_dir_path):
            self.__create_dir(server_root_dir_path)
        else:
            self.__remove_remote_dir_if_exists(backup_dir_path)
            self.__remove_remote_dir_if_exists(temp_dir_path)

            self.__check_temp_dirs(server_root_dir_path, temp_dir_suffix)

            self.__check_links_dir(server_root_dir_path,
                                   item.name,
                                   links_dir_path,
                                   temp_dir_suffix)

        self.__rsync(links_dir_path, item, temp_dir_path)

        self.__rename_dir(temp_dir_path, backup_dir_path)

        self.__recreate_links_dir(backup_dir_path, links_dir_path)

        log.debug(
            f"finished backing up of {item.name} to {self.__server.name}")

    def __execute_ssh_command(self, command: str):
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

        stderr = ', '.join(map(lambda s: s.rstrip(), stderr.readlines()))
        if stderr:
            raise OSError(f"stderr is not empty: '{stderr}'")

        return ', '.join(map(lambda s: s.rstrip(), stdout.readlines()))

    def __is_connected(self) -> bool:
        return self.ssh.get_transport() is not None and self.ssh.get_transport().is_active()

    def __ensure_connection(self) -> None:
        if not self.__is_connected():
            self.ssh.connect(hostname=self.__server.hostname,
                             port=self.__server.port,
                             username=self.__server.username,
                             key_filename=self.__server.key_path,
                             look_for_keys=self.__server.key_path == None)

    def __is_remote_dir_exist(self, path: str) -> bool:
        log.debug(f"checking if {path} exists")
        exists = self.__execute_ssh_command(
            f"if [ -d '{path}' ]; then echo true; else echo false; fi;")
        return exists == 'true'

    def __create_dir(self, path: str) -> None:
        log.debug(f"creating directory: {path}")
        result = self.__execute_ssh_command(f"mkdir -p '{path}'; echo $?")
        if result != '0':
            raise OSError(f"cannot create directory {path}")

    def __remove_remote_dir_if_exists(self, path: str) -> None:
        if self.__is_remote_dir_exist(path):
            self.__remove_remote_dir(path)

    def __remove_remote_dir(self, path: str) -> None:
        log.debug(f"removing directory {path}")
        result = self.__execute_ssh_command(f"rm -r '{path}'; echo $?")
        if result != '0':
            raise OSError(f"cannot remove directory {path}")

    def __check_temp_dirs(self, backup_dir_path: str, temp_dir_suffix: str) -> bool:
        log.debug(f"checking for temp dirs in {backup_dir_path}")

        result = self.__execute_ssh_command(
            f"find '{backup_dir_path}' -mindepth 1 -maxdepth 1 -type d -name '*{temp_dir_suffix}' | wc -l")

        if result != '0':
            log.error(f"Some temp dirs are in {backup_dir_path}")

    def __check_links_dir(self,
                          server_root_dir_path: str,
                          item_name: str,
                          links_dir_path: str,
                          temp_dir_suffix: str) -> None:
        log.debug("checking if directory for links exists")

        if self.__is_remote_dir_exist(links_dir_path):
            log.debug("links directory exists")
            return

        log.debug("links directory not found, trying to create a new one")

        last_backup_dir = self.__get_last_backup_dir(
            server_root_dir_path, temp_dir_suffix)
        if not last_backup_dir:
            log.debug("backup dir for relinking is not found")
            return

        log.debug(f'found last backup dir: {last_backup_dir}')
        if self.__recreate_links_dir(last_backup_dir, links_dir_path):
            log.debug("links dir recreated")
        else:
            log.debug("cannot recreate links dir")

    def __get_last_backup_dir(self,
                              server_root_dir_path: str,
                              temp_dir_suffix: str) -> Optional[str]:
        log.debug(f'looking for last backup dir in {server_root_dir_path}')

        command = f"find '{server_root_dir_path}' -mindepth 1 -maxdepth 1 " \
            "-type d ! -name '*{temp_dir_suffix}' " \
            "| sort -t- -k1 | tail -1"
        last_backup_dir = self.__execute_ssh_command(command)

        # TODO what is the output of this command??
        # if last_backup_dir:
        #     last_backup_dir = os.path.join(
        #         last_backup_dir, backup_dir_name, '')

        return last_backup_dir

    def __recreate_links_dir(self, last_backup_dir: str, links_dir_path: str) -> None:
        log.debug(f"re-linking '{last_backup_dir}' to '{links_dir_path}'")
        result = self.__execute_ssh_command(
            f"rm -f '{links_dir_path}' && ln -s '{last_backup_dir}' '{links_dir_path}'; echo $?")
        if result != '0':
            raise OSError(
                f"Cannot re-link directory {last_backup_dir} to {links_dir_path}")

    def __rename_dir(self, prev_name: str, new_name: str) -> None:
        log.debug(f"renaming dir from {prev_name} to {new_name}")
        result = self.__execute_ssh_command(
            f"mv '{prev_name}' '{new_name}'; echo $?")
        if result != '0':
            raise OSError(
                f"Cannot rename directory {prev_name} to {new_name}")

    def __rsync(self,
                links_dir_path: str,
                item: FilesBackupItem,
                remote_path: str) -> None:
        if self.__is_remote_dir_exist(links_dir_path):
            log.debug("links dir found")
            link_options = f"--link-dest={links_dir_path}"
        else:
            log.debug("links dir is not found")
            link_options = ''

        if self.__server.key_path:
            ssh_options = f"--rsh=\"ssh -i '{self.__server.key_path}' -p {self.__server.port}\" "
        else:
            ssh_options = f"--rsh=\"ssh -p {self.__server.port}\" "
        rsynccmd = f"rsync --archive --progress --compress {ssh_options} "
        rsynccmd += f"--verbose --human-readable --relative {link_options} "
        rsynccmd += f"{' '.join(f'--exclude {s}' for s in item.excludes)} "
        rsynccmd += f"{' '.join(item.includes)} "
        rsynccmd += f"{self.__server.username}@{self.__server.hostname}:{remote_path}"

        with subprocess.Popen(rsynccmd,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              bufsize=1,
                              universal_newlines=True) as rsync_proc:
            for line in rsync_proc.stdout:
                log.debug(line.rstrip())

            exit_code = rsync_proc.wait()
            if exit_code != 0:
                stderr = ", ".join(
                    map(lambda s: s.rstrip(), rsync_proc.stderr.readlines()))
                log.error(f"rsync finished with non-zero exit code {exit_code} "
                          f"and stderr: {stderr}")
                raise OSError(f'Cannot transfer to {remote_path}')
