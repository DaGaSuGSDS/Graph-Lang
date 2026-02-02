import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .core import Node, SubGraph, Program, G, Op


# ============================================================
# TOKENIZER (FIXED)
# ============================================================

class GLSpecTokenizer:
    KEYWORDS = {
        'FUNC', 'END', 'VAR', 'SET', 'IF', 'ELSE', 'ENDIF',
        'WHILE', 'ENDWHILE', 'FOR', 'IN', 'ENDFOR', 'RETURN',
        'PRINT', 'CALL', 'BREAK', 'CONTINUE', 'MAIN',
        'AND', 'OR', 'NOT', 'true', 'false'
    }
    
    TYPES = {'int', 'float', 'str', 'bool', 'void', 'any'}
    
    def tokenize(self, text: str) -> List[str]:
        tokens = []
        
        pattern = r'''
            (\.\.)              |
            (<=|>=|==|!=|->)    |
            ("[^"]*")           |
            (\d+\.\d+)          |
            (\d+)               |
            ([a-zA-Z_]\w*)      |
            ([+\-*/%<>(),=:])   |
            (\[|\])
        '''
        
        for match in re.finditer(pattern, text, re.VERBOSE):
            token = match.group(0)
            if token.strip():
                tokens.append(token)
        
        return tokens


@dataclass
class ParsedFunction:
    name: str
    params: List[Tuple[str, str]]
    return_type: str
    body: List[Any]


@dataclass  
class ParsedMain:
    body: List[Any]


class GLSpecParseError(SyntaxError):
    def __init__(self, message: str, token: str = None, position: int = None, expected: List[str] = None):
        self.token = token
        self.position = position
        self.expected = expected
        
        detail = message
        if token:
            detail += f" (got '{token}')"
        if position:
            detail += f" at position {position}"
        if expected:
            detail += f". Expected one of: {', '.join(expected)}"
        
        super().__init__(detail)


class GLSpecParser:
    MAX_PARSE_ITERATIONS = 10000
    
    VALID_TOP_LEVEL = {'FUNC', 'MAIN'}
    
    SIMILAR_KEYWORDS = {
        'FUNCTION': 'FUNC',
        'FN': 'FUNC',
        'DEF': 'FUNC',
        'def': 'FUNC',
        'function': 'FUNC',
        'func': 'FUNC',
        'main': 'MAIN',
        'LOOP': 'WHILE',
        'loop': 'WHILE',
        'ELSEIF': 'ELSE followed by IF',
        'ELIF': 'ELSE followed by IF',
        'elif': 'ELSE followed by IF',
        'THEN': '(not needed, use : instead)',
        'DO': '(not needed)',
        'BEGIN': '(not needed, blocks start with :)',
        'return': 'RETURN',
        'print': 'PRINT',
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'break': 'BREAK',
        'continue': 'CONTINUE',
    }
    
    def __init__(self):
        self.tokens: List[str] = []
        self.pos: int = 0
        self._iteration_count: int = 0
    
    def parse(self, glspec: str) -> Dict[str, Any]:
        """Parsea código GLSPEC completo"""
        tokenizer = GLSpecTokenizer()
        self.tokens = tokenizer.tokenize(glspec)
        self.pos = 0
        self._iteration_count = 0
        
        functions = []
        main = None
        
        while self.pos < len(self.tokens):
            self._check_iteration_limit()
            token = self.peek()
            
            if token == 'FUNC':
                functions.append(self._parse_function())
            elif token == 'MAIN':
                main = self._parse_main()
            else:
                self._handle_unexpected_token(token, list(self.VALID_TOP_LEVEL))
        
        return {'functions': functions, 'main': main}
    
    def _check_iteration_limit(self
        self._iteration_count += 1
        if self._iteration_count > self.MAX_PARSE_ITERATIONS:
            raise GLSpecParseError(
                "Parse limit exceeded - possible infinite loop or unclosed block",
                position=self.pos
            )
    
    def _handle_unexpected_token(self, token: str, expected: List[str
        if token in self.SIMILAR_KEYWORDS:
            suggestion = self.SIMILAR_KEYWORDS[token]
            raise GLSpecParseError(
                f"Unknown keyword '{token}'. Did you mean '{suggestion}'?",
                token=token,
                position=self.pos,
                expected=expected
            )
        raise GLSpecParseError(
            f"Unexpected token '{token}'",
            token=token,
            position=self.pos,
            expected=expected
        )
    
    def peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None
    
    def consume(self) -> str:
        if self.pos >= len(self.tokens):
            raise GLSpecParseError("Unexpected end of input", position=self.pos)
        token = self.tokens[self.pos]
        self.pos += 1
        return token
    
    def expect(self, expected: str) -> str:
        if self.pos >= len(self.tokens):
            raise GLSpecParseError(
                f"Unexpected end of input, expected '{expected}'",
                position=self.pos,
                expected=[expected]
            )
        token = self.consume()
        if token != expected:
            self.pos -= 1
            raise GLSpecParseError(
                f"Expected '{expected}'",
                token=token,
                position=self.pos,
                expected=[expected]
            )
        return token
    
    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.consume()
            return True
        return False
    
    def _parse_function(self) -> ParsedFunction:
        self.expect('FUNC')
        name = self.consume()
        self.expect('(')
        
        params = []
        if self.peek() != ')':
            while True:
                self._check_iteration_limit()
                pname = self.consume()
                self.expect(':')
                ptype = self.consume()
                params.append((pname, ptype))
                if not self.match(','):
                    break
        
        self.expect(')')
        
        return_type = 'any'
        if self.match('->'):
            return_type = self.consume()
        
        self.expect(':')
        body = self._parse_body(['END'], context='FUNC')
        self.expect('END')
        
        return ParsedFunction(name, params, return_type, body)
    
    def _parse_main(self) -> ParsedMain:
        self.expect('MAIN')
        self.expect(':')
        body = self._parse_body(['END'], context='MAIN')
        self.expect('END')
        return ParsedMain(body)
    
    def _parse_body(self, end_tokens: List[str], context: str = 'block') -> List[Any]:
        statements = []
        start_pos = self.pos
        iterations_without_progress = 0
        last_pos = self.pos
        
        while self.pos < len(self.tokens):
            self._check_iteration_limit()
            
            if self.pos == last_pos:
                iterations_without_progress += 1
                if iterations_without_progress > 10:
                    raise GLSpecParseError(
                        f"Parser stuck at token '{self.peek()}' in {context} block",
                        token=self.peek(),
                        position=self.pos,
                        expected=end_tokens
                    )
            else:
                iterations_without_progress = 0
                last_pos = self.pos
            
            if self.peek() in end_tokens:
                return statements
            
            all_end_tokens = {'END', 'ENDIF', 'ENDWHILE', 'ENDFOR', 'ELSE'}
            current = self.peek()
            if current in all_end_tokens and current not in end_tokens:
                raise GLSpecParseError(
                    f"Mismatched block closer '{current}' in {context} block",
                    token=current,
                    position=self.pos,
                    expected=end_tokens
                )
            
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
            elif self.peek() not in end_tokens:
                if self.peek() in self.SIMILAR_KEYWORDS or self.peek() in self.VALID_TOP_LEVEL:
                    raise GLSpecParseError(
                        f"Unclosed {context} block - found '{self.peek()}' but expected {end_tokens}",
                        token=self.peek(),
                        position=self.pos,
                        expected=end_tokens
                    )
        
        raise GLSpecParseError(
            f"Unclosed {context} block - reached end of input",
            position=self.pos,
            expected=end_tokens
        )
    
    def _parse_statement(self) -> Optional[Dict]:
        token = self.peek()
        
        if token == 'VAR':
            return self._parse_var()
        elif token == 'SET':
            return self._parse_set()
        elif token == 'IF':
            return self._parse_if()
        elif token == 'WHILE':
            return self._parse_while()
        elif token == 'FOR':
            return self._parse_for()
        elif token == 'RETURN':
            return self._parse_return()
        elif token == 'PRINT':
            return self._parse_print()
        elif token == 'CALL':
            return self._parse_call_stmt()
        elif token == 'BREAK':
            self.consume()
            return {'type': 'break'}
        elif token == 'CONTINUE':
            self.consume()
            return {'type': 'continue'}
        elif token in self.SIMILAR_KEYWORDS:
            self._handle_unexpected_token(token, ['VAR', 'SET', 'IF', 'WHILE', 'FOR', 'RETURN', 'PRINT'])
        else:
            return None
    
    def _parse_var(self) -> Dict:
        self.expect('VAR')
        name = self.consume()
        self.expect('=')
        value = self._parse_expression()
        return {'type': 'var', 'name': name, 'value': value}
    
    def _parse_set(self) -> Dict:
        self.expect('SET')
        name = self.consume()
        self.expect('=')
        value = self._parse_expression()
        return {'type': 'set', 'name': name, 'value': value}
    
    def _parse_if(self) -> Dict:
        self.expect('IF')
        condition = self._parse_expression()
        self.expect(':')
        then_body = self._parse_body(['ELSE', 'ENDIF'], context='IF')
        
        else_body = None
        if self.match('ELSE'):
            self.expect(':')
            else_body = self._parse_body(['ENDIF'], context='ELSE')
        
        self.expect('ENDIF')
        return {'type': 'if', 'condition': condition, 'then': then_body, 'else': else_body}
    
    def _parse_while(self) -> Dict:
        self.expect('WHILE')
        condition = self._parse_expression()
        self.expect(':')
        body = self._parse_body(['ENDWHILE'], context='WHILE')
        self.expect('ENDWHILE')
        return {'type': 'while', 'condition': condition, 'body': body}
    
    def _parse_for(self) -> Dict:
        self.expect('FOR')
        var_name = self.consume()
        self.expect('IN')
        start = self._parse_primary()
        self.expect('..')
        end = self._parse_primary()
        self.expect(':')
        body = self._parse_body(['ENDFOR'], context='FOR')
        self.expect('ENDFOR')
        return {'type': 'for', 'var': var_name, 'start': start, 'end': end, 'body': body}
    
    def _parse_return(self) -> Dict:
        self.expect('RETURN')
        value = self._parse_expression()
        return {'type': 'return', 'value': value}
    
    def _parse_print(self) -> Dict:
        self.expect('PRINT')
        args = [self._parse_expression()]
        while self.match(','):
            self._check_iteration_limit()
            args.append(self._parse_expression())
        return {'type': 'print', 'args': args}
    
    def _parse_call_stmt(self) -> Dict:
        self.expect('CALL')
        name = self.consume()
        self.expect('(')
        args = []
        if self.peek() != ')':
            args.append(self._parse_expression())
            while self.match(','):
                self._check_iteration_limit()
                args.append(self._parse_expression())
        self.expect(')')
        return {'type': 'call', 'name': name, 'args': args}
    
    def _parse_expression(self) -> Any:
        return self._parse_or()
    
    def _parse_or(self) -> Any:
        left = self._parse_and()
        while self.match('OR'):
            self._check_iteration_limit()
            right = self._parse_and()
            left = {'type': 'binary', 'op': 'or', 'left': left, 'right': right}
        return left
    
    def _parse_and(self) -> Any:
        left = self._parse_not()
        while self.match('AND'):
            self._check_iteration_limit()
            right = self._parse_not()
            left = {'type': 'binary', 'op': 'and', 'left': left, 'right': right}
        return left
    
    def _parse_not(self) -> Any:
        if self.match('NOT'):
            return {'type': 'unary', 'op': 'not', 'expr': self._parse_not()}
        return self._parse_comparison()
    
    def _parse_comparison(self) -> Any:
        left = self._parse_add_sub()
        ops = {'==': 'eq', '!=': 'neq', '<': 'lt', '>': 'gt', '<=': 'lte', '>=': 'gte'}
        while self.peek() in ops:
            self._check_iteration_limit()
            op = ops[self.consume()]
            right = self._parse_add_sub()
            left = {'type': 'binary', 'op': op, 'left': left, 'right': right}
        return left
    
    def _parse_add_sub(self) -> Any:
        left = self._parse_mul_div()
        while self.peek() in ('+', '-'):
            self._check_iteration_limit()
            op = 'add' if self.consume() == '+' else 'sub'
            right = self._parse_mul_div()
            left = {'type': 'binary', 'op': op, 'left': left, 'right': right}
        return left
    
    def _parse_mul_div(self) -> Any:
        left = self._parse_unary()
        ops = {'*': 'mul', '/': 'div', '%': 'mod'}
        while self.peek() in ops:
            self._check_iteration_limit()
            op = ops[self.consume()]
            right = self._parse_unary()
            left = {'type': 'binary', 'op': op, 'left': left, 'right': right}
        return left
    
    def _parse_unary(self) -> Any:
        if self.peek() == '-':
            self.consume()
            return {'type': 'unary', 'op': 'neg', 'expr': self._parse_unary()}
        return self._parse_primary()
    
    def _parse_primary(self) -> Any:
        token = self.peek()
        
        if token == '(':
            self.consume()
            expr = self._parse_expression()
            self.expect(')')
            return expr
        
        if self._is_number(token):
            self.consume()
            return {'type': 'literal', 'value': float(token) if '.' in token else int(token)}
        
        if token and token.startswith('"'):
            self.consume()
            return {'type': 'literal', 'value': token}
        
        if token in ('true', 'false'):
            self.consume()
            return {'type': 'literal', 'value': token == 'true'}
        
        if token and (token[0].isalpha() or token[0] == '_'):
            self.consume()
            
            if self.peek() == '(':
                self.consume()
                args = []
                if self.peek() != ')':
                    args.append(self._parse_expression())
                    while self.match(','):
                        self._check_iteration_limit()
                        args.append(self._parse_expression())
                self.expect(')')
                return {'type': 'func_call', 'name': token, 'args': args}
            
            return {'type': 'var', 'name': token}
        
        raise GLSpecParseError(f"Unexpected token in expression", token=token, position=self.pos)
    
    def _is_number(self, token: Optional[str]) -> bool:
        if not token:
            return False
        try:
            float(token)
            return True
        except ValueError:
            return False

class GLSpecToGraph:
    """Convierte AST de GLSPEC a Grafo"""
    
    def convert(self, ast: Dict) -> Program:
        """Convierte AST completo a Program"""
        program = G.program("generated")
        
        for func in ast.get('functions', []):
            sg = self._convert_function(func)
            program.register(sg)
        
        if ast.get('main'):
            main_node = self._convert_body(ast['main'].body)
            program.entry(main_node)
        
        return program
    
    def _convert_function(self, func: ParsedFunction) -> SubGraph:
        params = [p[0] for p in func.params]  # Solo nombres
        sg = G.subgraph(func.name, params)
        body = self._convert_body(func.body)
        sg.set_body(body)
        return sg
    
    def _convert_body(self, statements: List[Dict]) -> Optional[Node]:
        if not statements:
            return G.nop()
        
        nodes = [self._convert_statement(s) for s in statements if s]
        nodes = [n for n in nodes if n]  # Filter None
        
        if not nodes:
            return G.nop()
        elif len(nodes) == 1:
            return nodes[0]
        else:
            return G.seq(*nodes)
    
    def _convert_statement(self, stmt: Dict) -> Optional[Node]:
        stmt_type = stmt.get('type')
        
        if stmt_type == 'var':
            value = self._convert_expr(stmt['value'])
            return G.def_var(stmt['name'], value)
        
        elif stmt_type == 'set':
            value = self._convert_expr(stmt['value'])
            return G.set(stmt['name'], value)
        
        elif stmt_type == 'if':
            cond = self._convert_expr(stmt['condition'])
            then_branch = self._convert_body(stmt['then'])
            else_branch = self._convert_body(stmt['else']) if stmt.get('else') else None
            return G.if_(cond, then_branch, else_branch)
        
        elif stmt_type == 'while':
            cond = self._convert_expr(stmt['condition'])
            body = self._convert_body(stmt['body'])
            return G.loop(cond, body)
        
        elif stmt_type == 'for':
            var_name = stmt['var']
            start = self._convert_expr(stmt['start'])
            end = self._convert_expr(stmt['end'])
            
            init = G.def_var(var_name, start)
            cond = G.lte(var_name, end)
            
            body_stmts = [self._convert_statement(s) for s in stmt['body']]
            body_stmts.append(G.set(var_name, G.add(var_name, 1)))
            body = G.seq(*[n for n in body_stmts if n])
            
            loop = G.loop(cond, body)
            return G.seq(init, loop)
        
        elif stmt_type == 'return':
            value = self._convert_expr(stmt['value'])
            return G.return_(value)
        
        elif stmt_type == 'print':
            args = [self._convert_expr(a) for a in stmt['args']]
            return G.print_(*args)
        
        elif stmt_type == 'call':
            args = [self._convert_expr(a) for a in stmt['args']]
            return G.call(stmt['name'], args)
        
        elif stmt_type == 'break':
            return G.break_()
        
        elif stmt_type == 'continue':
            return G.continue_()
        
        return None
    
    def _convert_expr(self, expr: Any) -> Any:
        if not isinstance(expr, dict):
            return expr
        
        expr_type = expr.get('type')
        
        if expr_type == 'literal':
            return expr['value']
        
        elif expr_type == 'var':
            return expr['name']
        
        elif expr_type == 'binary':
            left = self._convert_expr(expr['left'])
            right = self._convert_expr(expr['right'])
            op = expr['op']
            
            op_map = {
                'add': G.add, 'sub': G.sub, 'mul': G.mul, 'div': G.div, 'mod': G.mod,
                'eq': G.eq, 'neq': G.neq, 'gt': G.gt, 'lt': G.lt, 'gte': G.gte, 'lte': G.lte,
                'and': G.and_, 'or': G.or_
            }
            
            if op in op_map:
                return op_map[op](left, right)
            return left
        
        elif expr_type == 'unary':
            inner = self._convert_expr(expr['expr'])
            if expr['op'] == 'not':
                return G.not_(inner)
            elif expr['op'] == 'neg':
                if isinstance(inner, (int, float)):
                    return -inner
                return G.sub(0, inner)
            return inner
        
        elif expr_type == 'func_call':
            args = [self._convert_expr(a) for a in expr['args']]
            return G.call(expr['name'], args)
        
        return expr

def glspec_to_graph(glspec: str) -> Program:
    parser = GLSpecParser()
    ast = parser.parse(glspec)
    converter = GLSpecToGraph()
    return converter.convert(ast)