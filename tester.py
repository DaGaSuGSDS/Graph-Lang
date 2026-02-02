import argparse
import json
import time
from collections import Counter, defaultdict

from run_program import DslGenerator, compile_user_text


# ---------- Suite de pruebas (ampliable) ----------

TESTS = [
    # Básicos
    {"id": "sum_es_1", "text": "Crea una funcion suma que reciba a y b y devuelva a+b", "lang": "py"},
    {"id": "sum_es_2", "text": "haz una función llamada suma con a y b y retorna a + b", "lang": "js"},
    {"id": "sum_en_1", "text": "create a function sum(a,b) that returns a+b", "lang": "c"},

    # Variación de estilo / ruido
    {"id": "mul_es_1", "text": "quiero una funcion multiplica con a y b devuelve a*b", "lang": "py"},
    {"id": "sub_es_1", "text": "define resta(a,b) retorna a-b", "lang": "js"},
    {"id": "div_es_1", "text": "haz division segura: si b es 0 devuelve 0 si no a/b", "lang": "py"},

    # Condicional
    {"id": "if_es_1", "text": "Crea una funcion abs(x) si x es menor que 0 devuelve -x si no devuelve x", "lang": "py"},
    {"id": "max_es_1", "text": "Haz una funcion max2(a,b): si a>b retorna a si no retorna b", "lang": "js"},

    # Variables y returns simples
    {"id": "var_es_1", "text": "en una funcion demo crea una variable x=10 y devuelve x", "lang": "py"},
    {"id": "var_es_2", "text": "funcion demo: define x=10 luego x=x+5 y retorna x", "lang": "js"},

    # Calls
    {"id": "call_es_1", "text": "Crea funcion suma(a,b) devuelve a+b y luego llama suma(10,20)", "lang": "py"},
    {"id": "call_es_2", "text": "Define inc(x) devuelve x+1 y llama inc(41)", "lang": "js"},

    # Renombrados / intentos típicos
    {"id": "rename_es_1", "text": "Crea una funcion add(a,b) y luego renombra add a suma", "lang": "py"},

    # English mix
    {"id": "mix_1", "text": "make a function 'area' that takes r and returns 3.14*r*r", "lang": "py"},
    {"id": "mix_2", "text": "haz function clamp(x) if x<0 return 0 if x>1 return 1 else return x", "lang": "js"},

    # Edge-ish
    {"id": "edge_1", "text": "funcion identidad(x) devuelve x", "lang": "c"},
    {"id": "edge_2", "text": "una funcion que siempre devuelve 1", "lang": "py"},
]

# Para “muchas pruebas”, generamos variantes automáticamente
def expand_tests(base_tests, n_variants=12):
    variants = []
    templates = [
        "Crea una funcion {name}({args}) que devuelva {expr}",
        "Haz {name} con {args} retorna {expr}",
        "Define {name}({args}) => {expr}",
        "Necesito una función {name} que recibe {args} y devuelve {expr}",
        "create function {name}({args}) return {expr}",
    ]
    pool = [
        ("suma", "a,b", "a + b"),
        ("resta", "a,b", "a - b"),
        ("mul", "a,b", "a * b"),
        ("cuadrado", "x", "x * x"),
        ("area", "r", "3.14 * r * r"),
        ("inc", "x", "x + 1"),
        ("dec", "x", "x - 1"),
    ]
    idx = 0
    for t in templates:
        for (name, args, expr) in pool:
            idx += 1
            variants.append({
                "id": f"auto_{idx}",
                "text": t.format(name=name, args=args, expr=expr),
                "lang": "py" if idx % 3 == 0 else ("js" if idx % 3 == 1 else "c"),
            })
            if len(variants) >= n_variants * len(pool):
                return base_tests + variants
    return base_tests + variants

BIG_TESTS = expand_tests(TESTS, n_variants=20)


# ---------- Runner ----------

def run_suite(model_dir: str, max_new_tokens: int, limit: int | None = None):
    gen = DslGenerator(model_dir)

    tests = BIG_TESTS if limit is None else BIG_TESTS[:limit]
    stats = Counter()
    failures = []

    t0 = time.time()
    for t in tests:
        out = compile_user_text(gen, t["text"], t["lang"], max_new_tokens=max_new_tokens)

        stats["total"] += 1

        # checks
        glspec = out.get("glspec", "")
        if glspec.endswith("END") or "\nEND" in glspec:
            stats["has_end"] += 1
        else:
            stats["no_end"] += 1

        if out["graph_ok"]:
            stats["graph_ok"] += 1
            # code should exist
            if out.get("code"):
                stats["code_ok"] += 1
            else:
                stats["code_missing"] += 1
                failures.append({
                    "id": t["id"],
                    "text": t["text"],
                    "lang": t["lang"],
                    "glspec": glspec,
                    "error": "code missing though graph_ok",
                })
        else:
            stats["graph_fail"] += 1
            failures.append({
                "id": t["id"],
                "text": t["text"],
                "lang": t["lang"],
                "glspec": glspec,
                "error": out.get("error"),
            })

    dt = time.time() - t0
    report = {
        "model_dir": model_dir,
        "max_new_tokens": max_new_tokens,
        "elapsed_s": dt,
        "stats": dict(stats),
        "rates": {
            "has_end": stats["has_end"] / max(1, stats["total"]),
            "graph_ok": stats["graph_ok"] / max(1, stats["total"]),
            "code_ok": stats["code_ok"] / max(1, stats["total"]),
        },
        "failures": failures[:200],  # cap para que no sea enorme
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="out_minillama_lora/final")
    ap.add_argument("--max_new_tokens", type=int, default=180)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="report.json")
    args = ap.parse_args()

    report = run_suite(args.model, args.max_new_tokens, args.limit)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=== REPORT ===")
    print(json.dumps({k: report[k] for k in ["stats", "rates", "elapsed_s"]}, ensure_ascii=False, indent=2))
    print(f"\nSaved: {args.out}")
    if report["failures"]:
        print(f"Failures (showing up to 5/{len(report['failures'])}):")
        for row in report["failures"][:5]:
            print("-", row["id"], "=>", row["error"])


if __name__ == "__main__":
    main()
