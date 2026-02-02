#!/usr/bin/env python3
"""
Graph-Lang Demo - Demostración completa del sistema
====================================================

Ejecuta: python main.py
"""

from graph_lang import (
    G, GraphSerializer,
    GLSpecParser, GLSpecToGraph, glspec_to_graph,
    JSTranslator, PythonTranslator, CTranslator
)
from graph_lang.dataset import DatasetGenerator, DATASET_GENERATION_PROMPT


def demo_basic():
    """Demo básico: construir grafo programáticamente"""
    print("=" * 60)
    print("1️⃣  DEMO: Construir grafo programáticamente")
    print("=" * 60)
    
    # Crear: x = 10; x = x + 1; print(x)
    prog = (G.program("incremento")
        .entry(
            G.def_var('x', 10)
            .then(G.set('x', G.add('x', 1)))
            .then(G.print_('x'))
        ))
    
    serializer = GraphSerializer()
    print("\n📊 Grafo serializado:")
    print(serializer.serialize(prog))
    
    print("\n🟨 JavaScript:")
    js = JSTranslator().translate(prog)
    print(js)
    
    print("\n🐍 Python:")
    py = PythonTranslator().translate(prog)
    print(py)


def demo_glspec():
    """Demo GLSPEC: convertir pseudo-código a grafo"""
    print("\n" + "=" * 60)
    print("2️⃣  DEMO: GLSPEC → Grafo → Código")
    print("=" * 60)
    
    glspec = """
FUNC factorial(n: int) -> int:
  IF n <= 1:
    RETURN 1
  ELSE:
    RETURN n * factorial(n - 1)
  ENDIF
END

MAIN:
  PRINT factorial(6)
END
"""
    
    print("\n📥 GLSPEC Input:")
    print(glspec)
    
    # Convertir
    program = glspec_to_graph(glspec)
    
    # Serializar
    serializer = GraphSerializer()
    print("\n📊 Grafo generado:")
    print(serializer.serialize(program))
    
    # Traducir
    print("\n🟨 JavaScript:")
    print(JSTranslator().translate(program))
    
    print("\n🐍 Python:")
    py_code = PythonTranslator().translate(program)
    print(py_code)
    
    # Ejecutar Python
    print("\n🚀 Ejecutando Python:")
    exec(py_code, {"__builtins__": __builtins__})


def demo_fizzbuzz():
    """Demo FizzBuzz completo"""
    print("\n" + "=" * 60)
    print("3️⃣  DEMO: FizzBuzz completo")
    print("=" * 60)
    
    glspec = """
FUNC esDivisible(n: int, d: int) -> bool:
  RETURN n % d == 0
END

MAIN:
  VAR i = 1
  WHILE i <= 15:
    IF esDivisible(i, 15):
      PRINT "FizzBuzz"
    ELSE:
      IF esDivisible(i, 3):
        PRINT "Fizz"
      ELSE:
        IF esDivisible(i, 5):
          PRINT "Buzz"
        ELSE:
          PRINT i
        ENDIF
      ENDIF
    ENDIF
    SET i = i + 1
  ENDWHILE
END
"""
    
    print("\n📥 GLSPEC:")
    print(glspec)
    
    program = glspec_to_graph(glspec)
    
    print("\n🐍 Python generado:")
    py_code = PythonTranslator().translate(program)
    print(py_code)
    
    print("\n🚀 Ejecutando:")
    exec(py_code, {"__builtins__": __builtins__})


def demo_dataset():
    """Demo generación de dataset"""
    print("\n" + "=" * 60)
    print("4️⃣  DEMO: Generación de Dataset")
    print("=" * 60)
    
    generator = DatasetGenerator()
    
    # Estadísticas
    stats = generator.get_statistics()
    print(f"\n📊 Estadísticas del dataset:")
    print(f"   Total ejemplos base: {stats['total_examples']}")
    print(f"   Total con variantes: {stats['total_with_variants']}")
    print(f"   Categorías: {stats['categories']}")
    
    # Generar
    minillama_data = generator.generate_minillama_dataset()
    graphgen_data = generator.generate_graphgen_dataset()
    
    print(f"\n📁 Dataset MiniLlama: {len(minillama_data)} ejemplos")
    print(f"📁 Dataset GraphGen: {len(graphgen_data)} ejemplos")
    
    # Mostrar ejemplos
    print("\n--- Ejemplo MiniLlama ---")
    ex = minillama_data[5]
    print(f"Input: {ex['instruction']}")
    print(f"Output:\n{ex['output']}")
    
    print("\n--- Ejemplo GraphGen ---")
    ex = graphgen_data[5]
    print(f"Input:\n{ex['input']}")
    print(f"Output:\n{ex['output']}")
    
    # Guardar datasets
    generator.export_jsonl(minillama_data, "dataset_minillama.jsonl")
    generator.export_jsonl(graphgen_data, "dataset_graphgen.jsonl")
    print("\n✅ Datasets guardados:")
    print("   - dataset_minillama.jsonl")
    print("   - dataset_graphgen.jsonl")


def show_prompt():
    """Muestra el prompt para generar más datos"""
    print("\n" + "=" * 60)
    print("5️⃣  PROMPT PARA GENERAR MÁS DATOS")
    print("=" * 60)
    
    prompt = DATASET_GENERATION_PROMPT.replace("{N}", "50")
    
    print("\n📝 Usa este prompt con Claude/GPT para generar más ejemplos:\n")
    print("-" * 60)
    print(prompt[:2000] + "...\n")
    print("-" * 60)
    print("\n💡 El prompt completo está en: graph_lang/dataset.py")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    GRAPH-LANG v2 (Python)                    ║
╠══════════════════════════════════════════════════════════════╣
║  Sistema de programación basado en grafos dirigidos          ║
║                                                              ║
║  Pipeline:                                                   ║
║  Usuario → MiniLlama → GLSPEC → GraphGen → Grafo → Código   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    demo_basic()
    demo_glspec()
    demo_fizzbuzz()
    demo_dataset()
    show_prompt()
    
    print("\n" + "=" * 60)
    print("✅ Demo completado!")
    print("=" * 60)


if __name__ == "__main__":
    main()
