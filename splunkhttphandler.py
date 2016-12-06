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
        event = record.__dict__
        splunk_event = {
            "host": hostname,
            "source": event['module']
        }

        return splunk_event

    def mapLogRecord(self, record):
        """

        """
        splunk_event = self.__getSplunkEventDict(record)

        event = record.__dict__

        splunk_event["event"] = {
            "message": event['msg'],
            "level": event['levelname']
        }
        return splunk_event

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
            data = json.dumps(self.mapLogRecord(record))
            h.putrequest('POST', self.url)
            # support multiple hosts on one IP address...
            # need to strip optional :port from host, if present
            i = host.find(":")
            if i >= 0:
                host = host[:i]
            h.putheader("Host", host)
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
