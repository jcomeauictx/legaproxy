#!/usr/bin/python3
'''
Parse and log JavaScript

Mostly a copy of jsfix.py but with the editing parts removed

Purpose is to check if the parse errors are due to the editing or antlr itself
'''
import sys, threading, logging  # pylint: disable=multiple-imports
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.TokenStreamRewriter import TokenStreamRewriter
from JavaScriptLexer import JavaScriptLexer
from JavaScriptParser import JavaScriptParser
from JavaScriptParserListener import JavaScriptParserListener

LOWERCASE_LETTERS = tuple('abcdefghijklmnopqrstuvwxyz')

class WalkingJavascriptListener(JavaScriptParserListener):
    '''
    Subclass listener to change `let` to `var` and other primitivizations
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
        logging.debug('enterEveryRule: ctx=%s: %s', ctx, show(ctx))

    def exitEveryRule(self, ctx):
        '''
        see docstring for enterEveryRule
        '''
        logging.debug('exitEveryRule: ctx=%s: %s', ctx, show(ctx))

def walk(filedata):
    '''
    Parse data and log
    '''
    input_stream = InputStream(filedata)
    lexer = JavaScriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = JavaScriptParser(tokens)
    rewriter = TokenStreamRewriter(tokens)
    listener = WalkingJavascriptListener(rewriter)
    tree = parser.program()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)
    logging.log(logging.NOTSET,  # change to logging.DEBUG to see this
        'parse tree: %s', tree.toStringTree(recog=parser))
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            with open(filename, 'r', encoding='utf-8') as infile:
                print(walk(infile.read()))
    else:
        logging.error('Usage: %s filename.js', sys.argv[0])
        logging.warning('assuming data on stdin, ^D or ^C if necessary')
        print(walk(sys.stdin.read()))
