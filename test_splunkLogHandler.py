from unittest import TestCase
from unittest.mock import patch

import logging

import splunkloghandler


class TestSplunkLogHandler(TestCase):
    def setUp(self):
        self.splunk_http_handler = splunkloghandler.SplunkLogHandler('host', 'url', 'token')
        self.logrecord = logging.LogRecord('simple_example',
                                           10,
                                           '/Users/spa/Git/palette-splunk-logger/test_logger.py',
                                           15,
                                           'debug message',
                                           None,
                                           None,
                                           '<module>',
                                           None
                                           )
        self.logrecord.created = 1480955547.678524
        self.logrecord.msecs = 678.5240173339844
        self.logrecord.relativeCreated = 6.676912307739258

        #     **{'relativeCreated': 6.676912307739258, 'funcName': '<module>', 'lineno': 15, 'name': 'simple_example',
        #        'levelname': 'DEBUG', 'filename': 'test_logger.py', 'msecs': 678.5240173339844, 'exc_info': None,
        #        'created': 1480955547.678524, 'stack_info': None, 'process': 10581, 'exc_text': None, 'args': (),
        #        'levelno': 10,
        #        'thread': 140736880042944, 'processName': 'MainProcess', 'msg': 'debug message',
        #        'pathname': '/Users/spa/Git/palette-splunk-logger/test_logger.py', 'threadName': 'MainThread',
        #        'module': 'test_logger'})
        self.splunk_event = self.splunk_http_handler.mapLogRecordWithFormat(self.logrecord)

    def test_event_has_no_time(self):
        self.assertNotIn('time', self.splunk_event)

    @patch('socket.gethostname')
    def test_event_has_hostname(self, mock_gethostname):
        mock_gethostname.return_value = "test_host.local"
        splunk_event = self.splunk_http_handler.mapLogRecordWithFormat(self.logrecord)
        self.assertEqual("test_host.local", splunk_event["host"])

    def test_event_has_the_message(self):
        self.assertEqual('debug message', self.splunk_event["event"])

    def test_formatted_output_without_formatter(self):
        splunk_event = self.splunk_http_handler.mapLogRecordWithFormat(self.logrecord)

        self.assertEqual('debug message', splunk_event["event"])

    def test_formatted_output_with_formatter(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.splunk_http_handler.setFormatter(formatter)
        splunk_event = self.splunk_http_handler.mapLogRecordWithFormat(self.logrecord)

        self.assertEqual('2016-12-05 17:32:27,678 - simple_example - DEBUG - debug message', splunk_event["event"])
