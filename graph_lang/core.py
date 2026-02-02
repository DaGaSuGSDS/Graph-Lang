"""
GRAPH-LANG v2 - Python Implementation
=====================================

Sistema de programación basado en grafos dirigidos.

Arquitectura:
    Usuario → MiniLlama → GLSPEC → GraphGen → Grafo → Traductor → Código
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum, auto
import json


# ============================================================
# PARTE 1: Operaciones (tipo ensamblador)
# ============================================================

class Op(Enum):
    """Operaciones disponibles en el grafo (vocabulario fijo ~40 tokens)"""
    
    # Variables
    DEF_VAR = "def"
    SET = "set"
    GET = "get"
    
    # Aritmética
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    
    # Comparación
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    
    # Lógicos
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # Control de flujo
    IF = "if"
    LOOP = "loop"
    BREAK = "break"
    CONTINUE = "continue"
    
    # Funciones
    CALL = "call"
    RETURN = "ret"
    
    # I/O
    PRINT = "print"
    
    # Estructura
    SEQ = "seq"
    NOP = "nop"
    LITERAL = "lit"

# ============================================================
# PARTE 2: Nodos del Grafo
# ============================================================

_node_counter = 0

def _next_id() -> int:
    global _node_counter
    _node_counter += 1
    return _node_counter


@dataclass
class Node:
    """Nodo del grafo de programación"""
    op: Op
    data: Dict[str, Any] = field(default_factory=dict)
    node_id: int = field(default_factory=_next_id)
    next_node: Optional[Node] = None
    
    def then(self, node: Node) -> Node:
        """Encadena este nodo con el siguiente, retorna el HEAD"""
        # Encontrar el último nodo de la cadena
        current = self
        while current.next_node:
            current = current.next_node
        current.next_node = node
        return self  # Retornar HEAD para encadenar
    
    def __repr__(self):
        return f"Node({self.op.value}, {self.data})"


# ============================================================
# PARTE 3: SubGraph (Función)
# ============================================================

@dataclass
class SubGraph:
    """Un subgrafo representa una función/subrutina"""
    name: str
    params: List[str] = field(default_factory=list)
    body: Optional[Node] = None
    uses_globals: List[str] = field(default_factory=list)
    
    def globals(self, *names: str) -> SubGraph:
        """Declara qué variables globales usa este subgrafo"""
        self.uses_globals = list(names)
        return self
    
    def set_body(self, node: Node) -> SubGraph:
        """Establece el cuerpo del subgrafo"""
        self.body = node
        return self


# ============================================================
# PARTE 4: Programa Principal
# ============================================================

@dataclass
class Program:
    """Programa completo con globales, subgrafos y main"""
    name: str = "program"
    globals_vars: Dict[str, Any] = field(default_factory=dict)
    subgraphs: Dict[str, SubGraph] = field(default_factory=dict)
    main: Optional[Node] = None
    
    def add_global(self, name: str, value: Any = None) -> Program:
        """Añade una variable global"""
        self.globals_vars[name] = value
        return self
    
    def register(self, subgraph: SubGraph) -> Program:
        """Registra un subgrafo (función)"""
        self.subgraphs[subgraph.name] = subgraph
        return self
    
    def entry(self, node: Node) -> Program:
        """Establece el punto de entrada (main)"""
        self.main = node
        return self


# ============================================================
# PARTE 5: DSL - Constructores de Nodos (API fluida)
# ============================================================

class G:
    """
    DSL para construir grafos de forma fluida.
    
    Ejemplo:
        G.def_var('x', 10).then(G.set('x', G.add('x', 1))).then(G.print('x'))
    """
    
    # --- Variables ---
    @staticmethod
    def def_var(name: str, value: Any) -> Node:
        return Node(Op.DEF_VAR, {'name': name, 'value': value})
    
    @staticmethod
    def set(name: str, value: Any) -> Node:
        return Node(Op.SET, {'name': name, 'value': value})
    
    @staticmethod
    def get(name: str) -> Node:
        return Node(Op.GET, {'name': name})
    
    # --- Literales ---
    @staticmethod
    def lit(value: Any) -> Node:
        return Node(Op.LITERAL, {'value': value})
    
    # --- Aritmética ---
    @staticmethod
    def add(left: Any, right: Any) -> Node:
        return Node(Op.ADD, {'left': left, 'right': right})
    
    @staticmethod
    def sub(left: Any, right: Any) -> Node:
        return Node(Op.SUB, {'left': left, 'right': right})
    
    @staticmethod
    def mul(left: Any, right: Any) -> Node:
        return Node(Op.MUL, {'left': left, 'right': right})
    
    @staticmethod
    def div(left: Any, right: Any) -> Node:
        return Node(Op.DIV, {'left': left, 'right': right})
    
    @staticmethod
    def mod(left: Any, right: Any) -> Node:
        return Node(Op.MOD, {'left': left, 'right': right})
    
    # --- Comparación ---
    @staticmethod
    def eq(left: Any, right: Any) -> Node:
        return Node(Op.EQ, {'left': left, 'right': right})
    
    @staticmethod
    def neq(left: Any, right: Any) -> Node:
        return Node(Op.NEQ, {'left': left, 'right': right})
    
    @staticmethod
    def gt(left: Any, right: Any) -> Node:
        return Node(Op.GT, {'left': left, 'right': right})
    
    @staticmethod
    def lt(left: Any, right: Any) -> Node:
        return Node(Op.LT, {'left': left, 'right': right})
    
    @staticmethod
    def gte(left: Any, right: Any) -> Node:
        return Node(Op.GTE, {'left': left, 'right': right})
    
    @staticmethod
    def lte(left: Any, right: Any) -> Node:
        return Node(Op.LTE, {'left': left, 'right': right})
    
    # --- Lógicos ---
    @staticmethod
    def and_(left: Any, right: Any) -> Node:
        return Node(Op.AND, {'left': left, 'right': right})
    
    @staticmethod
    def or_(left: Any, right: Any) -> Node:
        return Node(Op.OR, {'left': left, 'right': right})
    
    @staticmethod
    def not_(expr: Any) -> Node:
        return Node(Op.NOT, {'expr': expr})
    
    # --- Control de flujo ---
    @staticmethod
    def if_(cond: Any, then_branch: Node, else_branch: Optional[Node] = None) -> Node:
        return Node(Op.IF, {'cond': cond, 'then': then_branch, 'else': else_branch})
    
    @staticmethod
    def loop(cond: Any, body: Node) -> Node:
        return Node(Op.LOOP, {'cond': cond, 'body': body})
    
    @staticmethod
    def break_() -> Node:
        return Node(Op.BREAK)
    
    @staticmethod
    def continue_() -> Node:
        return Node(Op.CONTINUE)
    
    # --- Funciones ---
    @staticmethod
    def call(name: str, args: List[Any] = None) -> Node:
        return Node(Op.CALL, {'name': name, 'args': args or []})
    
    @staticmethod
    def return_(value: Any) -> Node:
        return Node(Op.RETURN, {'value': value})
    
    # --- I/O ---
    @staticmethod
    def print_(*args: Any) -> Node:
        return Node(Op.PRINT, {'args': list(args)})
    
    # --- Estructura ---
    @staticmethod
    def seq(*nodes: Node) -> Node:
        return Node(Op.SEQ, {'nodes': list(nodes)})
    
    @staticmethod
    def nop() -> Node:
        return Node(Op.NOP)
    
    # --- Constructores de alto nivel ---
    @staticmethod
    def subgraph(name: str, params: List[str] = None) -> SubGraph:
        return SubGraph(name, params or [])
    
    @staticmethod
    def program(name: str = "program") -> Program:
        return Program(name)


# ============================================================
# PARTE 6: Serializador (Grafo → S-expression texto)
# ============================================================

class GraphSerializer:
    """Serializa un programa/grafo a formato S-expression"""
    
    def serialize(self, program: Program) -> str:
        """Serializa un programa completo"""
        parts = [f'(program "{program.name}"']
        
        # Globales
        if program.globals_vars:
            globals_str = ' '.join(
                f'(global {name} {self._serialize_value(val)})'
                for name, val in program.globals_vars.items()
            )
            parts.append(f'  (globals {globals_str})')
        
        # Subgrafos
        if program.subgraphs:
            subs = ' '.join(
                self._serialize_subgraph(sg)
                for sg in program.subgraphs.values()
            )
            parts.append(f'  (subgraphs {subs})')
        
        # Main
        if program.main:
            parts.append(f'  (main {self._serialize_node(program.main)})')
        
        return '\n'.join(parts) + ')'
    
    def _serialize_subgraph(self, sg: SubGraph) -> str:
        params = ' '.join(sg.params)
        body = self._serialize_node(sg.body) if sg.body else '(nop)'
        return f'(fn {sg.name} [{params}] {body})'
    
    def _serialize_node(self, node: Node) -> str:
        if node is None:
            return 'nil'
        
        d = node.data
        result = ''
        
        if node.op == Op.DEF_VAR:
            result = f"(def {d['name']} {self._serialize_value(d['value'])})"
        elif node.op == Op.SET:
            result = f"(set {d['name']} {self._serialize_value(d['value'])})"
        elif node.op == Op.GET:
            result = d['name']
        elif node.op == Op.LITERAL:
            result = self._serialize_value(d['value'])
        elif node.op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                         Op.EQ, Op.NEQ, Op.GT, Op.LT, Op.GTE, Op.LTE,
                         Op.AND, Op.OR):
            left = self._serialize_value(d['left'])
            right = self._serialize_value(d['right'])
            result = f"({node.op.value} {left} {right})"
        elif node.op == Op.NOT:
            result = f"(not {self._serialize_value(d['expr'])})"
        elif node.op == Op.IF:
            cond = self._serialize_value(d['cond'])
            then_part = self._serialize_node(d['then'])
            else_part = self._serialize_node(d['else']) if d.get('else') else 'nil'
            result = f"(if {cond} {then_part} {else_part})"
        elif node.op == Op.LOOP:
            cond = self._serialize_value(d['cond'])
            body = self._serialize_node(d['body'])
            result = f"(loop {cond} {body})"
        elif node.op == Op.BREAK:
            result = "(break)"
        elif node.op == Op.CONTINUE:
            result = "(continue)"
        elif node.op == Op.CALL:
            args = ' '.join(self._serialize_value(a) for a in d['args'])
            result = f"(call {d['name']} [{args}])"
        elif node.op == Op.RETURN:
            result = f"(ret {self._serialize_value(d['value'])})"
        elif node.op == Op.PRINT:
            args = ' '.join(self._serialize_value(a) for a in d['args'])
            result = f"(print [{args}])"
        elif node.op == Op.SEQ:
            nodes = ' '.join(self._serialize_node(n) for n in d['nodes'])
            result = f"(seq {nodes})"
        elif node.op == Op.NOP:
            result = "(nop)"
        else:
            result = f"({node.op.value})"
        
        # Encadenar siguiente nodo
        if node.next_node:
            result = f"(seq {result} {self._serialize_node(node.next_node)})"
        
        return result
    
    def _serialize_value(self, val: Any) -> str:
        if isinstance(val, Node):
            return self._serialize_node(val)
        elif isinstance(val, bool):
            return 'true' if val else 'false'
        elif isinstance(val, str):
            if val.startswith('"'):
                return val
            elif val.replace('.', '').replace('-', '').isdigit():
                return val
            else:
                return val  # Variable name
        elif val is None:
            return 'nil'
        else:
            return str(val)