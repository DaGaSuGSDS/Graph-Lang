import argparse
import json
import re
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from graph_lang import glspec_to_graph, PythonTranslator, JSTranslator, CTranslator


# ---------- Utilidades GLSPEC ----------

def extract_glspec(text: str) -> str:
    """
    Recorta el output del modelo para quedarnos SOLO con el bloque GLSPEC
    terminando en END. Basado en tu enfoque que ya te funcionó. :contentReference[oaicite:1]{index=1}
    """
    if "### OUTPUT:" in text:
        text = text.split("### OUTPUT:", 1)[1].strip()

    # Corta en la primera aparición de "\nEND"
    if "\nEND" in text:
        text = text.split("\nEND", 1)[0].rstrip() + "\nEND"

    return text.strip()


def normalize_glspec(glspec: str) -> str:
    """
    Normaliza espacios y saltos de línea para que el parser sea más robusto.
    """
    glspec = glspec.replace("\r\n", "\n").replace("\r", "\n").strip()
    # quita trailing spaces
    glspec = "\n".join(line.rstrip() for line in glspec.split("\n"))
    return glspec


# ---------- Inferencia ----------

class DslGenerator:
    def __init__(self, model_dir: str):
        self.tok = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            device_map="auto",
            torch_dtype="auto",
        )

    def to_glspec(self, user_text: str, max_new_tokens: int = 160) -> str:
        prompt = f"### INPUT:\n{user_text}\n\n### OUTPUT:\n"
        x = self.tok(prompt, return_tensors="pt").to(self.model.device)

        # Greedy (determinista) -> mejor para DSL
        y = self.model.generate(
            **x,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=self.tok.eos_token_id,
        )

        decoded = self.tok.decode(y[0], skip_special_tokens=True)
        glspec = extract_glspec(decoded)
        return normalize_glspec(glspec)


# ---------- Pipeline ----------

def compile_user_text(
    gen: DslGenerator,
    user_text: str,
    lang: str,
    max_new_tokens: int = 160,
) -> dict:
    """
    Devuelve dict con:
    - glspec
    - graph_ok (bool)
    - code (si graph_ok)
    - error (si falla)
    """
    glspec = gen.to_glspec(user_text, max_new_tokens=max_new_tokens)

    try:
        G = glspec_to_graph(glspec)
    except Exception as e:
        return {
            "glspec": glspec,
            "graph_ok": False,
            "error": f"GLSPEC parse error: {type(e).__name__}: {e}",
        }

    if lang == "py":
        code = PythonTranslator().translate(G)
    elif lang == "js":
        code = JSTranslator().translate(G)
    elif lang == "c":
        code = CTranslator().translate(G)
    else:
        raise ValueError("lang must be one of: py, js, c")

    return {
        "glspec": glspec,
        "graph_ok": True,
        "code": code,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="out_minillama_lora/final", help="ruta al modelo fine-tuned (LoRA merged o adapter)")
    p.add_argument("--lang", default="py", choices=["py", "js", "c"], help="lenguaje de salida")
    p.add_argument("--max_new_tokens", type=int, default=160)
    p.add_argument("--input", default=None, help="texto de usuario (si no, lee stdin)")
    p.add_argument("--json", action="store_true", help="imprime resultado como JSON")
    args = p.parse_args()

    user_text = args.input
    if user_text is None:
        user_text = sys.stdin.read().strip()
    if not user_text:
        print("No input provided.", file=sys.stderr)
        sys.exit(1)

    gen = DslGenerator(args.model)
    result = compile_user_text(gen, user_text, args.lang, max_new_tokens=args.max_new_tokens)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== GLSPEC ===")
        print(result["glspec"])
        print("")
        if result["graph_ok"]:
            print(f"=== CODE ({args.lang}) ===")
            print(result["code"])
        else:
            print("=== ERROR ===")
            print(result["error"])


if __name__ == "__main__":
    main()
