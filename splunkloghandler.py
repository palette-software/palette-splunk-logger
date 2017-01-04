import json
import logging
import logging.handlers
import socket
import queue
import threading
from datetime import datetime, timedelta

StopTimeoutSeconds = 10
BatchSize = 100


class SplunkLogHandler(logging.Handler):
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
            "host": hostname
        }

        return splunk_event

    def mapLogRecordWithFormat(self, record):
        splunk_event = self.__getSplunkEventDict(record)
        splunk_event["event"] = self.format(record)
        return splunk_event

    def setFormatter(self, fmt):
        super().setFormatter(fmt)

    def prepare(self, record):
        data = json.dumps(self.mapLogRecordWithFormat(record))
        return data

    def send(self, data):
        if data is None or data == "":
            return None

        import http.client
        host = self.host
        if self.secure:
            h = http.client.HTTPSConnection(host, context=self.context)
        else:
            h = http.client.HTTPConnection(host)

        h.putrequest('POST', self.url)
        h.putheader("Content-type",
                    "application/x-www-form-urlencoded")
        h.putheader("Content-length", str(len(data)))
        if self.token:
            s = 'Splunk ' + self.token
            h.putheader('Authorization', s)
        h.endheaders()

        h.send(data.encode('utf-8'))
        return h.getresponse()

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Splunk server as a percent-encoded dictionary
        """
        try:
            self.send(self.prepare(record))
        except Exception:
            self.handleError(record)


class AsyncSplunkLogHandler(SplunkLogHandler):
    _sentinel = None

    def __init__(self, host, url, token=None, secure=False, context=None):
        """
        Initialise an instance with the specified queue and
        handler.
        """
        super().__init__(host, url, token, secure, context)
        self.queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = None

        self.start()

    def _monitor(self):
        """
        Monitor the queue for records, and ask the handler
        to deal with them.

        This method runs on a separate, internal thread.
        The thread will terminate if it sees a sentinel object in the queue.
        """
        payload = None
        stop_noticed = None
        while True:
            try:
                if self._stop.is_set():
                    if self.queue.empty():
                        break

                    # Store when we first met the stop sign so that we can time out later
                    if stop_noticed is None:
                        stop_noticed = datetime.now()

                    # Check if we have reached the timeout period
                    if datetime.now() - stop_noticed > timedelta(seconds=StopTimeoutSeconds):
                        break

                if payload is None:
                    payload = self.dequeue(True)

                # Todo check response
                response = self.send(payload)

                payload = None
            except Exception as err:
                pass

    def close(self):
        self.stop()
        super().close()

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue, preparing it for pickling first.
        """
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            self.handleError(record)

    def enqueue(self, record):
        self.queue.put_nowait(record)

    def dequeue(self, block):
        payload = ""
        count = 0
        while count <= BatchSize:
            try:
                message = self.queue.get(block)
                block = False
                if message is not self._sentinel:
                    payload += message
                    count += 1
            except queue.Empty:
                break

        return payload

    def enqueue_sentinel(self):
        self.queue.put_nowait(self._sentinel)

    def start(self):
        """
        Start the listener.

        This starts up a background thread to monitor the queue for
        LogRecords to process.
        """
        self._thread = t = threading.Thread(target=self._monitor)
        t.setDaemon(True)
        t.start()

    def stop(self):
        """
        Stop the listener.

        This asks the thread to terminate, and then waits for it to do so.
        Note that if you don't call this before your application exits, there
        may be some records still left on the queue, which won't be processed.
        """
        self._stop.set()
        self.enqueue_sentinel()
        self._thread.join()
        self._thread = None
