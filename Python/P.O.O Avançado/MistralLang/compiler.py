"""
Mistral Compiler
----------------
Translates Mistral source code into Python.
Now supports single-line comments starting with //.
"""

import sys
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union, Any

# ----------------------------------------------------------------------
# Token definitions
# ----------------------------------------------------------------------


class TokenType(Enum):
    # Keywords
    SAY = 'say'
    FUN = 'fun'
    IF = 'if'
    ELSE = 'else'
    WHILE = 'while'
    RETURN = 'return'
    TRUE = 'true'
    FALSE = 'false'
    AND = 'and'
    OR = 'or'
    NOT = 'not'
    # Literals
    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    # Operators
    PLUS = '+'
    MINUS = '-'
    STAR = '*'
    SLASH = '/'
    PERCENT = '%'
    EQ = '=='
    NEQ = '!='
    LT = '<'
    GT = '>'
    LE = '<='
    GE = '>='
    ASSIGN = '='
    LPAREN = '('
    RPAREN = ')'
    LBRACE = '{'
    RBRACE = '}'
    COMMA = ','
    SEMICOLON = ';'
    # Special
    EOF = 'EOF'


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int

# ----------------------------------------------------------------------
# Lexer (scanner) with comment support
# ----------------------------------------------------------------------


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1

    def scan_tokens(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def scan_token(self):
        c = self.advance()
        if c.isspace():
            if c == '\n':
                self.line += 1
                self.column = 1
            # ignore other whitespace
            return
        # Single-character tokens
        if c == '+':
            self.add_token(TokenType.PLUS)
        elif c == '-':
            self.add_token(TokenType.MINUS)
        elif c == '*':
            self.add_token(TokenType.STAR)
        elif c == '/':
            # Could be division or comment
            if self.match('/'):  # // comment
                # consume until end of line
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
                # don't add token; comment is ignored
            else:
                self.add_token(TokenType.SLASH)
        elif c == '%':
            self.add_token(TokenType.PERCENT)
        elif c == '(':
            self.add_token(TokenType.LPAREN)
        elif c == ')':
            self.add_token(TokenType.RPAREN)
        elif c == '{':
            self.add_token(TokenType.LBRACE)
        elif c == '}':
            self.add_token(TokenType.RBRACE)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == '=':
            if self.match('='):
                self.add_token(TokenType.EQ)
            else:
                self.add_token(TokenType.ASSIGN)
        elif c == '!':
            if self.match('='):
                self.add_token(TokenType.NEQ)
            else:
                self.error("Unexpected character '!'")
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.LE)
            else:
                self.add_token(TokenType.LT)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.GE)
            else:
                self.add_token(TokenType.GT)
        elif c == '"':
            self.string()
        else:
            # Identifiers or keywords
            if c.isalpha() or c == '_':
                while self.peek().isalnum() or self.peek() == '_':
                    self.advance()
                text = self.source[self.start:self.current]
                # Check keywords
                token_type = {
                    'say': TokenType.SAY,
                    'fun': TokenType.FUN,
                    'if': TokenType.IF,
                    'else': TokenType.ELSE,
                    'while': TokenType.WHILE,
                    'return': TokenType.RETURN,
                    'true': TokenType.TRUE,
                    'false': TokenType.FALSE,
                    'and': TokenType.AND,
                    'or': TokenType.OR,
                    'not': TokenType.NOT,
                }.get(text, TokenType.IDENTIFIER)
                self.add_token(token_type)
            elif c.isdigit():
                while self.peek().isdigit():
                    self.advance()
                self.add_token(TokenType.NUMBER)
            else:
                self.error(f"Unexpected character '{c}'")

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()
        if self.is_at_end():
            self.error("Unterminated string")
            return
        # closing "
        self.advance()
        self.add_token(TokenType.STRING)

    def add_token(self, token_type: TokenType):
        lexeme = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, lexeme, self.line, self.start+1))

    def error(self, message: str):
        print(
            f"Lexer error at line {self.line}, column {self.column}: {message}", file=sys.stderr)
        sys.exit(1)

# ----------------------------------------------------------------------
# Parser (recursive descent) - unchanged
# ----------------------------------------------------------------------


class ParseError(Exception):
    pass


class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


@dataclass
class SayStatement(ASTNode):
    expression: ASTNode


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: Optional[List[ASTNode]]


@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: List[ASTNode]


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode]


@dataclass
class ExpressionStatement(ASTNode):
    expression: ASTNode


@dataclass
class Block(ASTNode):
    statements: List[ASTNode]


@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]


@dataclass
class VariableDeclaration(ASTNode):
    name: str
    initializer: Optional[ASTNode]


@dataclass
class Binary(ASTNode):
    left: ASTNode
    operator: TokenType
    right: ASTNode


@dataclass
class Unary(ASTNode):
    operator: TokenType
    right: ASTNode


@dataclass
class Literal(ASTNode):
    value: Any


@dataclass
class Variable(ASTNode):
    name: str


@dataclass
class Call(ASTNode):
    callee: ASTNode
    arguments: List[ASTNode]


@dataclass
class Grouping(ASTNode):
    expression: ASTNode


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        statements = []
        while not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    # ---------- Helpers ----------
    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def match(self, *types: TokenType) -> bool:
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        raise self.error(self.peek(), message)

    def error(self, token: Token, message: str) -> ParseError:
        print(
            f"Parse error at line {token.line}, column {token.column}: {message}", file=sys.stderr)
        return ParseError()

    # ---------- Grammar rules ----------
    def declaration(self) -> Optional[ASTNode]:
        try:
            if self.match(TokenType.FUN):
                return self.function_declaration()
            if self.match(TokenType.IDENTIFIER):
                # Could be assignment or variable declaration
                name = self.previous().lexeme
                if self.match(TokenType.ASSIGN):
                    expr = self.expression()
                    self.consume(TokenType.SEMICOLON,
                                 "Expect ';' after variable declaration.")
                    return VariableDeclaration(name, expr)
                else:
                    # it's an expression statement beginning with identifier
                    # rewind? easier: we treat identifier as start of expression
                    self.current -= 1  # go back
                    return self.statement()
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def function_declaration(self) -> FunctionDeclaration:
        name = self.consume(TokenType.IDENTIFIER,
                            "Expect function name.").lexeme
        self.consume(TokenType.LPAREN, "Expect '(' after function name.")
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters.append(self.consume(
                TokenType.IDENTIFIER, "Expect parameter name.").lexeme)
            while self.match(TokenType.COMMA):
                parameters.append(self.consume(
                    TokenType.IDENTIFIER, "Expect parameter name.").lexeme)
        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")
        self.consume(TokenType.LBRACE, "Expect '{' before function body.")
        body = self.block_statements()
        self.consume(TokenType.RBRACE, "Expect '}' after function body.")
        return FunctionDeclaration(name, parameters, body)

    def statement(self) -> ASTNode:
        if self.match(TokenType.SAY):
            return self.say_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.LBRACE):
            # block
            statements = self.block_statements()
            self.consume(TokenType.RBRACE, "Expect '}' after block.")
            return Block(statements)
        return self.expression_statement()

    def say_statement(self) -> SayStatement:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return SayStatement(expr)

    def if_statement(self) -> IfStatement:
        condition = self.expression()
        self.consume(TokenType.LBRACE, "Expect '{' after if condition.")
        then_branch = self.block_statements()
        self.consume(TokenType.RBRACE, "Expect '}' after then branch.")
        else_branch = None
        if self.match(TokenType.ELSE):
            if self.match(TokenType.LBRACE):
                else_branch = self.block_statements()
                self.consume(TokenType.RBRACE, "Expect '}' after else branch.")
            else:
                # single statement after else? For simplicity, we require block.
                raise self.error(self.peek(), "Expected '{' after else.")
        return IfStatement(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStatement:
        condition = self.expression()
        self.consume(TokenType.LBRACE, "Expect '{' after while condition.")
        body = self.block_statements()
        self.consume(TokenType.RBRACE, "Expect '}' after while body.")
        return WhileStatement(condition, body)

    def return_statement(self) -> ReturnStatement:
        if self.check(TokenType.SEMICOLON):
            value = None
        else:
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return ReturnStatement(value)

    def block_statements(self) -> List[ASTNode]:
        statements = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return statements

    def expression_statement(self) -> ExpressionStatement:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStatement(expr)

    # ---------- Expressions (precedence climbing) ----------
    def expression(self) -> ASTNode:
        return self.assignment()

    def assignment(self) -> ASTNode:
        expr = self.logical_or()
        if self.match(TokenType.ASSIGN):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, Variable):
                # treat as variable declaration/assignment
                return VariableDeclaration(expr.name, value)
            raise self.error(equals, "Invalid assignment target.")
        return expr

    def logical_or(self) -> ASTNode:
        expr = self.logical_and()
        while self.match(TokenType.OR):
            operator = self.previous().type
            right = self.logical_and()
            expr = Binary(expr, operator, right)
        return expr

    def logical_and(self) -> ASTNode:
        expr = self.equality()
        while self.match(TokenType.AND):
            operator = self.previous().type
            right = self.equality()
            expr = Binary(expr, operator, right)
        return expr

    def equality(self) -> ASTNode:
        expr = self.comparison()
        while self.match(TokenType.EQ, TokenType.NEQ):
            operator = self.previous().type
            right = self.comparison()
            expr = Binary(expr, operator, right)
        return expr

    def comparison(self) -> ASTNode:
        expr = self.term()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            operator = self.previous().type
            right = self.term()
            expr = Binary(expr, operator, right)
        return expr

    def term(self) -> ASTNode:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().type
            right = self.factor()
            expr = Binary(expr, operator, right)
        return expr

    def factor(self) -> ASTNode:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.previous().type
            right = self.unary()
            expr = Binary(expr, operator, right)
        return expr

    def unary(self) -> ASTNode:
        if self.match(TokenType.MINUS, TokenType.NOT):
            operator = self.previous().type
            right = self.unary()
            return Unary(operator, right)
        return self.call()

    def call(self) -> ASTNode:
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                # function call
                arguments = []
                if not self.check(TokenType.RPAREN):
                    arguments.append(self.expression())
                    while self.match(TokenType.COMMA):
                        arguments.append(self.expression())
                self.consume(TokenType.RPAREN, "Expect ')' after arguments.")
                expr = Call(expr, arguments)
            else:
                break
        return expr

    def primary(self) -> ASTNode:
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.NUMBER):
            return Literal(int(self.previous().lexeme))
        if self.match(TokenType.STRING):
            # strip quotes
            s = self.previous().lexeme[1:-1]
            return Literal(s)
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous().lexeme)
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expect ')' after expression.")
            return Grouping(expr)
        raise self.error(self.peek(), "Expect expression.")

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            if self.peek().type in {TokenType.FUN, TokenType.IF, TokenType.WHILE, TokenType.SAY, TokenType.RETURN}:
                return
            self.advance()

# ----------------------------------------------------------------------
# Code Generator (Python) - unchanged
# ----------------------------------------------------------------------


class Generator:
    def __init__(self):
        self.output = []
        self.indent_level = 0

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level -= 1

    def emit(self, line: str):
        self.output.append("    " * self.indent_level + line)

    def generate(self, node: ASTNode) -> str:
        self.output = []
        self.visit(node)
        return "\n".join(self.output)

    def visit(self, node: ASTNode):
        method = f"visit_{type(node).__name__}"
        getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node):
        raise NotImplementedError(f"No visit method for {type(node).__name__}")

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_SayStatement(self, node: SayStatement):
        self.emit(f"print({self.expression(node.expression)})")

    def visit_IfStatement(self, node: IfStatement):
        self.emit(f"if {self.expression(node.condition)}:")
        self.indent()
        for stmt in node.then_branch:
            self.visit(stmt)
        self.dedent()
        if node.else_branch:
            self.emit("else:")
            self.indent()
            for stmt in node.else_branch:
                self.visit(stmt)
            self.dedent()

    def visit_WhileStatement(self, node: WhileStatement):
        self.emit(f"while {self.expression(node.condition)}:")
        self.indent()
        for stmt in node.body:
            self.visit(stmt)
        self.dedent()

    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.value:
            self.emit(f"return {self.expression(node.value)}")
        else:
            self.emit("return")

    def visit_Block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_FunctionDeclaration(self, node: FunctionDeclaration):
        params = ", ".join(node.params)
        self.emit(f"def {node.name}({params}):")
        self.indent()
        for stmt in node.body:
            self.visit(stmt)
        self.dedent()

    def visit_VariableDeclaration(self, node: VariableDeclaration):
        if node.initializer:
            self.emit(f"{node.name} = {self.expression(node.initializer)}")
        else:
            self.emit(f"{node.name} = None")

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        # expression as statement (like function call)
        self.emit(f"{self.expression(node.expression)}")

    def expression(self, node: ASTNode) -> str:
        if isinstance(node, Literal):
            return repr(node.value)
        if isinstance(node, Variable):
            return node.name
        if isinstance(node, Binary):
            left = self.expression(node.left)
            right = self.expression(node.right)
            op = {
                TokenType.PLUS: '+',
                TokenType.MINUS: '-',
                TokenType.STAR: '*',
                TokenType.SLASH: '/',
                TokenType.PERCENT: '%',
                TokenType.EQ: '==',
                TokenType.NEQ: '!=',
                TokenType.LT: '<',
                TokenType.GT: '>',
                TokenType.LE: '<=',
                TokenType.GE: '>=',
                TokenType.AND: 'and',
                TokenType.OR: 'or',
            }.get(node.operator, str(node.operator))
            return f"({left} {op} {right})"
        if isinstance(node, Unary):
            right = self.expression(node.right)
            op = {
                TokenType.MINUS: '-',
                TokenType.NOT: 'not ',
            }.get(node.operator, str(node.operator))
            return f"({op}{right})"
        if isinstance(node, Call):
            callee = self.expression(node.callee)
            args = ", ".join(self.expression(arg) for arg in node.arguments)
            return f"{callee}({args})"
        if isinstance(node, Grouping):
            return f"({self.expression(node.expression)})"
        raise ValueError(f"Unknown expression node: {type(node)}")

# ----------------------------------------------------------------------
# Public interface
# ----------------------------------------------------------------------


def compile_mistral(source: str) -> str:
    """Compile Mistral source code to Python source code."""
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = Generator()
    return generator.generate(ast)


def execute_mistral(source: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Compile and execute Mistral code in a subprocess (safer)."""
    python_code = compile_mistral(source)
    # Run in a subprocess
    return subprocess.run(
        [sys.executable, "-c", python_code],
        capture_output=capture_output,
        text=True
    )


if __name__ == "__main__":
    # Simple command-line interface
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <file.mistral>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        src = f.read()
    result = execute_mistral(src, capture_output=True)
    print("--- stdout ---")
    print(result.stdout)
    print("--- stderr ---")
    print(result.stderr)
