import hashlib
import json
import re
from datetime import datetime
from io import BytesIO

import easyocr
import numpy as np
import streamlit as st
from PIL import Image


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Validador de Comprobantes",
    page_icon="🏦",
    layout="wide",
)

BANK_NAMES = [
    "Mercantil Banco",
    "Banco Mercantil",
    "Banco Nacional",
    "Banco de Costa Rica",
    "BAC Credomatic",
    "BAC",
    "Scotiabank",
    "Davivienda",
    "Banco General",
    "Banistmo",
    "Global Bank",
    "Banco Pichincha",
    "Banco Guayaquil",
    "Banco Industrial",
    "Banco Atlántida",
    "Banco Ficohsa",
    "Banco Promerica",
]


# =========================================================
# CARGA DEL MOTOR OCR
# =========================================================

@st.cache_resource
def load_ocr_reader():
    """
    Carga EasyOCR una sola vez.

    gpu=False permite usarlo sin tarjeta gráfica dedicada.
    """
    return easyocr.Reader(
        ["es", "en"],
        gpu=False,
    )


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def clean_text(value: str | None) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def clean_number(value: str) -> float | None:
    """
    Convierte diferentes formatos de monto a float.

    Ejemplos:
    1,250.50 -> 1250.50
    1.250,50 -> 1250.50
    62.50    -> 62.50
    """
    value = clean_text(value)

    if not value:
        return None

    value = re.sub(r"[^\d,.\-]", "", value)

    try:
        if "," in value and "." in value:
            # Formato 1.250,50
            if value.rfind(",") > value.rfind("."):
                value = value.replace(".", "")
                value = value.replace(",", ".")
            else:
                # Formato 1,250.50
                value = value.replace(",", "")

        elif "," in value:
            decimal_digits = len(value.split(",")[-1])

            if decimal_digits == 2:
                value = value.replace(",", ".")
            else:
                value = value.replace(",", "")

        return float(value)

    except ValueError:
        return None


def format_amount(value: float | None) -> str:
    if value is None:
        return ""

    return f"{value:.2f}"


def get_uploaded_file_id(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def find_next_line(lines: list[str], labels: set[str]) -> str | None:
    """
    Busca una etiqueta y devuelve la siguiente línea con contenido.
    """
    for index, line in enumerate(lines):
        normalized_line = clean_text(line).lower()

        if normalized_line in labels and index + 1 < len(lines):
            return clean_text(lines[index + 1])

    return None


# =========================================================
# EXTRACCIÓN DE MONTOS
# =========================================================

def extract_amounts(text: str) -> dict:
    result = {
        "amount": None,
        "commission": None,
        "tax": None,
        "total_amount": None,
    }

    normalized_text = clean_text(text)

    amount_pattern = r"([\d.,]+(?:\d{2})?)"

    # Monto principal
    main_amount_patterns = [
        rf"(?:¡?listo!?[\s,:-]*)?transferiste[\s:]*\$?\s*{amount_pattern}",
        rf"monto\s+transferido[\s:]*\$?\s*{amount_pattern}",
        rf"importe\s+transferido[\s:]*\$?\s*{amount_pattern}",
        rf"valor\s+transferido[\s:]*\$?\s*{amount_pattern}",
        rf"monto[\s:]*\$?\s*{amount_pattern}",
        rf"importe[\s:]*\$?\s*{amount_pattern}",
    ]

    for pattern in main_amount_patterns:
        match = re.search(
            pattern,
            normalized_text,
            re.IGNORECASE,
        )

        if match:
            result["amount"] = clean_number(match.group(1))

            if result["amount"] is not None:
                break

    # Comisión
    commission_match = re.search(
        rf"comisi[oó]n[\s:]*\$?\s*{amount_pattern}",
        normalized_text,
        re.IGNORECASE,
    )

    if commission_match:
        result["commission"] = clean_number(
            commission_match.group(1)
        )

    # Impuesto
    tax_match = re.search(
        rf"(?:ITBMS|IVA|impuesto)[\s:]*\$?\s*{amount_pattern}",
        normalized_text,
        re.IGNORECASE,
    )

    if tax_match:
        result["tax"] = clean_number(
            tax_match.group(1)
        )

    # Total
    total_patterns = [
        rf"total\s+a\s+pagar[\s:]*\$?\s*{amount_pattern}",
        rf"total\s+pagado[\s:]*\$?\s*{amount_pattern}",
        rf"total[\s:]*\$?\s*{amount_pattern}",
    ]

    for pattern in total_patterns:
        total_match = re.search(
            pattern,
            normalized_text,
            re.IGNORECASE,
        )

        if total_match:
            result["total_amount"] = clean_number(
                total_match.group(1)
            )

            if result["total_amount"] is not None:
                break

    # Respaldo: buscar todos los valores acompañados por moneda
    money_matches = re.findall(
        r"(?:\$|USD|DOP|CRC|PAB|MXN|GTQ|HNL|NIO|PEN|COP)"
        r"\s*([\d.,]+)",
        normalized_text,
        re.IGNORECASE,
    )

    numeric_amounts = [
        clean_number(value)
        for value in money_matches
    ]

    numeric_amounts = [
        value
        for value in numeric_amounts
        if value is not None
    ]

    # Si no se identificó el monto por contexto,
    # excluir comisión, impuesto y total.
    if result["amount"] is None and numeric_amounts:
        excluded_values = {
            result["commission"],
            result["tax"],
            result["total_amount"],
        }

        candidates = [
            value
            for value in numeric_amounts
            if value not in excluded_values
        ]

        if candidates:
            result["amount"] = max(candidates)
        else:
            result["amount"] = max(numeric_amounts)

    return result


# =========================================================
# EXTRACCIÓN DE CAMPOS
# =========================================================

def detect_bank(text: str) -> str | None:
    lower_text = text.lower()

    for bank in BANK_NAMES:
        if bank.lower() in lower_text:
            if "mercantil" in bank.lower():
                return "Mercantil Banco"

            return bank

    return None


def extract_account(text: str) -> str | None:
    patterns = [
        r"(?:CORRIENTE|AHORRO|CUENTA|ACCOUNT)"
        r"\s*[:#-]?\s*([0-9*Xx\- ]{6,})",

        r"(?:cuenta\s+destino|cuenta\s+beneficiaria)"
        r"\s*[:#-]?\s*([0-9*Xx\- ]{6,})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            account = clean_text(match.group(1))
            account = re.sub(r"\s+", "", account)

            return account

    return None


def extract_date(text: str) -> str | None:
    months = (
        r"enero|febrero|marzo|abril|mayo|junio|julio|"
        r"agosto|septiembre|octubre|noviembre|diciembre"
    )

    patterns = [
        rf"\b(\d{{1,2}}\s+(?:{months})\s+\d{{4}})\b",
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return clean_text(match.group(1))

    return None


def extract_time(text: str) -> str | None:
    match = re.search(
        r"\b((?:[01]?\d|2[0-3]):[0-5]\d"
        r"(?:\s*[AaPp]\.?[Mm]\.?)?)\b",
        text,
    )

    if match:
        return clean_text(match.group(1))

    return None


def extract_confirmation(text: str) -> str | None:
    patterns = [
        r"(?:Confirmación|Confirmacion|Referencia|Reference|"
        r"Comprobante|Transacción|Transaccion)"
        r"\s*[:#-]?\s*([A-Z0-9\-]{5,})",

        r"#\s*([A-Z0-9\-]{5,})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return clean_text(match.group(1)).replace("#", "")

    return None


def extract_receipt_data(text: str) -> dict:
    lines = [
        clean_text(line)
        for line in text.splitlines()
        if clean_text(line)
    ]

    amounts = extract_amounts(text)

    description = find_next_line(
        lines,
        {"descripción", "descripcion", "concepto", "detalle"},
    )

    sender = find_next_line(
        lines,
        {"desde", "ordenante", "remitente", "origen"},
    )

    recipient = find_next_line(
        lines,
        {"hacia", "destinatario", "beneficiario", "destino"},
    )

    return {
        "bank": detect_bank(text),
        "account": extract_account(text),
        "amount": amounts["amount"],
        "commission": amounts["commission"],
        "tax": amounts["tax"],
        "total_amount": amounts["total_amount"],
        "date": extract_date(text),
        "time": extract_time(text),
        "confirmation": extract_confirmation(text),
        "description": description,
        "sender": sender,
        "recipient": recipient,
    }


# =========================================================
# OCR
# =========================================================

@st.cache_data(show_spinner=False)
def process_image(file_bytes: bytes) -> dict:
    """
    Ejecuta OCR y devuelve el texto, confianza y campos extraídos.
    """
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    image_array = np.array(image)

    reader = load_ocr_reader()

    results = reader.readtext(
        image_array,
        detail=1,
        paragraph=False,
    )

    detected_lines = []
    confidence_values = []

    for _, detected_text, confidence in results:
        detected_text = clean_text(detected_text)

        if detected_text:
            detected_lines.append(detected_text)
            confidence_values.append(float(confidence))

    raw_text = "\n".join(detected_lines)

    average_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0
    )

    return {
        "raw_text": raw_text,
        "average_confidence": average_confidence,
        "extracted_data": extract_receipt_data(raw_text),
    }


# =========================================================
# INTERFAZ
# =========================================================

st.title("🏦 Prototipo de lectura de comprobantes")

st.markdown(
    """
Sube un comprobante bancario para extraer automáticamente sus datos.
Los campos obtenidos por OCR pueden revisarse y corregirse antes de
guardar el resultado.
"""
)

uploaded_file = st.file_uploader(
    "Subir comprobante",
    type=["jpg", "jpeg", "png"],
    help="Formatos permitidos: JPG, JPEG y PNG.",
)

if uploaded_file is None:
    st.info("Sube un comprobante para comenzar.")
    st.stop()


file_bytes = uploaded_file.getvalue()
file_id = get_uploaded_file_id(file_bytes)

# Cuando cambia el documento, se limpia el estado anterior.
if st.session_state.get("current_file_id") != file_id:
    st.session_state.current_file_id = file_id
    st.session_state.corrected_data = None


with st.spinner("Procesando comprobante con OCR..."):
    ocr_result = process_image(file_bytes)


image = Image.open(BytesIO(file_bytes))
extracted = ocr_result["extracted_data"]
confidence = ocr_result["average_confidence"]

left_column, right_column = st.columns(
    [0.9, 1.1],
    gap="large",
)

with left_column:
    st.subheader("Comprobante")

    st.image(
        image,
        width="stretch",
    )

    confidence_percentage = confidence * 100

    st.metric(
        "Confianza promedio del OCR",
        f"{confidence_percentage:.1f}%",
    )

    if confidence_percentage >= 85:
        st.success("Lectura OCR con confianza alta.")
    elif confidence_percentage >= 65:
        st.warning("Conviene revisar algunos campos.")
    else:
        st.error("La imagen requiere revisión manual.")


with right_column:
    st.subheader("Datos extraídos y editables")

    st.caption(
        "Corrige cualquier campo que el OCR no haya leído correctamente."
    )

    with st.form("correction_form"):
        bank = st.text_input(
            "Banco",
            value=extracted["bank"] or "",
        )

        account = st.text_input(
            "Cuenta",
            value=extracted["account"] or "",
        )

        amount = st.text_input(
            "Monto transferido",
            value=format_amount(extracted["amount"]),
        )

        commission = st.text_input(
            "Comisión",
            value=format_amount(extracted["commission"]),
        )

        tax = st.text_input(
            "Impuesto",
            value=format_amount(extracted["tax"]),
        )

        total_amount = st.text_input(
            "Total pagado",
            value=format_amount(extracted["total_amount"]),
        )

        date = st.text_input(
            "Fecha",
            value=extracted["date"] or "",
        )

        time = st.text_input(
            "Hora",
            value=extracted["time"] or "",
        )

        confirmation = st.text_input(
            "Confirmación o referencia",
            value=extracted["confirmation"] or "",
        )

        description = st.text_input(
            "Descripción",
            value=extracted["description"] or "",
        )

        sender = st.text_input(
            "Remitente",
            value=extracted["sender"] or "",
        )

        recipient = st.text_input(
            "Destinatario",
            value=extracted["recipient"] or "",
        )

        submitted = st.form_submit_button(
            "Guardar correcciones",
            type="primary",
            width="stretch",
        )


if submitted:
    corrected_data = {
        "bank": clean_text(bank),
        "account": clean_text(account),
        "amount": clean_number(amount),
        "commission": clean_number(commission),
        "tax": clean_number(tax),
        "total_amount": clean_number(total_amount),
        "date": clean_text(date),
        "time": clean_text(time),
        "confirmation": clean_text(confirmation),
        "description": clean_text(description),
        "sender": clean_text(sender),
        "recipient": clean_text(recipient),
        "source_file": uploaded_file.name,
        "ocr_confidence": round(confidence, 4),
        "reviewed_at": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    st.session_state.corrected_data = corrected_data
    st.success("Las correcciones fueron guardadas.")


# =========================================================
# RESULTADO GUARDADO Y DESCARGA
# =========================================================

if st.session_state.corrected_data:
    st.divider()
    st.subheader("Resultado revisado")

    corrected_data = st.session_state.corrected_data

    validation_messages = []

    if not corrected_data["bank"]:
        validation_messages.append(
            "No se indicó el banco."
        )

    if not corrected_data["amount"]:
        validation_messages.append(
            "No se indicó el monto transferido."
        )

    if not corrected_data["confirmation"]:
        validation_messages.append(
            "No se indicó la confirmación o referencia."
        )

    if (
        corrected_data["amount"] is not None
        and corrected_data["commission"] is not None
        and corrected_data["tax"] is not None
        and corrected_data["total_amount"] is not None
    ):
        calculated_total = (
            corrected_data["amount"]
            + corrected_data["commission"]
            + corrected_data["tax"]
        )

        if abs(
            calculated_total
            - corrected_data["total_amount"]
        ) > 0.02:
            validation_messages.append(
                "El monto, la comisión y el impuesto no coinciden "
                "con el total pagado."
            )

    if validation_messages:
        for message in validation_messages:
            st.warning(message)
    else:
        st.success(
            "Los campos principales están completos."
        )

    st.json(corrected_data)

    json_content = json.dumps(
        corrected_data,
        indent=4,
        ensure_ascii=False,
    )

    st.download_button(
        label="Descargar resultado en JSON",
        data=json_content,
        file_name="resultado_comprobante.json",
        mime="application/json",
        width="stretch",
    )


# =========================================================
# TEXTO OCR
# =========================================================

with st.expander("Ver texto detectado por OCR"):
    st.text_area(
        "Texto completo",
        value=ocr_result["raw_text"],
        height=300,
        disabled=True,
    )