#!/usr/bin/python3
'''
fast lexer for javascript

sacrifice completeness for speed
'''
import sys, logging, string, re  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
WHITESPACE = tuple('\t\v\f \xa0\ufeff')  # may need to add more
ENDLINE = tuple('\n\r\u2028\u2029')
COMMENTS = {
    '//': ENDLINE,
    '#!': ENDLINE,  # only valid at start of script, but lexer needn't care
    '/*': '*/',
}
COMMENT_START = tuple(COMMENTS)
ID_START = tuple(string.ascii_letters + '$_')
ID_CONTINUE = ID_START + tuple(string.digits)
ID = re.compile('[' + ''.join(ID_START) + '][' +
                ''.join(ID_CONTINUE) + ']*')

def jslex(string):
    '''
    break input string into lexical elements

    //developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar
    '''
    tokens = []

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r') as infile:
                print(jslex(infile.read()))
    else:
        logging.warn('Assuming data on stdin, ^D or ^C if none')
        print(jslex(sys.stdin.read()))
