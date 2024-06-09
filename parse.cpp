/* from codeproject.com/Articles/5308882/
 * ANTLR-Parsing-and-Cplusplus-Part-1-Introduction */
#include <iostream>
#include "antlr4-runtime.h"
#include "JavaScriptLexer.h"
#include "JavaScriptParser.h"

int main(int argc, const char* argv[]) {

    // Provide the input text in a stream
    antlr4::CharStream input("6*(2+3)");
    
    // Create a lexer from the input
    JavaScriptLexer lexer(&input);
    
    // Create a token stream from the lexer
    antlr4::CommonTokenStream tokens(&lexer);
    
    // Create a parser from the token stream
    JavaScriptParser parser(&tokens);    

    // Display the parse tree
    std::cout << parser.program()->toStringTree() << std::endl;
    return 0;
}
