#!/usr/bin/python3
'''
mitmdump filter to test delayed responses
'''
import logging, posixpath, re  # pylint: disable=multiple-imports
import mitmproxy

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

def request(flow: http.HTTPFlow):
    logging.debug('request received: %s', flow.request.url)
    filename = flow.request.path.lstrip('/')
    if os.path.exists(filename):
        logging.debug('serving file %s', filename)
async def response(flow: http.HTTPFlow) -> None:
    logging.debug('response received: %s', flow.request.url)
    filename = posixpath.basename(flow.request.url)
    if filename.endswith('.png'):
        logging.debug('delaying response for %s', filename)
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
