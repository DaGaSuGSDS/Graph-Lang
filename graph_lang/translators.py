from typing import Any, Optional
from .core import Node, SubGraph, Program, Op

class BaseTranslator:
    def __init__(self):
        self.indent = 0
        self._expr_depth = 0
    
    def translate(self, program: Program) -> str:
        raise NotImplementedError
    
    def _pad(self) -> str:
        return self._indent_str * self.indent
    
    @property
    def _indent_str(self) -> str:
        return "  "

class JSTranslator(BaseTranslator):
    def translate(self, program: Program) -> str:
        self.indent = 0
        self._expr_depth = 0
        
        lines = [
            "// Generated from Graph-Lang",
            f"// Program: {program.name}",
            ""
        ]
        
        if program.globals_vars:
            lines.append("// === GLOBALS ===")
            for name, value in program.globals_vars.items():
                lines.append(f"let {name} = {self._value_to_js(value)};")
            lines.append("")
        
        if program.subgraphs:
            lines.append("// === FUNCTIONS ===")
            for sg in program.subgraphs.values():
                lines.append(self._translate_subgraph(sg))
                lines.append("")
        
        if program.main:
            lines.append("// === MAIN ===")
            lines.append(self._translate_node(program.main))
        
        return "\n".join(lines)
    
    def _translate_subgraph(self, sg: SubGraph) -> str:
        params = ", ".join(sg.params)
        self.indent = 1
        body = self._translate_node(sg.body) if sg.body else ""
        self.indent = 0
        return f"function {sg.name}({params}) {{\n{body}\n}}"
    
    def _translate_node(self, node: Optional[Node]) -> str:
        if node is None:
            return ""
        
        lines = []
        d = node.data
        
        if node.op == Op.DEF_VAR:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}let {d['name']} = {value};")
        
        elif node.op == Op.SET:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}{d['name']} = {value};")
        
        elif node.op == Op.GET:
            return d['name']
        
        elif node.op == Op.LITERAL:
            return self._value_to_js(d['value'])
        
        elif node.op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD):
            ops = {Op.ADD: '+', Op.SUB: '-', Op.MUL: '*', Op.DIV: '/', Op.MOD: '%'}
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} {ops[node.op]} {right})"
        
        elif node.op in (Op.EQ, Op.NEQ, Op.GT, Op.LT, Op.GTE, Op.LTE):
            ops = {Op.EQ: '===', Op.NEQ: '!==', Op.GT: '>', Op.LT: '<', Op.GTE: '>=', Op.LTE: '<='}
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} {ops[node.op]} {right})"
        
        elif node.op == Op.AND:
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} && {right})"
        
        elif node.op == Op.OR:
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} || {right})"
        
        elif node.op == Op.NOT:
            expr = self._translate_value(d['expr'])
            return f"(!{expr})"
        
        elif node.op == Op.IF:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}if ({cond}) {{")
            self.indent += 1
            if d.get('then'):
                lines.append(self._translate_node(d['then']))
            self.indent -= 1
            if d.get('else'):
                lines.append(f"{self._pad()}}} else {{")
                self.indent += 1
                lines.append(self._translate_node(d['else']))
                self.indent -= 1
            lines.append(f"{self._pad()}}}")
        
        elif node.op == Op.LOOP:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}while ({cond}) {{")
            self.indent += 1
            if d.get('body'):
                lines.append(self._translate_node(d['body']))
            self.indent -= 1
            lines.append(f"{self._pad()}}}")
        
        elif node.op == Op.BREAK:
            lines.append(f"{self._pad()}break;")
        
        elif node.op == Op.CONTINUE:
            lines.append(f"{self._pad()}continue;")
        
        elif node.op == Op.CALL:
            args = ", ".join(self._translate_value(a) for a in d.get('args', []))
            call_expr = f"{d['name']}({args})"
            if self._expr_depth > 0:
                return call_expr
            lines.append(f"{self._pad()}{call_expr};")
        
        elif node.op == Op.RETURN:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}return {value};")
        
        elif node.op == Op.PRINT:
            args = ", ".join(self._translate_value(a) for a in d.get('args', []))
            lines.append(f"{self._pad()}console.log({args});")
        
        elif node.op == Op.SEQ:
            for n in d.get('nodes', []):
                lines.append(self._translate_node(n))
        
        elif node.op == Op.NOP:
            pass
        
        if node.next_node:
            lines.append(self._translate_node(node.next_node))
        
        return "\n".join(filter(None, lines))
    
    def _translate_value(self, val: Any) -> str:
        if isinstance(val, Node):
            self._expr_depth += 1
            result = self._translate_node(val)
            self._expr_depth -= 1
            return result
        elif isinstance(val, bool):
            return "true" if val else "false"
        elif isinstance(val, str):
            if val.startswith('"'):
                return val
            try:
                float(val)
                return val
            except ValueError:
                return val
        elif val is None:
            return "null"
        else:
            return str(val)
    
    def _value_to_js(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        elif isinstance(val, str):
            if val.startswith('"'):
                return val
            return f'"{val}"'
        elif val is None:
            return "null"
        else:
            return str(val)

class PythonTranslator(BaseTranslator):
    """Traduce grafos a Python"""
    
    @property
    def _indent_str(self) -> str:
        return "    "
    
    def translate(self, program: Program) -> str:
        self.indent = 0
        self._expr_depth = 0
        
        lines = [
            "# Generated from Graph-Lang",
            f"# Program: {program.name}",
            ""
        ]
        
        if program.subgraphs:
            lines.append("# === FUNCTIONS ===")
            for sg in program.subgraphs.values():
                lines.append(self._translate_subgraph(sg))
                lines.append("")
        
        if program.main:
            lines.append("# === MAIN ===")
            if program.globals_vars:
                for name, value in program.globals_vars.items():
                    lines.append(f"{name} = {self._value_to_py(value)}")
            lines.append(self._translate_node(program.main))
        
        return "\n".join(lines)
    
    def _translate_subgraph(self, sg: SubGraph) -> str:
        params = ", ".join(sg.params)
        lines = [f"def {sg.name}({params}):"]
        
        if sg.uses_globals:
            lines.append(f"    global {', '.join(sg.uses_globals)}")
        
        self.indent = 1
        body = self._translate_node(sg.body) if sg.body else "    pass"
        self.indent = 0
        
        lines.append(body if body else "    pass")
        return "\n".join(lines)
    
    def _translate_node(self, node: Optional[Node]) -> str:
        if node is None:
            return ""
        
        lines = []
        d = node.data
        
        if node.op == Op.DEF_VAR:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}{d['name']} = {value}")
        
        elif node.op == Op.SET:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}{d['name']} = {value}")
        
        elif node.op == Op.GET:
            return d['name']
        
        elif node.op == Op.LITERAL:
            return self._value_to_py(d['value'])
        
        elif node.op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD):
            ops = {Op.ADD: '+', Op.SUB: '-', Op.MUL: '*', Op.DIV: '//', Op.MOD: '%'}
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} {ops[node.op]} {right})"
        
        elif node.op in (Op.EQ, Op.NEQ, Op.GT, Op.LT, Op.GTE, Op.LTE):
            ops = {Op.EQ: '==', Op.NEQ: '!=', Op.GT: '>', Op.LT: '<', Op.GTE: '>=', Op.LTE: '<='}
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} {ops[node.op]} {right})"
        
        elif node.op == Op.AND:
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} and {right})"
        
        elif node.op == Op.OR:
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} or {right})"
        
        elif node.op == Op.NOT:
            expr = self._translate_value(d['expr'])
            return f"(not {expr})"
        
        elif node.op == Op.IF:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}if {cond}:")
            self.indent += 1
            then_code = self._translate_node(d['then']) if d.get('then') else f"{self._pad()}pass"
            lines.append(then_code if then_code else f"{self._pad()}pass")
            self.indent -= 1
            if d.get('else'):
                lines.append(f"{self._pad()}else:")
                self.indent += 1
                else_code = self._translate_node(d['else'])
                lines.append(else_code if else_code else f"{self._pad()}pass")
                self.indent -= 1
        
        elif node.op == Op.LOOP:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}while {cond}:")
            self.indent += 1
            body_code = self._translate_node(d['body']) if d.get('body') else f"{self._pad()}pass"
            lines.append(body_code if body_code else f"{self._pad()}pass")
            self.indent -= 1
        
        elif node.op == Op.BREAK:
            lines.append(f"{self._pad()}break")
        
        elif node.op == Op.CONTINUE:
            lines.append(f"{self._pad()}continue")
        
        elif node.op == Op.CALL:
            args = ", ".join(self._translate_value(a) for a in d.get('args', []))
            call_expr = f"{d['name']}({args})"
            if self._expr_depth > 0:
                return call_expr
            lines.append(f"{self._pad()}{call_expr}")
        
        elif node.op == Op.RETURN:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}return {value}")
        
        elif node.op == Op.PRINT:
            args = ", ".join(self._translate_value(a) for a in d.get('args', []))
            lines.append(f"{self._pad()}print({args})")
        
        elif node.op == Op.SEQ:
            for n in d.get('nodes', []):
                result = self._translate_node(n)
                if result:
                    lines.append(result)
        
        elif node.op == Op.NOP:
            pass
        
        if node.next_node:
            result = self._translate_node(node.next_node)
            if result:
                lines.append(result)
        
        return "\n".join(filter(None, lines))
    
    def _translate_value(self, val: Any) -> str:
        if isinstance(val, Node):
            self._expr_depth += 1
            result = self._translate_node(val)
            self._expr_depth -= 1
            return result
        elif isinstance(val, bool):
            return "True" if val else "False"
        elif isinstance(val, str):
            if val.startswith('"'):
                return val
            try:
                float(val)
                return val
            except ValueError:
                return val
        elif val is None:
            return "None"
        else:
            return str(val)
    
    def _value_to_py(self, val: Any) -> str:
        if isinstance(val, bool):
            return "True" if val else "False"
        elif isinstance(val, str):
            if val.startswith('"'):
                return val
            return f'"{val}"'
        elif val is None:
            return "None"
        else:
            return str(val)

class CTranslator(BaseTranslator):
    def translate(self, program: Program) -> str:
        self.indent = 0
        self._expr_depth = 0
        
        lines = [
            "// Generated from Graph-Lang",
            f"// Program: {program.name}",
            "#include <stdio.h>",
            ""
        ]
        
        if program.subgraphs:
            for sg in program.subgraphs.values():
                lines.append(self._translate_subgraph(sg))
                lines.append("")
        
        lines.append("int main() {")
        self.indent = 1
        
        if program.globals_vars:
            for name, value in program.globals_vars.items():
                lines.append(f"{self._pad()}int {name} = {self._value_to_c(value)};")
        
        if program.main:
            lines.append(self._translate_node(program.main))
        
        lines.append(f"{self._pad()}return 0;")
        self.indent = 0
        lines.append("}")
        
        return "\n".join(lines)
    
    def _translate_subgraph(self, sg: SubGraph) -> str:
        params = ", ".join(f"int {p}" for p in sg.params)
        lines = [f"int {sg.name}({params}) {{"]
        
        self.indent = 1
        body = self._translate_node(sg.body) if sg.body else ""
        self.indent = 0
        
        lines.append(body)
        lines.append("}")
        return "\n".join(lines)
    
    def _translate_node(self, node: Optional[Node]) -> str:
        if node is None:
            return ""
        
        lines = []
        d = node.data
        
        if node.op == Op.DEF_VAR:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}int {d['name']} = {value};")
        
        elif node.op == Op.SET:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}{d['name']} = {value};")
        
        elif node.op == Op.GET:
            return d['name']
        
        elif node.op == Op.LITERAL:
            return self._value_to_c(d['value'])
        
        elif node.op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                         Op.EQ, Op.NEQ, Op.GT, Op.LT, Op.GTE, Op.LTE):
            ops = {
                Op.ADD: '+', Op.SUB: '-', Op.MUL: '*', Op.DIV: '/', Op.MOD: '%',
                Op.EQ: '==', Op.NEQ: '!=', Op.GT: '>', Op.LT: '<', Op.GTE: '>=', Op.LTE: '<='
            }
            left = self._translate_value(d['left'])
            right = self._translate_value(d['right'])
            return f"({left} {ops[node.op]} {right})"
        
        elif node.op == Op.AND:
            return f"({self._translate_value(d['left'])} && {self._translate_value(d['right'])})"
        
        elif node.op == Op.OR:
            return f"({self._translate_value(d['left'])} || {self._translate_value(d['right'])})"
        
        elif node.op == Op.NOT:
            return f"(!{self._translate_value(d['expr'])})"
        
        elif node.op == Op.IF:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}if ({cond}) {{")
            self.indent += 1
            lines.append(self._translate_node(d.get('then')))
            self.indent -= 1
            if d.get('else'):
                lines.append(f"{self._pad()}}} else {{")
                self.indent += 1
                lines.append(self._translate_node(d['else']))
                self.indent -= 1
            lines.append(f"{self._pad()}}}")
        
        elif node.op == Op.LOOP:
            cond = self._translate_value(d['cond'])
            lines.append(f"{self._pad()}while ({cond}) {{")
            self.indent += 1
            lines.append(self._translate_node(d.get('body')))
            self.indent -= 1
            lines.append(f"{self._pad()}}}")
        
        elif node.op == Op.BREAK:
            lines.append(f"{self._pad()}break;")
        
        elif node.op == Op.CONTINUE:
            lines.append(f"{self._pad()}continue;")
        
        elif node.op == Op.CALL:
            args = ", ".join(self._translate_value(a) for a in d.get('args', []))
            call_expr = f"{d['name']}({args})"
            if self._expr_depth > 0:
                return call_expr
            lines.append(f"{self._pad()}{call_expr};")
        
        elif node.op == Op.RETURN:
            value = self._translate_value(d['value'])
            lines.append(f"{self._pad()}return {value};")
        
        elif node.op == Op.PRINT:
            args = d.get('args', [])
            if args:
                val = self._translate_value(args[0])
                if val.strip().startswith('"'):
                    fmt = "%s"
                else:
                    fmt = "%d"
                lines.append(f'{self._pad()}printf("{fmt}\\n", {val});')
        
        elif node.op == Op.SEQ:
            for n in d.get('nodes', []):
                lines.append(self._translate_node(n))
        
        if node.next_node:
            lines.append(self._translate_node(node.next_node))
        
        return "\n".join(filter(None, lines))
    
    def _translate_value(self, val: Any) -> str:
        if isinstance(val, Node):
            self._expr_depth += 1
            result = self._translate_node(val)
            self._expr_depth -= 1
            return result
        elif isinstance(val, bool):
            return "1" if val else "0"
        elif isinstance(val, str):
            try:
                float(val)
                return val
            except ValueError:
                return val
        elif val is None:
            return "0"
        else:
            return str(val)
    
    def _value_to_c(self, val: Any) -> str:
        if isinstance(val, bool):
            return "1" if val else "0"
        elif val is None:
            return "0"
        else:
            return str(val)
