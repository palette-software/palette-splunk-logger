import json
import logging
import socket

class SplunkHTTPHandler(logging.Handler):
    """
    A class which sends records to a Splunk server via its HTTP Event Collector
    interface
    """

    def __init__(self, host, url, token=None, secure=False, context=None):
        logging.Handler.__init__(self)
        self.host = host
        self.url = url
        self.token = token
        self.secure = secure
        self.context = context

    def __getSplunkEventDict(self, record):
        hostname = socket.gethostname()

        splunk_event = {
            "host": hostname,
            "source": record.module
        }

        return splunk_event

    def mapLogRecord(self, record):
        """

        """
        splunk_event = self.__getSplunkEventDict(record)

        splunk_event["event"] = {
            "message": record.msg,
            "level": record.levelname
        }
        return splunk_event

    def mapLogRecordWithFormat(self, record):
        splunk_event = self.__getSplunkEventDict(record)
        splunk_event["event"] = self.format(record)
        return splunk_event

    def setFormatter(self, fmt):
        super().setFormatter(fmt)

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Splunk server as a percent-encoded dictionary
        """
        try:
            import http.client, urllib.parse
            host = self.host
            if self.secure:
                h = http.client.HTTPSConnection(host, context=self.context)
            else:
                h = http.client.HTTPConnection(host)

            data = json.dumps(self.mapLogRecordWithFormat(record))

            h.putrequest('POST', self.url)
            h.putheader("Content-type",
                        "application/x-www-form-urlencoded")
            h.putheader("Content-length", str(len(data)))
            if self.token:
                s = 'Splunk ' + self.token
                h.putheader('Authorization', s)
            h.endheaders()

            h.send(data.encode('utf-8'))
            response = h.getresponse()
        except Exception:
            self.handleError(record)
