"""
Dataset Generator - Genera datos de entrenamiento para MiniLlama y GraphGen
============================================================================

Formatos de salida:
- JSONL para fine-tuning
- Pares (natural, GLSPEC) para MiniLlama
- Pares (GLSPEC, Grafo) para GraphGen
"""

import json
import random
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

from .core import G, GraphSerializer
from .glspec_parser import glspec_to_graph


# ============================================================
# TEMPLATES DE EJEMPLOS
# ============================================================

@dataclass
class Example:
    """Un ejemplo de entrenamiento"""
    natural: str          # Descripción en lenguaje natural
    natural_variants: List[str]  # Variantes de la descripción
    glspec: str           # Código GLSPEC
    category: str         # Categoría del ejemplo


# Ejemplos base organizados por categoría
EXAMPLES: List[Example] = [
    
    # ==================== FUNCIONES MATEMÁTICAS ====================
    
    Example(
        natural="función que suma dos números",
        natural_variants=[
            "crea una función para sumar dos números",
            "quiero una función que sume a y b",
            "función suma de dos valores",
            "haz una función que reciba dos números y los sume",
            "necesito sumar dos números en una función",
        ],
        glspec="""FUNC suma(a: int, b: int) -> int:
  RETURN a + b
END""",
        category="math"
    ),
    
    Example(
        natural="función que resta dos números",
        natural_variants=[
            "función para restar b de a",
            "quiero restar dos valores",
            "crea función de resta",
        ],
        glspec="""FUNC resta(a: int, b: int) -> int:
  RETURN a - b
END""",
        category="math"
    ),
    
    Example(
        natural="función que multiplica dos números",
        natural_variants=[
            "multiplicar a por b",
            "función de multiplicación",
            "producto de dos números",
        ],
        glspec="""FUNC multiplica(a: int, b: int) -> int:
  RETURN a * b
END""",
        category="math"
    ),
    
    Example(
        natural="función que divide dos números",
        natural_variants=[
            "dividir a entre b",
            "función de división",
            "cociente de dos números",
        ],
        glspec="""FUNC divide(a: int, b: int) -> int:
  RETURN a / b
END""",
        category="math"
    ),
    
    Example(
        natural="función que calcula el módulo",
        natural_variants=[
            "resto de la división",
            "módulo de a entre b",
            "función módulo",
        ],
        glspec="""FUNC modulo(a: int, b: int) -> int:
  RETURN a % b
END""",
        category="math"
    ),
    
    Example(
        natural="función que calcula el promedio de dos números",
        natural_variants=[
            "promedio de a y b",
            "media de dos valores",
            "calcular promedio",
        ],
        glspec="""FUNC promedio(a: int, b: int) -> float:
  RETURN (a + b) / 2
END""",
        category="math"
    ),
    
    Example(
        natural="función que calcula el cuadrado de un número",
        natural_variants=[
            "elevar al cuadrado",
            "número al cuadrado",
            "x^2",
            "cuadrado de x",
        ],
        glspec="""FUNC cuadrado(x: int) -> int:
  RETURN x * x
END""",
        category="math"
    ),
    
    Example(
        natural="función que calcula el cubo de un número",
        natural_variants=[
            "elevar al cubo",
            "x^3",
            "cubo de x",
        ],
        glspec="""FUNC cubo(x: int) -> int:
  RETURN x * x * x
END""",
        category="math"
    ),
    
    # ==================== FUNCIONES CON CONDICIONALES ====================
    
    Example(
        natural="función que retorna el máximo de dos números",
        natural_variants=[
            "máximo entre a y b",
            "el mayor de dos números",
            "función max",
            "encontrar el más grande",
        ],
        glspec="""FUNC max(a: int, b: int) -> int:
  IF a > b:
    RETURN a
  ELSE:
    RETURN b
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que retorna el mínimo de dos números",
        natural_variants=[
            "mínimo entre a y b",
            "el menor de dos números",
            "función min",
        ],
        glspec="""FUNC min(a: int, b: int) -> int:
  IF a < b:
    RETURN a
  ELSE:
    RETURN b
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que retorna el valor absoluto",
        natural_variants=[
            "valor absoluto de x",
            "abs de un número",
            "quitar signo negativo",
        ],
        glspec="""FUNC abs(x: int) -> int:
  IF x < 0:
    RETURN 0 - x
  ELSE:
    RETURN x
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que verifica si un número es positivo",
        natural_variants=[
            "es positivo",
            "comprobar si es mayor que cero",
            "número positivo",
        ],
        glspec="""FUNC esPositivo(x: int) -> bool:
  IF x > 0:
    RETURN true
  ELSE:
    RETURN false
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que verifica si un número es par",
        natural_variants=[
            "es par",
            "comprobar si es divisible por 2",
            "número par",
        ],
        glspec="""FUNC esPar(n: int) -> bool:
  IF n % 2 == 0:
    RETURN true
  ELSE:
    RETURN false
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que verifica si un número es impar",
        natural_variants=[
            "es impar",
            "no es par",
            "número impar",
        ],
        glspec="""FUNC esImpar(n: int) -> bool:
  IF n % 2 != 0:
    RETURN true
  ELSE:
    RETURN false
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que verifica si un número está en un rango",
        natural_variants=[
            "está entre min y max",
            "dentro del rango",
            "verificar rango",
        ],
        glspec="""FUNC enRango(x: int, min: int, max: int) -> bool:
  IF x >= min AND x <= max:
    RETURN true
  ELSE:
    RETURN false
  ENDIF
END""",
        category="conditional"
    ),
    
    Example(
        natural="función que retorna el signo de un número",
        natural_variants=[
            "signo de x",
            "-1, 0 o 1 según el signo",
            "función signo",
        ],
        glspec="""FUNC signo(x: int) -> int:
  IF x > 0:
    RETURN 1
  ELSE:
    IF x < 0:
      RETURN 0 - 1
    ELSE:
      RETURN 0
    ENDIF
  ENDIF
END""",
        category="conditional"
    ),
    
    # ==================== FUNCIONES RECURSIVAS ====================
    
    Example(
        natural="función factorial recursiva",
        natural_variants=[
            "factorial de n",
            "calcular n!",
            "factorial recursivo",
        ],
        glspec="""FUNC factorial(n: int) -> int:
  IF n <= 1:
    RETURN 1
  ELSE:
    RETURN n * factorial(n - 1)
  ENDIF
END""",
        category="recursive"
    ),
    
    Example(
        natural="función fibonacci recursiva",
        natural_variants=[
            "fibonacci de n",
            "secuencia fibonacci",
            "número fibonacci",
        ],
        glspec="""FUNC fibonacci(n: int) -> int:
  IF n <= 1:
    RETURN n
  ELSE:
    RETURN fibonacci(n - 1) + fibonacci(n - 2)
  ENDIF
END""",
        category="recursive"
    ),
    
    Example(
        natural="función que suma números del 1 al n recursivamente",
        natural_variants=[
            "suma recursiva hasta n",
            "sumar 1 a n recursivo",
        ],
        glspec="""FUNC sumaHasta(n: int) -> int:
  IF n <= 0:
    RETURN 0
  ELSE:
    RETURN n + sumaHasta(n - 1)
  ENDIF
END""",
        category="recursive"
    ),
    
    # ==================== BUCLES ====================
    
    Example(
        natural="función que calcula potencia con bucle",
        natural_variants=[
            "base elevado a exponente",
            "potencia iterativa",
            "calcular x^n con while",
        ],
        glspec="""FUNC potencia(base: int, exp: int) -> int:
  VAR result = 1
  VAR i = 0
  WHILE i < exp:
    SET result = result * base
    SET i = i + 1
  ENDWHILE
  RETURN result
END""",
        category="loop"
    ),
    
    Example(
        natural="función factorial con bucle",
        natural_variants=[
            "factorial iterativo",
            "factorial sin recursión",
            "calcular factorial con while",
        ],
        glspec="""FUNC factorialLoop(n: int) -> int:
  VAR result = 1
  VAR i = 1
  WHILE i <= n:
    SET result = result * i
    SET i = i + 1
  ENDWHILE
  RETURN result
END""",
        category="loop"
    ),
    
    Example(
        natural="función que cuenta dígitos de un número",
        natural_variants=[
            "número de dígitos",
            "cuántos dígitos tiene",
            "longitud de un número",
        ],
        glspec="""FUNC contarDigitos(n: int) -> int:
  VAR count = 0
  VAR num = n
  WHILE num > 0:
    SET count = count + 1
    SET num = num / 10
  ENDWHILE
  RETURN count
END""",
        category="loop"
    ),
    
    Example(
        natural="función que suma los dígitos de un número",
        natural_variants=[
            "suma de dígitos",
            "sumar cada dígito",
        ],
        glspec="""FUNC sumaDigitos(n: int) -> int:
  VAR suma = 0
  VAR num = n
  WHILE num > 0:
    SET suma = suma + num % 10
    SET num = num / 10
  ENDWHILE
  RETURN suma
END""",
        category="loop"
    ),
    
    # ==================== PROGRAMAS COMPLETOS ====================
    
    Example(
        natural="imprimir números del 1 al 10",
        natural_variants=[
            "mostrar números 1 a 10",
            "print 1 to 10",
            "listar del uno al diez",
        ],
        glspec="""MAIN:
  VAR i = 1
  WHILE i <= 10:
    PRINT i
    SET i = i + 1
  ENDWHILE
END""",
        category="program"
    ),
    
    Example(
        natural="imprimir números pares del 2 al 20",
        natural_variants=[
            "mostrar pares hasta 20",
            "números pares",
        ],
        glspec="""MAIN:
  VAR i = 2
  WHILE i <= 20:
    PRINT i
    SET i = i + 2
  ENDWHILE
END""",
        category="program"
    ),
    
    Example(
        natural="fizzbuzz del 1 al 15",
        natural_variants=[
            "hacer fizzbuzz",
            "fizz buzz clásico",
            "juego fizzbuzz",
        ],
        glspec="""FUNC esDivisible(n: int, d: int) -> bool:
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
END""",
        category="program"
    ),
    
    Example(
        natural="calcular e imprimir factorial de 5",
        natural_variants=[
            "factorial de 5",
            "5!",
            "imprimir 5 factorial",
        ],
        glspec="""FUNC factorial(n: int) -> int:
  IF n <= 1:
    RETURN 1
  ELSE:
    RETURN n * factorial(n - 1)
  ENDIF
END

MAIN:
  PRINT factorial(5)
END""",
        category="program"
    ),
    
    # ==================== FINANZAS ====================
    
    Example(
        natural="función que calcula el IVA",
        natural_variants=[
            "calcular IVA de un precio",
            "impuesto IVA",
            "21% de IVA",
        ],
        glspec="""FUNC calcularIVA(precio: float) -> float:
  RETURN precio * 0.21
END""",
        category="finance"
    ),
    
    Example(
        natural="función que calcula precio con IVA",
        natural_variants=[
            "precio total con IVA",
            "añadir IVA al precio",
        ],
        glspec="""FUNC precioConIVA(precio: float) -> float:
  RETURN precio + precio * 0.21
END""",
        category="finance"
    ),
    
    Example(
        natural="función que calcula porcentaje",
        natural_variants=[
            "porcentaje de un número",
            "calcular tanto por ciento",
            "x% de cantidad",
        ],
        glspec="""FUNC porcentaje(cantidad: float, pct: float) -> float:
  RETURN cantidad * pct / 100
END""",
        category="finance"
    ),
    
    Example(
        natural="función que calcula descuento",
        natural_variants=[
            "aplicar descuento",
            "precio con descuento",
            "restar porcentaje",
        ],
        glspec="""FUNC aplicarDescuento(precio: float, descuento: float) -> float:
  RETURN precio - precio * descuento / 100
END""",
        category="finance"
    ),
]


# ============================================================
# GENERADOR DE DATASET
# ============================================================

class DatasetGenerator:
    """Genera datasets de entrenamiento"""
    
    def __init__(self, examples: List[Example] = None):
        self.examples = examples or EXAMPLES
        self.serializer = GraphSerializer()
    
    def generate_minillama_dataset(self, include_variants: bool = True) -> List[Dict]:
        """
        Genera dataset para entrenar MiniLlama.
        Formato: (natural, GLSPEC)
        """
        dataset = []
        
        for ex in self.examples:
            # Ejemplo principal
            dataset.append({
                "instruction": ex.natural,
                "output": ex.glspec.strip(),
                "category": ex.category
            })
            
            # Variantes
            if include_variants:
                for variant in ex.natural_variants:
                    dataset.append({
                        "instruction": variant,
                        "output": ex.glspec.strip(),
                        "category": ex.category
                    })
        
        return dataset
    
    def generate_graphgen_dataset(self) -> List[Dict]:
        """
        Genera dataset para entrenar GraphGen.
        Formato: (GLSPEC, Grafo)
        """
        dataset = []
        
        for ex in self.examples:
            try:
                program = glspec_to_graph(ex.glspec)
                graph_str = self.serializer.serialize(program)
                
                dataset.append({
                    "input": ex.glspec.strip(),
                    "output": graph_str,
                    "category": ex.category
                })
            except Exception as e:
                print(f"Warning: Could not convert example '{ex.natural}': {e}")
        
        return dataset
    
    def export_jsonl(self, dataset: List[Dict], filepath: str):
        """Exporta dataset a formato JSONL"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in dataset:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas del dataset"""
        categories = {}
        total_variants = 0
        
        for ex in self.examples:
            cat = ex.category
            categories[cat] = categories.get(cat, 0) + 1
            total_variants += len(ex.natural_variants)
        
        return {
            "total_examples": len(self.examples),
            "total_with_variants": len(self.examples) + total_variants,
            "categories": categories
        }


# ============================================================
# PROMPT PARA GENERAR MÁS EJEMPLOS
# ============================================================

DATASET_GENERATION_PROMPT = '''
Eres un generador de datos de entrenamiento para un sistema de programación basado en grafos.

Tu tarea es generar ejemplos en el formato GLSPEC (pseudo-código estructurado).

## FORMATO GLSPEC

Vocabulario fijo (~47 tokens):
- Palabras clave: FUNC, END, VAR, SET, IF, ELSE, ENDIF, WHILE, ENDWHILE, FOR, IN, ENDFOR, RETURN, PRINT, CALL, BREAK, CONTINUE, MAIN, AND, OR, NOT, true, false
- Tipos: int, float, str, bool, void, any
- Operadores: +, -, *, /, %, ==, !=, <, >, <=, >=

## ESTRUCTURA

```
FUNC nombre(param1: tipo, param2: tipo) -> tipo_retorno:
  VAR variable = expresion
  SET variable = expresion
  IF condicion:
    instrucciones
  ELSE:
    instrucciones
  ENDIF
  WHILE condicion:
    instrucciones
  ENDWHILE
  RETURN expresion
  PRINT expresion
END

MAIN:
  instrucciones
END
```

## FORMATO DE SALIDA

Para cada ejemplo, genera un JSON con:
```json
{
  "natural": "descripción en lenguaje natural",
  "natural_variants": ["variante 1", "variante 2", "variante 3"],
  "glspec": "código GLSPEC",
  "category": "categoría"
}
```

## CATEGORÍAS

- math: funciones matemáticas simples
- conditional: funciones con if/else
- recursive: funciones recursivas
- loop: funciones con bucles
- program: programas completos con MAIN
- finance: cálculos financieros
- string: manipulación de texto (conceptual)
- validation: validaciones y comprobaciones

## EJEMPLOS DE REFERENCIA

### Math
```json
{
  "natural": "función que calcula el doble de un número",
  "natural_variants": ["duplicar un número", "multiplicar por 2", "x * 2"],
  "glspec": "FUNC doble(x: int) -> int:\\n  RETURN x * 2\\nEND",
  "category": "math"
}
```

### Conditional
```json
{
  "natural": "función que verifica si un número es negativo",
  "natural_variants": ["es negativo", "menor que cero", "número negativo"],
  "glspec": "FUNC esNegativo(x: int) -> bool:\\n  IF x < 0:\\n    RETURN true\\n  ELSE:\\n    RETURN false\\n  ENDIF\\nEND",
  "category": "conditional"
}
```

### Loop
```json
{
  "natural": "función que calcula la suma de 1 a n",
  "natural_variants": ["sumar hasta n", "suma acumulada", "1+2+...+n"],
  "glspec": "FUNC sumaHasta(n: int) -> int:\\n  VAR suma = 0\\n  VAR i = 1\\n  WHILE i <= n:\\n    SET suma = suma + i\\n    SET i = i + 1\\n  ENDWHILE\\n  RETURN suma\\nEND",
  "category": "loop"
}
```

## INSTRUCCIONES

1. Genera {N} ejemplos NUEVOS y DIVERSOS
2. Varía las categorías equitativamente
3. Incluye al menos 3 variantes naturales por ejemplo
4. Asegúrate de que el GLSPEC sea sintácticamente correcto
5. Usa nombres de funciones y variables en español
6. Responde SOLO con un array JSON de ejemplos

## GENERA {N} EJEMPLOS:
'''.strip()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    generator = DatasetGenerator()
    
    print("=" * 60)
    print("DATASET GENERATOR - Graph-Lang")
    print("=" * 60)
    
    # Estadísticas
    stats = generator.get_statistics()
    print(f"\n📊 Estadísticas:")
    print(f"   Total ejemplos base: {stats['total_examples']}")
    print(f"   Total con variantes: {stats['total_with_variants']}")
    print(f"   Categorías: {stats['categories']}")
    
    # Generar datasets
    minillama_data = generator.generate_minillama_dataset()
    graphgen_data = generator.generate_graphgen_dataset()
    
    print(f"\n📁 Dataset MiniLlama: {len(minillama_data)} ejemplos")
    print(f"📁 Dataset GraphGen: {len(graphgen_data)} ejemplos")
    
    # Mostrar algunos ejemplos
    print("\n" + "=" * 60)
    print("EJEMPLOS MINILLAMA (natural → GLSPEC):")
    print("=" * 60)
    for ex in minillama_data[:3]:
        print(f"\n🎯 Input: {ex['instruction']}")
        print(f"📝 Output:\n{ex['output']}")
    
    print("\n" + "=" * 60)
    print("EJEMPLOS GRAPHGEN (GLSPEC → Grafo):")
    print("=" * 60)
    for ex in graphgen_data[:3]:
        print(f"\n📥 Input:\n{ex['input']}")
        print(f"\n📤 Output:\n{ex['output']}")
    
    # Prompt para generar más
    print("\n" + "=" * 60)
    print("PROMPT PARA GENERAR MÁS EJEMPLOS:")
    print("=" * 60)
    print("\nUsa este prompt con Claude/GPT para generar más ejemplos:")
    print("-" * 40)
    print(DATASET_GENERATION_PROMPT.replace("{N}", "20"))
