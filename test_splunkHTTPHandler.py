from unittest import TestCase
from unittest.mock import patch

from splunkhttphandler import SplunkHTTPHandler


class Record(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class TestSplunkHTTPHandler(TestCase):
    def setUp(self):
        self.splunk_http_handler = SplunkHTTPHandler('host', 'url', 'token')
        self.logrecord = Record(
            **{'relativeCreated': 6.676912307739258, 'funcName': '<module>', 'lineno': 15, 'name': 'simple_example',
               'levelname': 'DEBUG', 'filename': 'test_logger.py', 'msecs': 678.5240173339844, 'exc_info': None,
               'created': 1480955547.678524, 'stack_info': None, 'process': 10581, 'exc_text': None, 'args': (),
               'levelno': 10,
               'thread': 140736880042944, 'processName': 'MainProcess', 'msg': 'debug message',
               'pathname': '/Users/spa/Git/palette-splunk-logger/test_logger.py', 'threadName': 'MainThread',
               'module': 'test_logger'})
        self.splunk_event = self.splunk_http_handler.mapLogRecord(self.logrecord)

    def test_event_has_time_and_source(self):
        self.assertEqual(1480955547.678524, self.splunk_event["time"])
        self.assertEqual('test_logger', self.splunk_event["source"])

    @patch('socket.gethostname')
    def test_event_has_hostname(self, mock_gethostname):
        mock_gethostname.return_value = "test_host.local"
        splunk_event = self.splunk_http_handler.mapLogRecord(self.logrecord)
        self.assertEqual("test_host.local", splunk_event["host"])

    def test_event_has_the_logevent_details(self):
        logevent = self.splunk_event["event"]
        self.assertEqual('debug message', logevent["message"])
        self.assertEqual("DEBUG", logevent["level"])
