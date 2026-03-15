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
        '''
        handle start tag
        '''
        logging.debug('handling start tag %s', tag)
        self.tags.append(tag)
        self.parts.append('<' + tag + expand_attrs(attrs) + '>')

    def handle_endtag(self, tag):
        '''
        handle end tag
        '''
        logging.debug('handling end tag %s', tag)
        while self.tags[-1] != tag:
            popped = self.tags.pop(-1)
            logging.debug('popped unexpected tag %s', popped)
        self.tags.pop(-1)
        self.parts.append('</' + tag + '>')

    def handle_startendtag(self, tag, attrs):
        '''
        handle xml <tag/>
        '''
        logging.debug('handling start end tag %s', tag)
        self.parts.append('<' + tag + expand_attrs(attrs) + '/>')

    def handle_other(self, other):
        '''
        handle other stuff like data, comment, charref
        '''
        logging.debug('handling %s',  __name__[len('handle_'):])
        if __name__ == 'handle_comment':
            other = '<!-- ' + other + '-->'
        self.parts.append(other)

    handle_charref = handle_comment = handle_data = handle_decl \
        = handle_entityref = handle_pi = handle_other

def shim(filename=None):
    '''
    add shim code to file or stdin
    '''
    with open(filename, 'r', encoding='utf-8') \
            if filename not in [None, '-'] \
            else sys.stdin as infile:
        parser = ShimmerParser()
        for line in infile:
            parser.feed(line)
        logging.debug('final parser.tags: %s', parser.tags)
        print(''.join(parser.parts))

def expand_attrs(attrs):
    '''
    expand tag attributes

    >>> expand_attrs({'class': 'bleah', 'id': 'blargh', 'spam': 'spam spam'})
    'class="bleah" id="blargh" spam="spam spam"'
    '''
    result = ''
    for key, value in attrs:
        result += key + '="' + value + '"'
    return ' ' + result if result else result

if __name__ == '__main__':
    shim(*sys.argv[1:])
