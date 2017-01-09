# Palette Splunk Logger

## What is Palette Splunk Logger?

It provides a `logging.Handler` implementation. It can be added to the any python logger like eg. `StreamHandler` or `RotatingFileHandler`.
It sends the `LogRecord`s to the [HTTP Event Collector](http://dev.splunk.com/view/event-collector/SP-CAAAE7F) of the Splunk server.

## How do I set up Palette Splunk Logger?

### Prerequisites

* Palette Splunk Logger is compatible with Python 3.5
* The hostname and the HTTP Event Collector URL of the Splunk Server
* An Access Token to the HTTP Event Collector

### Package installation

Either copy the `splunkloghandler.py` to your project or you may use the `setup.py` to create a package.

```bash
python setup.py sdist
pip install dist/palette-splunk-logger-1.0.0.tar.gz
```

### Usage

You may instantiate the `AsyncSplunkLogHandler` class and add the handler to the logger.

```python
import splunkloghandler

ACCESS_TOKEN = 'YOUR TOKEN'
API_DOMAIN = 'YOUR SPLUNK SERVER HOSTNAME'
API_URL = '/services/collector/event'

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

sh = splunkloghandler.AsyncSplunkLogHandler(host=API_DOMAIN,
                                            url=API_URL,
                                            token=ACCESS_TOKEN,
                                            secure=True)

sh.setLevel(logging.DEBUG)

logger.addHandler(sh)

logger.debug('debug message')
logger.info('info message')
logger.warning('warn message')
logger.error('error message')
logger.critical('critical message')
```

## Is Palette Splunk Logger supported?

Palette Splunk Logger is licensed under the MIT License. For professional support please contact developers@palette-software.com

**TODO: Clarify support part!**

Any bugs discovered should be filed in the [Palette Splunk Logger Git issue tracker](https://github.com/palette-software/palette-splunk-logger/issues) or contribution is more than welcome.
