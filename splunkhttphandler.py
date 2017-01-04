import json
import logging
import logging.handlers
import socket
import queue
import threading


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

    def prepare(self, record):
        data = json.dumps(self.mapLogRecordWithFormat(record))
        return data

    def send(self, data):
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


class AsyncSplunkHTTPHandler(SplunkHTTPHandler):
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
        while not self._stop.isSet():
            try:
                record = self.dequeue(True)
                if record is self._sentinel:
                    break
                self.send(record)
            except queue.Empty:
                pass
        # There might still be records in the queue.
        while True:
            try:
                record = self.dequeue(False)
                if record is self._sentinel:
                    break
                self.send(record)
            except queue.Empty:
                break

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
        """
        Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method if you want to use blocking, timeouts or custom queue
        implementations.
        """
        self.queue.put_nowait(record)

    def dequeue(self, block):
        """
        Dequeue a record and return it, optionally blocking.

        The base implementation uses get. You may want to override this method
        if you want to use timeouts or work with custom queue implementations.
        """
        return self.queue.get(block)

    def enqueue_sentinel(self):
        """
        This is used to enqueue the sentinel record.

        The base implementation uses put_nowait. You may want to override this
        method if you want to use timeouts or work with custom queue
        implementations.
        """
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
