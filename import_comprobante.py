import json
import re
from datetime import datetime, timedelta

MONTHS_ES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12"
}

ALLOWED_BANKS = [
    "Mercantil Banco",
    "Banco Nacional",
    "Banco de Costa Rica",
    "BAC",
    "Scotiabank",
    "Davivienda"
]

OFFICIAL_ACCOUNTS = [
    "01202030024"
]

USED_CONFIRMATIONS = [
    "9999999999",
    "8888888888"
]


def load_document_ai_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("document", {}).get("text", "")


def normalize_date(text):
    pattern = r"(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})"
    match = re.search(pattern, text.lower())

    if not match:
        return None

    day = match.group(1).zfill(2)
    month = MONTHS_ES.get(match.group(2))
    year = match.group(3)

    return f"{year}-{month}-{day}"


def extract_payment_fields(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    result = {
        "bank_name": None,
        "account": None,
        "amount": None,
        "total_amount": None,
        "date": None,
        "time": None,
        "confirmation": None,
        "description": None,
        "sender": None,
        "raw_text": text
    }

    # Hora
    time_match = re.search(r"\b\d{1,2}:\d{2}\b", text)
    if time_match:
        result["time"] = time_match.group(0)

    # Montos
    amounts = re.findall(r"\$\s?([\d,]+(?:\.\d{2})?)", text)
    clean_amounts = [float(amount.replace(",", "")) for amount in amounts]

    if clean_amounts:
        result["amount"] = clean_amounts[0]

    total_match = re.search(r"Total a pagar:\s*\$\s?([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if total_match:
        result["total_amount"] = float(total_match.group(1).replace(",", ""))

    # Banco
    for bank in ALLOWED_BANKS:
        if bank.lower() in text.lower():
            result["bank_name"] = bank
            break

    # Cuenta
    account_match = re.search(r"(CORRIENTE|AHORRO|Cuenta)[:\s]+([0-9\-]+)", text, re.IGNORECASE)
    if account_match:
        result["account"] = account_match.group(2).replace("-", "")

    # Fecha
    result["date"] = normalize_date(text)

    # Confirmación
    confirmation_match = re.search(r"#\s?(\d+)", text)
    if confirmation_match:
        result["confirmation"] = confirmation_match.group(1)

    # Descripción
    description_index = None
    for i, line in enumerate(lines):
        if line.lower() == "descripción":
            description_index = i
            break

    if description_index is not None and description_index + 1 < len(lines):
        result["description"] = lines[description_index + 1]

    # Remitente / Desde
    for i, line in enumerate(lines):
        if line.lower() == "desde" and i + 1 < len(lines):
            result["sender"] = lines[i + 1]
            break

    return result


def validate_payment(payment, expected_amount=None):
    validations = {
        "is_valid": True,
        "manual_review_required": False,
        "errors": [],
        "warnings": []
    }

    if not payment["bank_name"]:
        validations["errors"].append("No se pudo identificar el banco.")
        validations["manual_review_required"] = True

    if not payment["account"]:
        validations["errors"].append("No se pudo identificar la cuenta bancaria.")
        validations["manual_review_required"] = True
    elif payment["account"] not in OFFICIAL_ACCOUNTS:
        validations["errors"].append("La cuenta bancaria no coincide con las cuentas oficiales.")
        validations["manual_review_required"] = True

    if not payment["amount"]:
        validations["errors"].append("No se pudo identificar el monto transferido.")
        validations["manual_review_required"] = True

    if expected_amount is not None and payment["amount"] is not None:
        if float(payment["amount"]) != float(expected_amount):
            validations["errors"].append(
                f"El monto detectado ({payment['amount']}) no coincide con el monto esperado ({expected_amount})."
            )
            validations["manual_review_required"] = True

    if not payment["date"]:
        validations["warnings"].append("No se pudo identificar la fecha.")
        validations["manual_review_required"] = True
    else:
        payment_date = datetime.strptime(payment["date"], "%Y-%m-%d").date()
        today = datetime.today().date()

        if payment_date > today:
            validations["errors"].append("La fecha del comprobante está en el futuro.")
            validations["manual_review_required"] = True

        if payment_date < today - timedelta(days=2):
            validations["warnings"].append("El comprobante tiene más de 48 horas.")
            validations["manual_review_required"] = True

    if not payment["confirmation"]:
        validations["errors"].append("No se pudo identificar el número de confirmación.")
        validations["manual_review_required"] = True
    elif payment["confirmation"] in USED_CONFIRMATIONS:
        validations["errors"].append("El número de confirmación ya fue utilizado anteriormente.")
        validations["manual_review_required"] = True

    if payment["total_amount"] and payment["amount"]:
        if payment["total_amount"] != payment["amount"]:
            validations["warnings"].append(
                "El comprobante contiene monto transferido y total con comisión. Usar el monto transferido."
            )

    if validations["errors"]:
        validations["is_valid"] = False

    return validations


if __name__ == "__main__":
    file_path = "response.json"

    text = load_document_ai_json(file_path)

    payment = extract_payment_fields(text)

    validations = validate_payment(
        payment,
        expected_amount=62.50
    )

    final_result = {
        "extracted_payment_data": payment,
        "validations": validations
    }

    print(json.dumps(final_result, indent=4, ensure_ascii=False))