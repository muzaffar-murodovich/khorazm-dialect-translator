import torch
import pypdfium2 as pdfium
from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32

model = LightOnOcrForConditionalGeneration.from_pretrained(
    "lightonai/LightOnOCR-2-1B", torch_dtype=dtype
).to(device)
processor = LightOnOcrProcessor.from_pretrained("lightonai/LightOnOCR-2-1B")

pdf = pdfium.PdfDocument("xorazm.pdf")

with open("ocr_natija.txt", "w", encoding="utf-8") as f:
    for i in range(len(pdf)):
        print(f"Sahifa {i+1}/{len(pdf)} ishlanmoqda...")

        # scale=2.77 o'rniga 1.5 ishlatamiz (108 DPI)
        page = pdf[i]
        image = page.render(scale=1.5).to_pil()

        conversation = [{"role": "user", "content": [{"type": "image", "image": image}]}]
        inputs = processor.apply_chat_template(
            conversation, add_generation_prompt=True,
            tokenize=True, return_dict=True, return_tensors="pt"
        )
        inputs = {k: v.to(device=device, dtype=dtype) if v.is_floating_point() else v.to(device) for k, v in inputs.items()}

        # Xotirani tozalash
        torch.cuda.empty_cache()

        output_ids = model.generate(**inputs, max_new_tokens=1024)
        generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
        text = processor.decode(generated_ids, skip_special_tokens=True)

        f.write(f"--- Sahifa {i+1} ---\n")
        f.write(text + "\n\n")
        f.flush()  # Har sahifada faylga yozadi
        print(f"  ✓ Sahifa {i+1} tayyor")

print("Natija ocr_natija.txt ga saqlandi!")