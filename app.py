import hashlib
import re
from datetime import datetime
from io import BytesIO
from typing import Any

import easyocr
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Reportar un depósito",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DEPOSIT_ACCOUNTS = [
    "MINOS S.A. - 02-4",
    "Mercantil Banco - 030024",
    "Banco General - 4589",
    "BAC Credomatic - 7512",
]

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
    "diciembre": "12",
}


# ============================================================
# ESTILOS
# ============================================================

st.html(
    """
<style>
    /* Ocultar componentes predeterminados de Streamlit */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        display: none;
    }

    div[data-testid="stToolbar"] {
        display: none;
    }

    .stDeployButton {
        display: none;
    }

    /* Aplicación */
    .stApp {
        background-color: #ffffff;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 0;
        padding-bottom: 60px;
    }

    /* Encabezado */
    .top-header {
        position: relative;
        left: 50%;
        width: 100vw;
        min-height: 80px;
        margin-left: -50vw;
        margin-bottom: 18px;
        background-color: #1d3f69;
    }

    .top-header-inner {
        width: 100%;
        max-width: 1050px;
        min-height: 80px;
        margin: 0 auto;
        padding: 0 24px;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .brand {
        color: #ffffff;
        font-family: Arial, sans-serif;
        font-size: 42px;
        line-height: 1;
        font-weight: 800;
        font-style: italic;
        letter-spacing: -3px;
    }

    .nav-center {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .nav-item {
        padding: 12px 18px;
        border-radius: 3px;
        color: #ffffff;
        background-color: #1763b4;
        font-size: 16px;
        font-weight: 700;
    }

    .nav-item.active {
        color: #15539a;
        background-color: #e9f2ff;
    }

    .nav-icons {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .nav-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        color: #ffffff;
        background-color: #1763b4;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    /* Contenedor de utilidad */
    .cashier-header {
        width: 100%;
        max-width: 550px;
        margin: 0 auto 4px auto;
    }

    .utility-row {
        margin: 5px 0 34px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .back-pill {
        padding: 4px 9px;
        border-radius: 20px;
        color: #17528c;
        background-color: #e8f5ff;
        font-size: 12px;
    }

    .balance-pill {
        min-width: 145px;
        padding: 2px 10px;
        border: 2px solid #b7d5fb;
        border-radius: 16px;
        color: #15539a;
        background-color: #ffffff;
        text-align: center;
        font-size: 12px;
    }

    .section-title {
        position: relative;
        margin-bottom: 24px;
        padding-bottom: 9px;
        color: #102f58;
        font-size: 20px;
        font-weight: 800;
    }

    .section-title::after {
        content: "";
        position: absolute;
        left: 0;
        bottom: 0;
        width: 108px;
        height: 3px;
        background-color: #153e73;
    }

    /* Etiquetas */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stFileUploader"] label {
        color: #6c625c !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    /* Espaciado de campos */
    div[data-testid="stSelectbox"],
    div[data-testid="stTextInput"],
    div[data-testid="stFileUploader"] {
        margin-bottom: 14px;
    }

    /* Select */
    div[data-baseweb="select"] > div {
        min-height: 50px;
        border: 1px solid #aeb8c5 !important;
        border-radius: 2px !important;
        background-color: #edf4fd !important;
    }

    div[data-baseweb="select"] span {
        color: #183758;
        font-weight: 600;
    }

    /* Inputs */
    .stTextInput input {
        height: 50px;
        border: none !important;
        border-radius: 2px !important;
        color: #183758 !important;
        background-color: #edf4fd !important;
        font-weight: 600;
    }

    .stTextInput input::placeholder {
        color: #a8aaad !important;
    }

    /* Upload */
    div[data-testid="stFileUploaderDropzone"] {
        min-height: 72px;
        padding: 10px 12px;
        border: 1px dashed #1c497c;
        border-radius: 2px;
        background-color: #f3f7fd;
    }

    div[data-testid="stFileUploaderDropzone"] button {
        color: #17528c !important;
        background-color: #ffffff !important;
    }

    div[data-testid="stFileUploaderFile"] {
        background-color: #edf4fd;
    }

    /* Mensajes personalizados */
    .ocr-message {
        margin: 8px 0 18px 0;
        padding: 12px 14px;
        border-left: 4px solid #1763b4;
        border-radius: 3px;
        color: #143d68;
        background-color: #edf5ff;
        font-size: 14px;
    }

    .required-message {
        margin-top: -7px;
        margin-bottom: 18px;
        color: #003b70;
        font-size: 14px;
    }

    .cancel-link {
        margin-top: 9px;
        color: #725246;
        text-align: center;
        font-size: 14px;
    }

    /* Botones */
    .stButton > button {
        width: 100%;
        min-height: 49px;
        border: none;
        border-radius: 3px;
        font-size: 16px;
        font-weight: 600;
    }

    .stButton > button[kind="primary"] {
        color: #ffffff;
        background-color: #1763b4;
    }

    .stButton > button:disabled {
        color: #c3c3c3 !important;
        background-color: #eef0f2 !important;
    }

    /* Adaptación móvil */
    @media (max-width: 760px) {
        .nav-center {
            display: none;
        }

        .brand {
            font-size: 32px;
        }

        .top-header-inner {
            padding: 0 15px;
        }

        .block-container {
            padding-left: 18px;
            padding-right: 18px;
        }

        .cashier-header {
            max-width: 100%;
        }
    }
</style>
"""
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def clean_text(value: Any) -> str:
    """Convierte un valor a texto y elimina espacios duplicados."""
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def parse_amount(value: Any) -> float | None:
    """
    Convierte montos en distintos formatos a float.

    Ejemplos:
    $62.50    -> 62.50
    1,250.50  -> 1250.50
    1.250,50  -> 1250.50
    """
    if value is None:
        return None

    normalized = clean_text(value)

    if not normalized:
        return None

    normalized = re.sub(r"[^\d,.\-]", "", normalized)

    if not normalized:
        return None

    try:
        if "," in normalized and "." in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "")
                normalized = normalized.replace(",", ".")
            else:
                normalized = normalized.replace(",", "")

        elif "," in normalized:
            decimal_section = normalized.split(",")[-1]

            if len(decimal_section) == 2:
                normalized = normalized.replace(",", ".")
            else:
                normalized = normalized.replace(",", "")

        return float(normalized)

    except (ValueError, TypeError):
        return None


def format_amount(value: float | None) -> str:
    """Formatea un monto con dos decimales."""
    if value is None:
        return ""

    return f"{value:.2f}"


def get_file_id(file_bytes: bytes) -> str:
    """Genera un identificador único para cada comprobante."""
    return hashlib.sha256(file_bytes).hexdigest()


# ============================================================
# FECHAS
# ============================================================

def normalize_date(value: str | None) -> str:
    """Convierte distintas fechas a DD/MM/YYYY."""
    if not value:
        return ""

    normalized = clean_text(value).lower()
    month_pattern = "|".join(MONTHS_ES.keys())

    textual_match = re.search(
        rf"(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})",
        normalized,
        re.IGNORECASE,
    )

    if textual_match:
        day = textual_match.group(1).zfill(2)
        month = MONTHS_ES[textual_match.group(2).lower()]
        year = textual_match.group(3)

        return f"{day}/{month}/{year}"

    numeric_match = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        normalized,
    )

    if numeric_match:
        day = numeric_match.group(1).zfill(2)
        month = numeric_match.group(2).zfill(2)
        year = numeric_match.group(3)

        if len(year) == 2:
            year = f"20{year}"

        return f"{day}/{month}/{year}"

    iso_match = re.search(
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
        normalized,
    )

    if iso_match:
        year = iso_match.group(1)
        month = iso_match.group(2).zfill(2)
        day = iso_match.group(3).zfill(2)

        return f"{day}/{month}/{year}"

    return clean_text(value)


def extract_date(text: str) -> str:
    """Extrae una fecha del texto OCR."""
    month_pattern = "|".join(MONTHS_ES.keys())

    patterns = [
        rf"\b(\d{{1,2}}\s+(?:{month_pattern})\s+\d{{4}})\b",
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return normalize_date(match.group(1))

    return ""


# ============================================================
# EXTRACCIÓN DE MONTOS
# ============================================================

def get_candidate_confidence(
    candidate_text: str,
    detected_items: list[dict[str, Any]],
) -> float:
    """Obtiene la confianza OCR del elemento que contiene el monto."""
    compact_candidate = re.sub(r"\s+", "", candidate_text)

    matching_confidences: list[float] = []

    for item in detected_items:
        item_text = re.sub(r"\s+", "", clean_text(item.get("text")))

        if compact_candidate and compact_candidate in item_text:
            matching_confidences.append(
                float(item.get("confidence", 0.0))
            )

    return (
        max(matching_confidences)
        if matching_confidences
        else 0.0
    )


def correct_possible_dollar_as_eight(
    candidate_text: str,
    confidence: float,
) -> dict[str, Any]:
    """
    Detecta el error frecuente en el que EasyOCR interpreta '$62.50'
    como '862.50'. La corrección solo se aplica a candidatos ubicados
    en el contexto de monto y con confianza OCR menor al umbral.
    """
    compact = re.sub(r"\s+", "", clean_text(candidate_text))
    regular_amount = parse_amount(compact)

    result: dict[str, Any] = {
        "amount": regular_amount,
        "corrected": False,
        "original_amount": regular_amount,
        "warning": "",
    }

    # Debe comenzar con 8 y terminar con exactamente dos decimales.
    possible_symbol_error = re.fullmatch(
        r"8\d+(?:[.,]\d{3})*[.,]\d{2}",
        compact,
    )

    if not possible_symbol_error:
        return result

    corrected_text = compact[1:]
    corrected_amount = parse_amount(corrected_text)

    # Evita correcciones fuera del rango admitido por el formulario.
    corrected_is_plausible = (
        corrected_amount is not None
        and 10 <= corrected_amount <= 20000
    )

    # Un umbral conservador reduce el riesgo de modificar un 8 real.
    if corrected_is_plausible and confidence < 0.90:
        result.update(
            {
                "amount": corrected_amount,
                "corrected": True,
                "original_amount": regular_amount,
                "warning": (
                    "EasyOCR pudo interpretar el símbolo $ como el "
                    "número 8. El monto fue corregido automáticamente, "
                    "pero debe revisarse antes de continuar."
                ),
            }
        )

    return result


def extract_amounts(
    text: str,
    detected_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Identifica monto transferido, comisión, impuesto y total usando
    palabras cercanas. Además, corrige de forma controlada el error
    '$' -> '8' de EasyOCR.
    """
    normalized = clean_text(text)
    detected_items = detected_items or []

    result: dict[str, Any] = {
        "amount": None,
        "commission": None,
        "tax": None,
        "total": None,
        "amount_corrected": False,
        "original_amount": None,
        "amount_warning": "",
        "amount_confidence": 0.0,
    }

    number_pattern = r"([\d.,]+)"

    main_amount_patterns = [
        rf"(?:¡?listo!?[\s,:-]*)?transferiste"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"monto\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"importe\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"valor\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"(?:monto|importe|valor)"
        rf"[\s:]*\$?\s*{number_pattern}",
    ]

    for pattern in main_amount_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if match:
            raw_candidate = match.group(1)
            candidate_confidence = get_candidate_confidence(
                raw_candidate,
                detected_items,
            )
            candidate_result = correct_possible_dollar_as_eight(
                raw_candidate,
                candidate_confidence,
            )

            if candidate_result["amount"] is not None:
                result["amount"] = candidate_result["amount"]
                result["amount_corrected"] = candidate_result["corrected"]
                result["original_amount"] = candidate_result["original_amount"]
                result["amount_warning"] = candidate_result["warning"]
                result["amount_confidence"] = candidate_confidence
                break

    commission_match = re.search(
        rf"comisi[oó]n[\s:()+-]*\$?\s*{number_pattern}",
        normalized,
        re.IGNORECASE,
    )

    if commission_match:
        result["commission"] = parse_amount(
            commission_match.group(1)
        )

    tax_match = re.search(
        rf"(?:ITBMS|IVA|impuesto)"
        rf"[\s:()+-]*\$?\s*{number_pattern}",
        normalized,
        re.IGNORECASE,
    )

    if tax_match:
        result["tax"] = parse_amount(
            tax_match.group(1)
        )

    total_patterns = [
        rf"total\s+a\s+pagar[\s:]*\$?\s*{number_pattern}",
        rf"total\s+pagado[\s:]*\$?\s*{number_pattern}",
        rf"total\s+debitado[\s:]*\$?\s*{number_pattern}",
        rf"total[\s:]*\$?\s*{number_pattern}",
    ]

    for pattern in total_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if match:
            candidate = parse_amount(match.group(1))

            if candidate is not None:
                result["total"] = candidate
                break

    # Respaldo: toma montos acompañados por símbolos o monedas.
    currency_amounts = re.findall(
        r"(?:\$|USD|US\$|DOP|CRC|PAB|MXN|GTQ|HNL|NIO|PEN|COP)"
        r"\s*([\d.,]+)",
        normalized,
        re.IGNORECASE,
    )

    parsed_candidates = [
        amount
        for amount in (
            parse_amount(value)
            for value in currency_amounts
        )
        if amount is not None
    ]

    if result["amount"] is None and parsed_candidates:
        excluded_values = {
            result["commission"],
            result["tax"],
            result["total"],
        }

        candidates = [
            amount
            for amount in parsed_candidates
            if amount not in excluded_values
        ]

        result["amount"] = (
            max(candidates)
            if candidates
            else max(parsed_candidates)
        )

    return result


# ============================================================
# REFERENCIA
# ============================================================

def extract_reference(text: str) -> str:
    """Extrae confirmación, referencia o número de operación."""
    patterns = [
        r"(?:confirmaci[oó]n|referencia|"
        r"n[uú]mero\s+de\s+referencia|"
        r"transacci[oó]n|"
        r"n[uú]mero\s+de\s+operaci[oó]n|"
        r"operaci[oó]n)"
        r"\s*[:#-]?\s*([A-Z0-9\-]{5,})",

        r"#\s*([A-Z0-9\-]{5,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return clean_text(match.group(1)).replace("#", "")

    return ""


# ============================================================
# PROCESAMIENTO DE IMAGEN
# ============================================================

def preprocess_image(image: Image.Image) -> Image.Image:
    """Mejora tamaño, contraste y nitidez antes del OCR."""
    processed = image.convert("RGB")

    if processed.width < 900:
        scale = 900 / processed.width

        processed = processed.resize(
            (
                int(processed.width * scale),
                int(processed.height * scale),
            )
        )

    processed = ImageEnhance.Contrast(
        processed
    ).enhance(1.15)

    processed = processed.filter(
        ImageFilter.SHARPEN
    )

    return processed


@st.cache_resource
def load_reader() -> easyocr.Reader:
    """Carga EasyOCR una sola vez."""
    return easyocr.Reader(
        ["es", "en"],
        gpu=False,
    )


@st.cache_data(show_spinner=False)
def process_receipt(file_bytes: bytes) -> dict[str, Any]:
    """Ejecuta OCR y devuelve los campos requeridos."""
    image = Image.open(
        BytesIO(file_bytes)
    ).convert("RGB")

    processed_image = preprocess_image(image)
    reader = load_reader()

    results = reader.readtext(
        np.array(processed_image),
        detail=1,
        paragraph=False,
        decoder="beamsearch",
    )

    detected_lines: list[str] = []
    detected_items: list[dict[str, Any]] = []
    confidences: list[float] = []

    for box, detected_text, confidence in results:
        detected_text = clean_text(detected_text)

        if detected_text:
            numeric_confidence = float(confidence)
            detected_lines.append(detected_text)
            confidences.append(numeric_confidence)
            detected_items.append(
                {
                    "box": box,
                    "text": detected_text,
                    "confidence": numeric_confidence,
                }
            )

    raw_text = "\n".join(detected_lines)
    amounts = extract_amounts(
        raw_text,
        detected_items=detected_items,
    )

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return {
        "raw_text": raw_text,
        "amount": format_amount(amounts["amount"]),
        "original_amount": format_amount(amounts["original_amount"]),
        "amount_corrected": bool(amounts["amount_corrected"]),
        "amount_warning": amounts["amount_warning"],
        "amount_confidence": float(amounts["amount_confidence"]),
        "reference": extract_reference(raw_text),
        "date": extract_date(raw_text),
        "confidence": average_confidence,
    }


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

DEFAULT_OCR_DATA = {
    "amount": "",
    "original_amount": "",
    "amount_corrected": False,
    "amount_warning": "",
    "amount_confidence": 0.0,
    "reference": "",
    "date": "",
    "raw_text": "",
    "confidence": 0.0,
}

if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = DEFAULT_OCR_DATA.copy()


# ============================================================
# ENCABEZADO
# ============================================================

st.html(
    """
<div class="top-header">
    <div class="top-header-inner">
        <div class="brand">betcris</div>

        <div class="nav-center">
            <div class="nav-item">Apuestas</div>
            <div class="nav-item active">Depósito</div>
            <div class="nav-item">Retiro</div>
        </div>

        <div class="nav-icons">
            <div class="nav-icon">▢</div>
            <div class="nav-icon">♙</div>
            <div class="nav-icon">♢</div>
        </div>
    </div>
</div>
"""
)


# ============================================================
# UTILIDADES Y TÍTULO
# ============================================================

st.html(
    """
<div class="cashier-header">
    <div class="utility-row">
        <span class="back-pill">← Atrás</span>
        <span class="balance-pill">Saldo&nbsp;&nbsp; USD $0.00</span>
    </div>

    <div class="section-title">REPORTAR UN DEPÓSITO</div>
</div>
"""
)


# ============================================================
# FORMULARIO
# ============================================================

left_space, form_column, right_space = st.columns(
    [1, 2.2, 1]
)

with form_column:
    account = st.selectbox(
        "Selecciona la cuenta donde depositaste",
        options=DEPOSIT_ACCOUNTS,
        key="deposit_account",
    )

    uploaded_file = st.file_uploader(
        "Sube el comprobante del depósito",
        type=["jpg", "jpeg", "png"],
        help="Tamaño máximo recomendado: 3 MB.",
        key="receipt_uploader",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        current_file_id = get_file_id(file_bytes)

        if st.session_state.current_file_id != current_file_id:
            st.session_state.current_file_id = current_file_id
            st.session_state.ocr_data = DEFAULT_OCR_DATA.copy()

            with st.spinner(
                "Leyendo la información del comprobante..."
            ):
                try:
                    st.session_state.ocr_data = process_receipt(
                        file_bytes
                    )

                except Exception as exc:
                    st.session_state.ocr_data = (
                        DEFAULT_OCR_DATA.copy()
                    )

                    st.error(
                        "No fue posible procesar el comprobante."
                    )

                    with st.expander(
                        "Ver detalle técnico"
                    ):
                        st.exception(exc)

        st.html(
            """
<div class="ocr-message">
    El comprobante fue procesado automáticamente.
    Revisa y corrige los datos antes de reportar el depósito.
</div>
"""
        )

    amount_widget_key = (
        f"amount_{st.session_state.current_file_id or 'empty'}"
    )

    reference_widget_key = (
        f"reference_{st.session_state.current_file_id or 'empty'}"
    )

    date_widget_key = (
        f"date_{st.session_state.current_file_id or 'empty'}"
    )

    amount = st.text_input(
        "Monto depositado",
        value=st.session_state.ocr_data["amount"],
        placeholder="USD 0.00",
        help=(
            "Monto mínimo: USD 10.00. "
            "Monto máximo: USD 20,000.00."
        ),
        key=amount_widget_key,
    )

    reference = st.text_input(
        "Ingresa el número de referencia",
        value=st.session_state.ocr_data["reference"],
        placeholder="Número de referencia",
        key=reference_widget_key,
    )

    deposit_date = st.text_input(
        "Selecciona la fecha del depósito",
        value=st.session_state.ocr_data["date"],
        placeholder="DD / MM / YYYY",
        key=date_widget_key,
    )

    if uploaded_file is None:
        st.html(
            """
<div class="required-message">
    Este documento es obligatorio
</div>
"""
        )

    parsed_amount = parse_amount(amount)

    amount_is_valid = (
        parsed_amount is not None
        and 10 <= parsed_amount <= 20000
    )

    reference_is_valid = bool(
        clean_text(reference)
    )

    date_is_valid = bool(
        clean_text(deposit_date)
    )

    file_is_valid = uploaded_file is not None

    required_fields_complete = (
        file_is_valid
        and amount_is_valid
        and reference_is_valid
        and date_is_valid
    )

    if parsed_amount is not None:
        if parsed_amount < 10:
            st.warning(
                "El monto mínimo permitido es USD 10.00."
            )

        elif parsed_amount > 20000:
            st.warning(
                "El monto máximo permitido es USD 20,000.00."
            )

    submit_button = st.button(
        "Reportar depósito",
        type="primary",
        disabled=not required_fields_complete,
        width="stretch",
    )

    st.html(
        """
<div class="cancel-link">
    Cancelar
</div>
"""
    )


# ============================================================
# RESULTADO DEL PROTOTIPO
# ============================================================

if submit_button and uploaded_file is not None:
    result = {
        "account": account,
        "amount": parsed_amount,
        "currency": "USD",
        "reference": clean_text(reference),
        "deposit_date": clean_text(deposit_date),
        "receipt_file": uploaded_file.name,
        "ocr_confidence": round(
            st.session_state.ocr_data["confidence"],
            4,
        ),
        "reported_at": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    st.success(
        "El depósito fue reportado correctamente."
    )

    with st.expander(
        "Ver resultado del prototipo"
    ):
        st.json(result)


# ============================================================
# COMPROBANTE Y TEXTO OCR
# ============================================================

if uploaded_file is not None:
    with st.expander(
        "Ver comprobante y texto detectado por OCR"
    ):
        preview_column, text_column = st.columns(2)

        with preview_column:
            st.image(
                uploaded_file,
                caption="Comprobante cargado",
                width="stretch",
            )

        with text_column:
            st.text_area(
                "Texto detectado",
                value=st.session_state.ocr_data["raw_text"],
                height=350,
                disabled=True,
            )