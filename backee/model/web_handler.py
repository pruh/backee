import logging
from logging import LogRecord

import requests
from requests.auth import HTTPBasicAuth

from concurrent.futures import ThreadPoolExecutor

from typing import Dict, Optional


class WebHandler(logging.Handler):

    def __init__(self, method: str, url: str, headers: Dict[str, str],
                 body: str, auth: Optional[Dict[str, str]], name: str):

        name_pattern = '{{ name }}'

        self._method = method
        self._url = self.__replace_pattern(
            pattern=name_pattern, new_text=name, original=url)
        self._headers = self.__replace_pattern_in_map(
            pattern=name_pattern, new_text=name, original_dict=headers) if headers else None
        self._body = self.__replace_pattern(
            pattern=name_pattern, new_text=name, original=body) if body else None

        if auth is not None and auth['type'] == 'basic':
            self._auth = HTTPBasicAuth(
                username=auth['username'], password=auth['password'])
        else:
            self._auth = None

        self.__executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix='web_logger')

        # call in the end of init as it is creates lock and
        # relies on __hash__ method, which requires all attributes to be set first
        super().__init__()

    def __replace_pattern(self, pattern: str, new_text: str, original: str) -> str:
        """
        Replace pattern in string with and URL encode.
        """
        return original.replace(
            pattern, new_text.replace("\\", "\\\\").replace('"', '\\"'))

    def __replace_pattern_in_map(self, pattern: str, new_text: str, original_dict: Dict[str, str]):
        new_dict = {}
        for k, v in original_dict.items():
            new_k = self.__replace_pattern(
                pattern=pattern, new_text=new_text, original=k)
            new_v = self.__replace_pattern(
                pattern=pattern, new_text=new_text, original=v)
            new_dict[new_k] = new_v
        return new_dict

    def emit(self, record: LogRecord):
        message_pattern = '{{ message }}'
        message = self.__format(record)
        url = self.__replace_pattern(
            pattern=message_pattern, new_text=message, original=self._url)
        headers = self.__replace_pattern_in_map(
            pattern=message_pattern, new_text=message, original_dict=self._headers)if self._headers else None
        data = self.__replace_pattern(
            pattern=message_pattern, new_text=message, original=self._body) if self._body else None
        future = self.__executor.submit(
            self.__make_call, self._method, url, headers, data, self._auth)
        try:
            self.__create_logger().debug(future.result(timeout=60))
        except Exception:
            self.__create_logger().exception('error while sending web log message')

    def __format(self, record):
        if record.exc_info:
            return f'{record.msg}: {record.exc_info}'
        else:
            return record.msg

    def __make_call(self,
                    method: str,
                    url: str,
                    headers: Optional[Dict[str, str]],
                    data: str,
                    auth: Optional[Dict[str, str]]):
        result = None
        if method == 'POST':
            result = requests.post(
                url=url,
                headers=headers,
                data=data,
                auth=auth)
        elif method == 'GET':
            result = requests.get(
                url=url,
                headers=headers,
                auth=auth)

        return f"web logger response {result}"

    def __create_logger(self) -> logging.Logger:
        """
        Creates logger that will avoid infinite loop and will not log to WebHandler
        """
        log = logging.getLogger(__name__)

        # get all handlers that are not instance of WebHandler
        handlers = []
        c = log
        while c:
            handlers.extend(
                [handler for handler in c.handlers if not isinstance(handler, WebHandler)])

            if not c.propagate:
                c = None  # break out
            else:
                c = c.parent

        # disable propagating current message to avoid logging to WebHandler
        log.propagate = False

        # add suitable handlers to new logger
        [log.addHandler(handler) for handler in handlers]

        return log

    def __repr__(self) -> str:
        """
        Make it similar to default handlers.
        """
        return f'<{self.__class__.__name__} {self._url} ({logging.getLevelName(self.level)})>'

    def __members(self):
        return (self.level,
                self._method,
                self._url,
                tuple(sorted(self._headers.items())
                      ) if self._headers else None,
                self._body,
                self._auth.username if self._auth else None,
                self._auth.password if self._auth else None,
                tuple(self.filters))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__members() == other.__members()
        else:
            return False

    def __hash__(self):
        return hash(self.__members())
