#!/usr/bin/python3
'''
mitmdump filter to test delayed responses
'''
import logging, re  # pylint: disable=multiple-imports
from http import HTTPStatus
from posixpath import basename, dirname, split, sep
from mitmproxy import http, ctx

MIMETYPES = {
    '.html': 'text/html',
    '.png': 'image/png'
}

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

def request(flow: http.HTTPFlow) -> None:
    logging.debug('request received: %s', flow.request.url)
    dirname, filename = split(flow.request.path.lstrip(sep))
    if dirname == 'mitm' and os.path.exists(filename):
        logging.debug('serving file %s', filename)
        mimetype = MIMETYPES.get(os.path.splitext(filename)[1], 'text/plain')
        flow.response = http.Response.make(
            HTTPStatus.OK,
            read(filename),
            {'Content-Type': mimetype}
        )
    elif dirname == 'mitm' and filename == 'shutdown':
        logging.warning('shutting down MITM')
        ctx.master.shutdown()

async def response(flow: http.HTTPFlow) -> None:
    logging.debug('response received: %s', flow.request.url)
    dirname, filename = split(flow.request.path.lstrip(sep))
    if filename.endswith('.png'):
        delay = int(flow.request.query.get('delay', '0').rstrip('s'))
        logging.debug('delaying response for %s by %d seconds', filename, delay)
        time.sleep(delay)

def read(filename):
    '''
    read and return file contents as bytes
    '''
    with open(filename, 'rb') as infile:
        return infile.read()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
