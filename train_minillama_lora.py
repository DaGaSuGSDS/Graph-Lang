import json
from datasets import Dataset
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

from peft import LoraConfig, get_peft_model

DATA_PATH = "dataset_minillama.jsonl"
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # cambia si quieres otro

def load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            inp = o.get("input") or o.get("prompt") or o.get("instruction") or o.get("text")
            out = o.get("output") or o.get("completion") or o.get("response")
            if inp is None or out is None:
                continue

            # Formato simple y estable
            text = f"### INPUT:\n{inp}\n\n### OUTPUT:\n{out}"
            rows.append({"text": text})
    return rows

def main():
    # 1) Dataset
    ds = Dataset.from_list(load_jsonl(DATA_PATH))

    # 2) Tokenizer
    tok = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    # 3) Tokenización
    def tokenize(batch):
        return tok(
            batch["text"],
            truncation=True,
            max_length=512,
            padding="max_length",
        )

    ds_tok = ds.map(tokenize, batched=True, remove_columns=["text"])

    # 4) Modelo base
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        torch_dtype="auto",
    )

    # 5) LoRA
    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora)

    # 6) Data collator (LM causal)
    collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

    # 7) Training args
    args = TrainingArguments(
        output_dir="out_minillama_lora",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=20,
        save_steps=200,
        fp16=True,          # con tu CUDA ya va OK
        bf16=False,
        report_to="none",
        remove_unused_columns=False,
    )

    # 8) Trainer
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_tok,
        data_collator=collator,
    )

    trainer.train()

    # 9) Guardar adapter LoRA + tokenizer
    trainer.save_model("out_minillama_lora/final")
    tok.save_pretrained("out_minillama_lora/final")
    print("✅ Saved to out_minillama_lora/final")

if __name__ == "__main__":
    main()
