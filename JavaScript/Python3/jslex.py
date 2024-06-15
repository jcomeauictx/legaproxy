#!/usr/bin/python3
'''
fast lexer for javascript

sacrifice completeness for speed

see references JavaScriptLexer.g4 and
developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar

NOTES:
    iff="if and only if"
    nullish="null or undefined"
'''
import sys, logging, re  # pylint: disable=multiple-imports
from re import escape as esc
from string import ascii_letters, digits
from collections import OrderedDict
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
WHITESPACE = '\t\v\f \xa0\ufeff'  # may need to add more
ENDLINE = '\n\r\u2028\u2029'
ZEROWIDTH = tuple('\u200c\u200d')  # non-joiner and joiner
# parsing comments is problematic, because comment delimiters are meaningless
# inside strings, and strings need not be parsed inside comments.
# NOTE: T_ versions of following are for post-lexing of templates
COMMENT = OrderedDict([
    ('/*', r'/\*.*?\*/'),
    ('//', '//[^' + ENDLINE + ']*[' + ENDLINE + ']+'),
    # shebang comment only valid at start of script, but lexer needn't care
    ('#!', '#![^' + ENDLINE + ']*[' + ENDLINE + ']+'),
])
STRING = OrderedDict([
    ('"', '"'),
    ("'", "'"),
    ('`', '`'),
])
GROUP = OrderedDict([
    ('{', '}'),
    ('[', ']'),
    ('(', ')'),
])
NUMBER = OrderedDict([
    # let any preceding sign be handled by the parser
    ('integer', '(?:0[BbOoXx])?[0-9A-Fa-f]+[n]?'),
    ('float', '(?:[.][0-9]+|[0-9]+.[0-9]*)(?:[Ee][+-]?[0-9]+)?'),
])
OPERATOR = [
    '>>>=',  # right shift logical assign
    '>>=',   # right shift arithmetic assign
    '=>',    # arrow
    '<<=',   # left shift assign
    '??=',   # nullish coalescing assign
    '**=',   # power assign
    '===',   # identity equals
    '>>>',   # right shift logical
    '!==',   # identity not equals
    '...',   # ellipsis ("spread" or "rest" syntax, like Python splat (*))
    '|=',    # bit-or assign
    '^=',    # bit-xor assign
    '*=',    # multiply assign
    '/=',    # divide assign
    '%=',    # modulus assign
    '+=',    # plus assign
    '-=',    # minus assign
    '&=',    # bit-and assign
    '?.',    # optional chaining (access property if LH not nullish)
    '||',    # logical or
    '&&',    # logical and
    '??',    # nullish coalesce (LH becomes RH iff LH is nullish)
    '++',    # increment
    '--',    # decrement
    '>>',    # right shift arithmetic
    '<<',    # left shift
    '<=',    # less than assign
    '>=',    # greater than assign
    '==',    # equals
    '!=',    # not equals
    '**',    # power
    '?',     # question ("if" as part of ternary operator `a ? b : c`)
    '|',     # bit-or
    '^',     # bit-xor
    '&',     # bit-and
    '~',     # bit-not
    '%',     # modulus
    '#',     # hash (precedes private field identifier in class definition)
    '>',     # greater than
    '<',     # less than
    '*',     # multiply
    '/',     # divide
    '+',     # plus
    '-',     # minus
    '=',     # assign
    '.',     # dot (property accessor, `a.b`, also expressed `a["b"]`)
    '!',     # not
    ':',     # colon
    ',',     # comma
    ';',     # semicolon
]
T_OPERATOR = OPERATOR + ['${'] + list(GROUP.keys()) + list(GROUP.values())
ID_START = tuple(ascii_letters + '$_')
ID_CONTINUE = ID_START + tuple(digits) + ZEROWIDTH
IDS = '[' + ''.join(ID_START) + '][' + ''.join(ID_CONTINUE) + ']*'
# NOTE: keywords are also matched by IDS
OPERATORS = '|'.join([esc(op) for op in OPERATOR])
T_OPERATORS = '|'.join([esc(op) for op in T_OPERATOR])
GROUPS = '|'.join(['|'.join([esc(k), esc(v)]) for k, v in GROUP.items()])
STRINGS = r'''([%s]).*?(?<!\\)(?:\\\\)*\2''' % ''.join(STRING)
T_STRINGS = r'''([%s]).*?(?<!\\)(?:\\\\)*\2''' % ''.join(tuple(STRING)[:2])
REGEXES = r'(?<=[!=(])/.*?(?<!\\)(?:\\\\)*/[dgimsuvy]?'
COMMENTS = '|'.join(COMMENT.values())
WHITESPACES = '[' + ''.join(WHITESPACE + ENDLINE) + ']+'
NUMBERS = '|'.join(NUMBER.values())
SPLITTER = re.compile('(' + '|'.join(
    [COMMENTS, REGEXES, STRINGS, OPERATORS, GROUPS, IDS, NUMBERS, WHITESPACES]
) + ')')
T_SPLITTER = re.compile('(' + '|'.join(
    [REGEXES, T_STRINGS, T_OPERATORS, IDS, NUMBERS, WHITESPACES]
) + ')')

def jslex(string):
    '''
    break input string into lexical elements

    //developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar
    '''
    logging.debug('OPERATORS: %r', OPERATORS)
    tokens = []
    ignored = ('', None) + tuple(STRING)
    tokens.extend([token for token in SPLITTER.split(string)
                  if token not in ignored] + ['<EOF>'])
    for index in range(len(tokens)):
        token = tokens[index]
        if token.startswith('`'):
            logging.debug('template: %s', token)
            tokens[index] = [t for t in T_SPLITTER.split(token)
                             if t not in ignored]
    return tokens

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r', encoding='utf-8') as infile:
                print(jslex(infile.read()))
    else:
        logging.warning('Assuming data on stdin, ^D or ^C if none')
        print(jslex(sys.stdin.read()))
