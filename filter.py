#!/usr/bin/python3
'''
Using example internet-in-mirror.py from
https://docs.mitmproxy.org/stable/addons-examples/
'''
import os, re, json, socket, logging  # pylint: disable=multiple-imports
from mitmproxy import http

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.WARNING)
HOSTNAME = 'digital.redwoodcu.org'
FILES = os.path.join('storage', 'files')
USERAGENT = ('Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X) '
             'AppleWebKit/605.1.15 (KHTML, like Gecko) '
             'Version/12.1.2 Mobile/15E148'
)

def request(flow: http.HTTPFlow):
    '''
    filter requests
    '''
    if flow.request.host.endswith('gvt1.com'):
        logging.info('dropping spyware(?) junk from gvt1.com')
        flow.kill()
    logging.debug('request: %s', vars(flow.request))
    logging.info('flow.live: %s', flow.live)
    logging.info('request.method: %s', flow.request.method)
    for header, value in flow.request.headers.items():
        logging.info('header "%s": "%s"', header, value)

def response(flow: http.HTTPFlow) -> None:
    '''
    filter responses
    '''
    # pylint: disable=undefined-variable, too-many-branches
    if flow.request.host == HOSTNAME:
        savefile(
            os.path.join(FILES, *flow.request.path_components),
            flow.response.content
        )
        logging.info('flow.request.path: %s', flow.request.path)
        else:
            logging.info('Not filtering request for %s', flow.request.path)

def savefile(path, contents, binary=False, overwrite=False, retry_ok=True):
    '''
    write contents to disk under given path
    '''
    mode = 'wb' if binary else 'w'
    if os.path.exists(path) and not overwrite:
        logging.warning('not overwriting %s', path)
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # pylint: disable=unspecified-encoding
        with open(path, mode) as outfile:
            outfile.write(contents)
    except OSError as failed:
        logging.error('could not write %s: %s', path, failed)
    except TypeError as failed:
        logging.error('could not write contents of %s: %s', path, failed)
        if retry_ok:
            savefile(path, contents, True, True, False)
            logging.info('wrote %s successfully as bytes', path)

# vim: set tabstop=4 expandtab shiftwidth=4 softtabstop=4
