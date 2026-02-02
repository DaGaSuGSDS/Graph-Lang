import sys
import traceback
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum, auto

sys.path.insert(0, '/home/claude')
from graph_lang import glspec_to_graph, PythonTranslator, JSTranslator

class FailType(Enum):
    PARSE_ERROR = auto()
    GRAPH_ERROR = auto()
    TRANSLATE_ERROR = auto()
    EXEC_ERROR = auto()
    WRONG_OUTPUT = auto()

@dataclass
class TestCase:
    id: str
    name: str
    glspec: str
    should_work: bool = True
    expected_output: Optional[str] = None
    category: str = "general"

@dataclass
class TestResult:
    test: TestCase
    success: bool
    fail_type: Optional[FailType] = None
    error_msg: str = ""
    glspec_parsed: bool = False
    graph_built: bool = False
    code_generated: str = ""
    code_ran: bool = False
    actual_output: str = ""

TESTS: List[TestCase] = [
    TestCase(
        id="basic_001",
        name="Función suma simple",
        category="basic",
        glspec="""
FUNC suma(a: int, b: int) -> int:
  RETURN a + b
END

MAIN:
  PRINT suma(3, 5)
END
""",
        expected_output="8"
    ),
    
    TestCase(
        id="basic_002", 
        name="Variable y asignación",
        category="basic",
        glspec="""
MAIN:
  VAR x = 10
  SET x = x + 5
  PRINT x
END
""",
        expected_output="15"
    ),

    TestCase(
        id="unclosed_001",
        name="❌ FUNC sin END",
        category="unclosed_blocks",
        glspec="""
FUNC suma(a: int, b: int) -> int:
  RETURN a + b

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="unclosed_002",
        name="❌ IF sin ENDIF",
        category="unclosed_blocks",
        glspec="""
FUNC test(x: int) -> int:
  IF x > 0:
    RETURN 1
  ELSE:
    RETURN 0
END

MAIN:
  PRINT test(5)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="unclosed_003",
        name="❌ WHILE sin ENDWHILE",
        category="unclosed_blocks",
        glspec="""
MAIN:
  VAR i = 0
  WHILE i < 5:
    PRINT i
    SET i = i + 1
END
""",
        should_work=False
    ),
    
    TestCase(
        id="unclosed_004",
        name="❌ IF anidado - falta un ENDIF",
        category="unclosed_blocks",
        glspec="""
FUNC test(x: int) -> int:
  IF x > 0:
    IF x > 10:
      RETURN 2
    ENDIF
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT test(5)
END
""",
        should_work=True
    ),
    TestCase(
        id="keyword_001",
        name="❌ FUNCTION en lugar de FUNC",
        category="wrong_keywords",
        glspec="""
FUNCTION suma(a: int, b: int) -> int:
  RETURN a + b
END

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="keyword_002",
        name="❌ def en lugar de FUNC (Python style)",
        category="wrong_keywords",
        glspec="""
def suma(a, b):
  return a + b

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="keyword_003",
        name="❌ ELSEIF en lugar de ELSE + IF",
        category="wrong_keywords",
        glspec="""
FUNC test(x: int) -> int:
  IF x > 10:
    RETURN 2
  ELSEIF x > 0:
    RETURN 1
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT test(5)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="keyword_004",
        name="❌ LOOP en lugar de WHILE",
        category="wrong_keywords",
        glspec="""
MAIN:
  VAR i = 0
  LOOP i < 5:
    PRINT i
    SET i = i + 1
  ENDLOOP
END
""",
        should_work=False
    ),
    TestCase(
        id="nested_001",
        name="IF anidado 3 niveles",
        category="deep_nesting",
        glspec="""
FUNC classify(x: int) -> int:
  IF x > 0:
    IF x > 10:
      IF x > 100:
        RETURN 3
      ELSE:
        RETURN 2
      ENDIF
    ELSE:
      RETURN 1
    ENDIF
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT classify(50)
END
""",
        expected_output="2"
    ),
    
    TestCase(
        id="nested_002",
        name="WHILE dentro de IF dentro de WHILE",
        category="deep_nesting",
        glspec="""
MAIN:
  VAR sum = 0
  VAR i = 1
  WHILE i <= 3:
    IF i > 1:
      VAR j = 1
      WHILE j <= i:
        SET sum = sum + 1
        SET j = j + 1
      ENDWHILE
    ENDIF
    SET i = i + 1
  ENDWHILE
  PRINT sum
END
""",
        expected_output="5"
    ),
    TestCase(
        id="expr_001",
        name="Expresión aritmética compleja",
        category="complex_expressions",
        glspec="""
MAIN:
  VAR result = (3 + 5) * 2 - 10 / 2
  PRINT result
END
""",
        expected_output="11"
    ),
    
    TestCase(
        id="expr_002",
        name="Expresión con múltiples operadores lógicos",
        category="complex_expressions",
        glspec="""
FUNC check(a: int, b: int, c: int) -> int:
  IF a > 0 AND b > 0 OR c > 0:
    RETURN 1
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT check(1, 0, 0)
END
""",
        expected_output="0"
    ),
    
    TestCase(
        id="expr_003",
        name="Precedencia de operadores",
        category="complex_expressions",
        glspec="""
MAIN:
  VAR x = 2 + 3 * 4
  PRINT x
END
""",
        expected_output="14"
    ),
    
    TestCase(
        id="expr_004",
        name="Negación y comparación",
        category="complex_expressions",
        glspec="""
FUNC test(x: int) -> int:
  IF NOT x > 5:
    RETURN 1
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT test(3)
END
""",
        expected_output="1"
    ),
    TestCase(
        id="recursion_001",
        name="Factorial recursivo",
        category="recursion",
        glspec="""
FUNC factorial(n: int) -> int:
  IF n <= 1:
    RETURN 1
  ELSE:
    RETURN n * factorial(n - 1)
  ENDIF
END

MAIN:
  PRINT factorial(5)
END
""",
        expected_output="120"
    ),
    
    TestCase(
        id="recursion_002",
        name="Fibonacci recursivo",
        category="recursion",
        glspec="""
FUNC fib(n: int) -> int:
  IF n <= 1:
    RETURN n
  ELSE:
    RETURN fib(n - 1) + fib(n - 2)
  ENDIF
END

MAIN:
  PRINT fib(10)
END
""",
        expected_output="55"
    ),
    TestCase(
        id="string_001",
        name="String simple",
        category="strings",
        glspec="""
MAIN:
  PRINT "Hello World"
END
""",
        expected_output="Hello World"
    ),
    
    TestCase(
        id="string_002",
        name="❌ String con comillas internas",
        category="strings",
        glspec="""
MAIN:
  PRINT "He said \"hello\""
END
""",
        should_work=False
    ),
    
    TestCase(
        id="string_003",
        name="String vacío",
        category="strings",
        glspec="""
MAIN:
  PRINT ""
END
""",
        expected_output=""
    ),
    TestCase(
        id="number_001",
        name="Número negativo",
        category="numbers",
        glspec="""
MAIN:
  VAR x = -5
  PRINT x
END
""",
        expected_output="-5"
    ),
    
    TestCase(
        id="number_002",
        name="Número decimal",
        category="numbers",
        glspec="""
MAIN:
  VAR x = 3.14
  PRINT x
END
""",
        expected_output="3.14"
    ),
    
    TestCase(
        id="number_003",
        name="Operación con negativos",
        category="numbers",
        glspec="""
MAIN:
  VAR x = 10
  VAR y = -3
  PRINT x + y
END
""",
        expected_output="7"
    ),
    TestCase(
        id="spacing_001",
        name="Sin espacios",
        category="spacing",
        glspec="""
FUNC suma(a:int,b:int)->int:
  RETURN a+b
END

MAIN:
  PRINT suma(1,2)
END
""",
        expected_output="3"
    ),
    
    TestCase(
        id="spacing_002",
        name="Muchos espacios",
        category="spacing",
        glspec="""
FUNC   suma  (  a  :  int  ,  b  :  int  )  ->  int  :
  RETURN   a   +   b
END

MAIN:
  PRINT   suma  (  1  ,  2  )
END
""",
        should_work=True
    ),
    
    TestCase(
        id="spacing_003",
        name="Tabs mezclados",
        category="spacing",
        glspec="FUNC suma(a: int, b: int) -> int:\n\tRETURN a + b\nEND\n\nMAIN:\n\tPRINT suma(1, 2)\nEND",
        expected_output="3"
    ),
    TestCase(
        id="edge_001",
        name="Función sin parámetros",
        category="edge_cases",
        glspec="""
FUNC getOne() -> int:
  RETURN 1
END

MAIN:
  PRINT getOne()
END
""",
        expected_output="1"
    ),
    
    TestCase(
        id="edge_002",
        name="MAIN vacío",
        category="edge_cases",
        glspec="""
MAIN:
END
""",
        should_work=True,
        expected_output=""
    ),
    
    TestCase(
        id="edge_003",
        name="Solo FUNC sin MAIN",
        category="edge_cases",
        glspec="""
FUNC suma(a: int, b: int) -> int:
  RETURN a + b
END
""",
        should_work=True,
        expected_output=""
    ),
    
    TestCase(
        id="edge_004",
        name="Variable no inicializada",
        category="edge_cases",
        glspec="""
MAIN:
  PRINT x
END
""",
        should_work=False
    ),
    
    TestCase(
        id="edge_005",
        name="División por cero",
        category="edge_cases",
        glspec="""
MAIN:
  VAR x = 10 / 0
  PRINT x
END
""",
        should_work=False
    ),
    TestCase(
        id="for_001",
        name="FOR loop básico",
        category="for_loops",
        glspec="""
MAIN:
  VAR sum = 0
  FOR i IN 1..5:
    SET sum = sum + i
  ENDFOR
  PRINT sum
END
""",
        expected_output="15"
    ),
    
    TestCase(
        id="for_002",
        name="FOR con rango inverso",
        category="for_loops",
        glspec="""
MAIN:
  FOR i IN 5..1:
    PRINT i
  ENDFOR
END
""",
        should_work=True,
        expected_output=""
    ),
    TestCase(
        id="multi_001",
        name="Función que llama a función",
        category="multiple_functions",
        glspec="""
FUNC double(x: int) -> int:
  RETURN x * 2
END

FUNC quadruple(x: int) -> int:
  RETURN double(double(x))
END

MAIN:
  PRINT quadruple(5)
END
""",
        expected_output="20"
    ),
    
    TestCase(
        id="multi_002",
        name="Recursión mutua",
        category="multiple_functions",
        glspec="""
FUNC isEven(n: int) -> int:
  IF n == 0:
    RETURN 1
  ELSE:
    RETURN isOdd(n - 1)
  ENDIF
END

FUNC isOdd(n: int) -> int:
  IF n == 0:
    RETURN 0
  ELSE:
    RETURN isEven(n - 1)
  ENDIF
END

MAIN:
  PRINT isEven(4)
END
""",
        expected_output="1"
    ),
    TestCase(
        id="punct_001",
        name="❌ Falta : después de IF",
        category="punctuation",
        glspec="""
FUNC test(x: int) -> int:
  IF x > 0
    RETURN 1
  ELSE:
    RETURN 0
  ENDIF
END

MAIN:
  PRINT test(5)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="punct_002",
        name="❌ Falta : después de FUNC",
        category="punctuation",
        glspec="""
FUNC suma(a: int, b: int) -> int
  RETURN a + b
END

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="punct_003",
        name="❌ Paréntesis no balanceados",
        category="punctuation",
        glspec="""
MAIN:
  VAR x = ((3 + 5) * 2
  PRINT x
END
""",
        should_work=False
    ),
    TestCase(
        id="mod_001",
        name="Operador módulo",
        category="operators",
        glspec="""
MAIN:
  VAR x = 17 % 5
  PRINT x
END
""",
        expected_output="2"
    ),
    TestCase(
        id="bool_001",
        name="Booleano true",
        category="booleans",
        glspec="""
MAIN:
  VAR x = true
  IF x:
    PRINT 1
  ELSE:
    PRINT 0
  ENDIF
END
""",
        expected_output="1"
    ),
    
    TestCase(
        id="bool_002",
        name="Booleano false",
        category="booleans",
        glspec="""
MAIN:
  VAR x = false
  IF x:
    PRINT 1
  ELSE:
    PRINT 0
  ENDIF
END
""",
        expected_output="0"
    ),
    TestCase(
        id="flow_001",
        name="BREAK en WHILE",
        category="flow_control",
        glspec="""
MAIN:
  VAR i = 0
  WHILE i < 10:
    IF i == 5:
      BREAK
    ENDIF
    PRINT i
    SET i = i + 1
  ENDWHILE
END
""",
        expected_output="0\n1\n2\n3\n4"
    ),
    
    TestCase(
        id="flow_002",
        name="CONTINUE en WHILE",
        category="flow_control",
        glspec="""
MAIN:
  VAR i = 0
  VAR sum = 0
  WHILE i < 5:
    SET i = i + 1
    IF i == 3:
      CONTINUE
    ENDIF
    SET sum = sum + i
  ENDWHILE
  PRINT sum
END
""",
        expected_output="12"  # 1 + 2 + 4 + 5 = 12
    ),
    TestCase(
        id="llm_001",
        name="❌ LLM mezcla Python y GLSPEC",
        category="llm_errors",
        glspec="""
FUNC suma(a: int, b: int) -> int:
    return a + b  # Python style
END

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="llm_002",
        name="❌ LLM usa indentación inconsistente",
        category="llm_errors",
        glspec="""
FUNC test(x: int) -> int:
IF x > 0:
RETURN 1
ELSE:
RETURN 0
ENDIF
END

MAIN:
PRINT test(5)
END
""",
        should_work=True
    ),
    
    TestCase(
        id="llm_003",
        name="❌ LLM añade comentarios // style",
        category="llm_errors",
        glspec="""
FUNC suma(a: int, b: int) -> int:  // suma dos números
  RETURN a + b
END

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="llm_004",
        name="❌ LLM olvida tipo en parámetro",
        category="llm_errors",
        glspec="""
FUNC suma(a, b) -> int:
  RETURN a + b
END

MAIN:
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="llm_005",
        name="❌ LLM usa == para asignación",
        category="llm_errors",
        glspec="""
MAIN:
  VAR x == 10
  PRINT x
END
""",
        should_work=False
    ),
    
    TestCase(
        id="llm_006",
        name="❌ LLM escribe MAIN sin :",
        category="llm_errors",
        glspec="""
FUNC suma(a: int, b: int) -> int:
  RETURN a + b
END

MAIN
  PRINT suma(1, 2)
END
""",
        should_work=False
    ),
    
    TestCase(
        id="llm_007",
        name="❌ LLM pone código después de END",
        category="llm_errors",
        glspec="""
FUNC suma(a: int, b: int) -> int:
  RETURN a + b
END

MAIN:
  PRINT suma(1, 2)
END

print("extra code")
""",
        should_work=False
    ),
]

def run_test(test: TestCase, verbose: bool = True) -> TestResult:

    result = TestResult(test=test, success=False)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🧪 {test.id}: {test.name}")
        print(f"   Categoría: {test.category}")
        print(f"   Debería funcionar: {'✅ Sí' if test.should_work else '❌ No'}")
        print(f"{'='*60}")
        print(f"\n📝 GLSPEC Input:")
        print("-"*40)
        for i, line in enumerate(test.glspec.strip().split('\n'), 1):
            print(f"  {i:3}: {line}")
        print("-"*40)
    
    try:
        graph = glspec_to_graph(test.glspec)
        result.glspec_parsed = True
        result.graph_built = True
        if verbose:
            print(f"\n✅ PARSE: OK")
    except Exception as e:
        result.fail_type = FailType.PARSE_ERROR
        result.error_msg = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"\n❌ PARSE ERROR:")
            print(f"   {result.error_msg}")
            traceback.print_exc()
        
        if not test.should_work:
            result.success = True
            if verbose:
                print(f"\n✅ RESULTADO: Esperado (debía fallar y falló)")
        return result
    try:
        translator = PythonTranslator()
        code = translator.translate(graph)
        result.code_generated = code
        if verbose:
            print(f"\n✅ TRANSLATE: OK")
            print(f"\n🐍 Python generado:")
            print("-"*40)
            for i, line in enumerate(code.split('\n'), 1):
                print(f"  {i:3}: {line}")
            print("-"*40)
    except Exception as e:
        result.fail_type = FailType.TRANSLATE_ERROR
        result.error_msg = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"\n❌ TRANSLATE ERROR:")
            print(f"   {result.error_msg}")
        
        if not test.should_work:
            result.success = True
        return result
    try:
        import io
        from contextlib import redirect_stdout
        
        output_buffer = io.StringIO()
        exec_globals = {"__builtins__": __builtins__}
        
        with redirect_stdout(output_buffer):
            exec(code, exec_globals)
        
        result.actual_output = output_buffer.getvalue().strip()
        result.code_ran = True
        
        if verbose:
            print(f"\n✅ EXEC: OK")
            print(f"\n📤 Output: '{result.actual_output}'")
            
    except Exception as e:
        result.fail_type = FailType.EXEC_ERROR
        result.error_msg = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"\n❌ EXEC ERROR:")
            print(f"   {result.error_msg}")
        
        if not test.should_work:
            result.success = True
        return result
    
    # 4. Verificar output
    if test.expected_output is not None:
        if result.actual_output == test.expected_output:
            result.success = True
            if verbose:
                print(f"\n✅ OUTPUT MATCH!")
        else:
            result.fail_type = FailType.WRONG_OUTPUT
            result.error_msg = f"Expected '{test.expected_output}', got '{result.actual_output}'"
            if verbose:
                print(f"\n❌ OUTPUT MISMATCH:")
                print(f"   Expected: '{test.expected_output}'")
                print(f"   Got:      '{result.actual_output}'")
    else:
        # No hay expected output definido
        if test.should_work:
            result.success = result.code_ran
        else:
            # Debería haber fallado pero no falló
            result.success = False
            result.fail_type = FailType.WRONG_OUTPUT
            result.error_msg = "Test debería fallar pero pasó"
            if verbose:
                print(f"\n⚠️ Test debería haber fallado pero pasó!")
    
    if verbose:
        if result.success:
            print(f"\n{'='*60}")
            print(f"✅ TEST PASSED: {test.id}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"❌ TEST FAILED: {test.id}")
            print(f"{'='*60}")
    
    return result


def run_all_tests(verbose: bool = True, category_filter: str = None):
    """Ejecuta todos los tests"""
    
    tests = TESTS
    if category_filter:
        tests = [t for t in TESTS if t.category == category_filter]
    
    print(f"\n{'#'*60}")
    print(f"# 🔥 GLSPEC STRESS TEST - {len(tests)} casos")
    print(f"{'#'*60}")
    
    results = []
    for test in tests:
        result = run_test(test, verbose=verbose)
        results.append(result)
    
    # Resumen
    print(f"\n\n{'='*60}")
    print(f"📊 RESUMEN DE RESULTADOS")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"📈 Success rate: {passed/len(results)*100:.1f}%")
    
    # Desglose por categoría
    print(f"\n📂 Por categoría:")
    categories = {}
    for r in results:
        cat = r.test.category
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0}
        if r.success:
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1
    
    for cat, stats in sorted(categories.items()):
        total = stats['passed'] + stats['failed']
        rate = stats['passed'] / total * 100
        emoji = "✅" if rate == 100 else "⚠️" if rate >= 50 else "❌"
        print(f"   {emoji} {cat}: {stats['passed']}/{total} ({rate:.0f}%)")
    
    # Lista de fallos
    failures = [r for r in results if not r.success]
    if failures:
        print(f"\n❌ TESTS FALLIDOS:")
        print("-"*60)
        for r in failures:
            print(f"\n🔴 {r.test.id}: {r.test.name}")
            print(f"   Categoría: {r.test.category}")
            print(f"   Tipo de fallo: {r.fail_type}")
            print(f"   Error: {r.error_msg}")
    
    # Casos que deberían fallar pero pasaron
    unexpected_passes = [r for r in results if r.success and not r.test.should_work]
    if unexpected_passes:
        print(f"\n⚠️ TESTS QUE DEBERÍAN FALLAR PERO PASARON:")
        print("-"*60)
        for r in unexpected_passes:
            print(f"   ⚠️ {r.test.id}: {r.test.name}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='GLSPEC Stress Test')
    parser.add_argument('--quiet', '-q', action='store_true', help='Modo silencioso')
    parser.add_argument('--category', '-c', type=str, help='Filtrar por categoría')
    parser.add_argument('--test', '-t', type=str, help='Ejecutar solo un test por ID')
    parser.add_argument('--list', '-l', action='store_true', help='Listar todos los tests')
    
    args = parser.parse_args()
    
    if args.list:
        print("📋 Tests disponibles:")
        for t in TESTS:
            emoji = "✅" if t.should_work else "❌"
            print(f"   {emoji} {t.id}: {t.name} [{t.category}]")
        sys.exit(0)
    
    if args.test:
        test = next((t for t in TESTS if t.id == args.test), None)
        if test:
            run_test(test, verbose=True)
        else:
            print(f"Test '{args.test}' no encontrado")
        sys.exit(0)
    
    run_all_tests(verbose=not args.quiet, category_filter=args.category)
