#!/usr/bin/python3
'''
mitmdump filter to test delayed responses
'''
import os, logging, time  # pylint: disable=multiple-imports
from http import HTTPStatus
from posixpath import split, sep
from mitmproxy import http, ctx

MIMETYPES = {
    '.html': 'text/html',
    '.png': 'image/png'
}

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

def request(flow: http.HTTPFlow) -> None:
    '''
    capture and modify http.Request object
    '''
    logging.info('request received: %s', flow.request.url)
    directory, filename = split(flow.request.path.lstrip(sep))
    if flow.request.host.endswith('gvt1.com'):
        logging.info('dropping google spyware')
        flow.kill()
    elif flow.request.host == 'mitm.it':
        logging.info('passing on request to mitm.it')
    elif directory == '' and filename in ('', 'index.html', 'favicon.ico'):
        logging.info('passing request on to server')
    elif directory == 'mitm' and os.path.exists(filename):
        logging.info('serving file %s', filename)
        mimetype = MIMETYPES.get(os.path.splitext(filename)[1], 'text/plain')
        flow.response = http.Response.make(
            HTTPStatus.OK,
            read(filename),
            {'Content-Type': mimetype}
        )
    elif directory == 'mitm' and filename == 'shutdown':
        logging.warning('shutting down MITM')
        flow.response = http.Response.make(
            HTTPStatus.OK,
            b'shutting down MITM',
            {'Content-Type': 'text/plain'}
        )
        ctx.master.shutdown()
    else:
        logging.warning('dropping unexpected request %s', flow.request.url)
        flow.kill()

async def response(flow: http.HTTPFlow) -> None:
    '''
    capture and modify http.Response object
    '''
    logging.info('response received: %s', flow.request.url)
    directory, filename = split(flow.request.path.lstrip(sep))
    filename = filename.split('?')[0]  # make sure any querystring is gone
    logging.debug('received request for directory %s, filename %s',
                  directory, filename)
    if directory == 'mitm' and filename.endswith('.png'):
        delay = int(flow.request.query.get('delay', '0').rstrip('s'))
        logging.info('delaying response for %s by %d seconds', filename, delay)
        time.sleep(delay)
    elif directory == '' and filename in ('', 'index.html'):
        logging.info('filter: %s', __file__)
        flow.response.content = read(__file__.replace('.py', '.html'))

def read(filename):
    '''
    read and return file contents as bytes
    '''
    with open(filename, 'rb') as infile:
        return infile.read()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
