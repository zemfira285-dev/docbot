import os
from docxtpl import DocxTemplate
from utils import format_amount, number_to_words

TEMPLATES_DIR = "templates"
OUTPUT_DIR = "generated_docs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def _render_doc(template_name: str, context: dict, output_prefix: str) -> str:
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    doc = DocxTemplate(template_path)
    
    doc.render(context)
    
    filename = f"{output_prefix}_{context.get('client_iin', 'doc')}.docx"
    output_path = os.path.join(OUTPUT_DIR, filename)
    doc.save(output_path)
    return output_path


def create_receipt(data: dict) -> str:
    amount = data["amount"]
    context = {
        "client_name": data["client_name"],
        "client_iin": data["client_iin"],
        "product": data["product"],
        "amount": format_amount(amount),
        "amount_words": number_to_words(amount),
        "date": data.get("date") or "сегодня",
        "installment": data.get("installment", False),
        "pay_from": data.get("pay_from", ""),
        "pay_to": data.get("pay_to", ""),
    }
    return _render_doc("receipt_template.docx", context, "receipt")


def create_guarantee_letter(data: dict) -> str:
    amount = data["amount"]
    context = {
        "client_name": data["client_name"],
        "client_iin": data["client_iin"],
        "product": data["product"],
        "amount": format_amount(amount),
        "amount_words": number_to_words(amount),
        "date": data.get("date") or "сегодня",
    }
    return _render_doc("guarantee_template.docx", context, "guarantee")


def create_contract(data: dict) -> str:
    amount = data["amount"]
    context = {
        "client_name": data["client_name"],
        "client_iin": data["client_iin"],
        "product": data["product"],
        "amount": format_amount(amount),
        "amount_words": number_to_words(amount),
        "date": data.get("date") or "сегодня",
        "installment": data.get("installment", False),
        "pay_from": data.get("pay_from", ""),
        "pay_to": data.get("pay_to", ""),
    }
    return _render_doc("contract_template.docx", context, "contract")