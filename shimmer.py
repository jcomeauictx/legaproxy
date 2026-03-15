#!/usr/bin/python3
'''
insert shim code into webpage

proof of concept which may turn out to be production code
'''
from html.parser import HTMLParser
import sys, os, fileinput, logging  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

class ShimmerParser(HTMLParser):
    '''
    parser that inserts a script tag with shim code
    '''
    parts = []
    tags = []
    
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.parts.append(tag)

    def handle_endtag(self, tag):
        while self.tags[-1] != tag:
            logging.debug('popping unexpected tag %s', self.tags.pop(-1))
        self.tags.pop(-1)

def shim():
    '''
    add shim code to file or stdin
    '''
    parser = ShimmerParser()
    for line in fileinput.input(encoding='utf-8'):
        parser.feed(line)
    logging.debug('parser.tags: %s', parser.tags)
    print(''.join(parser.parts))

if __name__ == '__main__':
    shim()
