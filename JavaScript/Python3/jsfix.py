#!/usr/bin/python3
'''
Parse and optionally modify JavaScript

adapted from sample script at
https://github.com/antlr/grammars-v4/tree/master/javascript/javascript/Python3
'''
import sys, os, logging  # pylint: disable=multiple-imports
#import threading  # for speeding up parsing if I find a likely path forward
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.TokenStreamRewriter import TokenStreamRewriter
from JavaScriptLexer import JavaScriptLexer
from JavaScriptParser import JavaScriptParser
from JavaScriptParserListener import JavaScriptParserListener
logging.disabled = lambda *args, **kwargs: logging.log(
    logging.NOTSET, *args, **kwargs)

LOWERCASE_LETTERS = tuple('abcdefghijklmnopqrstuvwxyz')
FIXUP = os.getenv('FIXUP', '')

class DowngradingJavascriptListener(JavaScriptParserListener):
    '''
    Subclass listener to change `let` to `var` and other primitivizations

    (Appending methods I removed but may need again)

    def visitErrorNode(self, node):
        logging.debug('Visiting error node: %s', node)

    def visitTerminal(self, node):
        logging.debug('Visiting terminal node: %s (%s)', node.symbol, node)
    '''
    rewriter = None

    def __init__(self, rewriter):
        '''
        associate a TokenStreamRewriter with this listener
        '''
        self.rewriter = rewriter

    def enterEveryRule(self, ctx):
        '''
        for analyzing how antlr4 works, with an eye to multithreading it
        '''
        text = ctx.getText()
        doctest_debug('enterEveryRule: ctx=%r (%d chars)',
                      snippet(text), len(text))

    def exitEveryRule(self, ctx):
        '''
        see docstring for enterEveryRule
        '''
        text = ctx.getText()
        doctest_debug('exitEveryRule: ctx=%r: (%d chars)',
                      snippet(text), len(text))

    def exitVariableDeclarationList(self, ctx):
        '''
        convert `let` and `const` to `var`
        '''
        logging.debug('ctx: %r', ctx.getText())
        modifier = ctx.varModifier()
        logging.debug('varModifier: %s', modifier)
        if FIXUP and modifier.getText() != 'var':
            self.rewriter.replaceRangeTokens(
                modifier.start, modifier.stop, 'var'
            )

    def exitArrowFunction(self, ctx):
        '''
        convert arrow function to old-style `function(){}`
        '''
        doctest_debug('ctx: %r', ctx.getText())
        if not FIXUP:
            return
        parameters = ctx.arrowFunctionParameters()
        body = ctx.arrowFunctionBody()
        arrow = ([child.symbol for child in ctx.children
                 if getattr(child, 'symbol', None) is not None
                 and child.symbol.text == '=>'] + [None])[0]
        doctest_debug('ctx.arrowFunctionParameters: %s: %s`',
                      parameters, show(parameters))
        doctest_debug('ctx.arrowFunctionBody: %s: %s',
                      body, show(body))
        #import pdb; pdb.set_trace()
        if arrow is not None:
            logging.disabled('arrow: %r: %s', arrow, show(arrow))
            self.rewriter.deleteToken(arrow)
        else:
            logging.error('no arrow was parsed, likely an antlr4 error node')
        if parameters.start.text != '(':
            # assume single unparenthesized arg
            self.rewriter.insertBeforeToken(parameters.start, 'function(')
            self.rewriter.insertAfterToken(parameters.stop, ')')
        else:
            # parenthesized arg(s)
            self.rewriter.insertBeforeToken(ctx.start, 'function')
        if body.start.text != '{':
            # assume single statement (for now)
            self.rewriter.insertBeforeToken(body.start, '{return ')
            self.rewriter.insertAfterToken(body.stop, '}')

def fixup(filedata):
    '''
    Parse data, fix for older browsers, and return modified source
    '''
    input_stream = InputStream(filedata)
    logging.debug('starting lexer phase')
    lexer = JavaScriptLexer(input_stream)
    logging.debug('getting tokens')
    tokens = CommonTokenStream(lexer)
    tokens.fill()
    tokenlist = list(t.text for t in tokens.tokens)
    if os.getenv('FIXUP_RETURN_TOKENS_ONLY'):
        logging.debug('returning list of token text')
        return tokenlist
    logging.debug('tokens: %s', snippet(str(tokenlist), 1024))
    logging.debug('starting parse phase')
    parser = JavaScriptParser(tokens)
    logging.debug('creating stream rewriter')
    rewriter = TokenStreamRewriter(tokens)
    logging.debug('instantiating downgrading listener')
    listener = DowngradingJavascriptListener(rewriter)
    logging.debug('creating parse tree')
    tree = parser.program()
    logging.debug('creating parse tree walker')
    walker = ParseTreeWalker()
    logging.debug('walking parse tree')
    walker.walk(listener, tree)
    logging.log(logging.NOTSET,  # change to logging.DEBUG to see this
        'parse tree: %s', tree.toStringTree(recog=parser))
    logging.debug('returning modified program text')
    return listener.rewriter.getDefaultText()

def show(something):
    '''
    a vars-alike that only shows things likely to be of interest
    '''
    candidates = {
        k: getattr(something, k) for k in dir(something)
        if k.startswith(LOWERCASE_LETTERS)
    }
    result = {}
    for k, v in candidates.items():
        if callable(v):
            result[k] = '(function)'
        else:
            result[k] = v
    return result

def snippet(string, maxlength=80):
    '''
    limit debugging output for long strings
    '''
    half = maxlength // 2
    if len(string) > maxlength:
        string = string[:half] + '...' + string[-half:]
    return string

def doctest_debug(msg, *args, **kwargs):
    # pylint: disable=unused-argument
    '''
    enable only for doctests
    '''

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s:jsfix:%(levelname)s:%(message)s',
        level=logging.DEBUG if __debug__ else logging.INFO,
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    if os.path.split(sys.argv[0])[1].startswith('doctest'):
        # pylint: disable=function-redefined
        def doctest_debug(msg, *args, **kwargs):
            '''
            verbose debugging only during doctests
            '''
            logging.debug(msg, *args, **kwargs)
    logging.debug('starting jsfix')
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r', encoding='utf-8') as infile:
                print(fixup(infile.read()))
    else:
        logging.error('Usage: %s filename.js', sys.argv[0])
        logging.warning('assuming data on stdin, ^D or ^C if necessary')
        print(fixup(sys.stdin.read()))
