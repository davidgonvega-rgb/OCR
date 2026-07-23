import hashlib
import re
from difflib import SequenceMatcher
from datetime import datetime
from io import BytesIO
from typing import Any

import easyocr
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


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
    "BLUEANT, S.A. C.V.-1166",
    "Banco de Fomento Agropecuario-41-9",
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

    /* Ventana emergente de confirmación */
    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 10px;
        padding: 8px;
    }

    div[data-testid="stDialog"] h2 {
        color: #102f58;
        font-weight: 800;
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
    """
    Extrae fechas de comprobantes digitales y recibos de ATM.

    Formatos admitidos, entre otros:
    - 21/07/2026
    - 22/07/26
    - 21 julio 2026
    - 22 julio (se utiliza el año actual)
    - Hoy (21 julio 2026)
    """
    normalized = clean_text(text).lower()
    month_pattern = "|".join(MONTHS_ES.keys())

    # Prioriza fechas completas con mes escrito.
    textual_with_year = re.search(
        rf"\b(\d{{1,2}})\s+(?:de\s+)?({month_pattern})"
        rf"(?:\s+de)?\s+(\d{{4}})\b",
        normalized,
        re.IGNORECASE,
    )

    if textual_with_year:
        day = textual_with_year.group(1).zfill(2)
        month = MONTHS_ES[textual_with_year.group(2).lower()]
        year = textual_with_year.group(3)
        return f"{day}/{month}/{year}"

    # Fechas numéricas de recibos ATM y comprobantes móviles.
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

    # Algunos bancos muestran únicamente "22 julio".
    textual_without_year = re.search(
        rf"\b(\d{{1,2}})\s+(?:de\s+)?({month_pattern})\b",
        normalized,
        re.IGNORECASE,
    )

    if textual_without_year:
        day = textual_without_year.group(1).zfill(2)
        month = MONTHS_ES[textual_without_year.group(2).lower()]
        year = str(datetime.now().year)
        return f"{day}/{month}/{year}"

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
    Extrae el monto de comprobantes de Panamá y El Salvador.

    Reconoce etiquetas como:
    - Transferiste
    - Monto / Monto debitado
    - USD
    - Importe / Valor

    También conserva la corrección controlada del error "$" -> "8".
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

    number_pattern = r"([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2}|[0-9]+[.,][0-9]{2})"

    # Ordenados desde las etiquetas más específicas hasta las genéricas.
    main_amount_patterns = [
        rf"monto\s+debitado[\s:]*\$?\s*{number_pattern}",
        rf"monto\s+(?:transferido|depositado|enviado|acreditado)"
        rf"[\s:]*\$?\s*{number_pattern}",
        rf"(?:¡?listo!?[\s,:-]*)?transferiste"
        rf"[\s:]*\$?\s*{number_pattern}",
        rf"importe\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",
        rf"valor\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",
        rf"(?:monto|importe|valor)[\s:]*\$?\s*{number_pattern}",
        # Recibos de ATM de El Salvador: "USD : 10.00".
        rf"\bUSD\b[\s:.-]*\$?\s*{number_pattern}",
    ]

    for pattern in main_amount_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if not match:
            continue

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
        rf"(?:comisi[oó]n|costo\s+de\s+la\s+transacci[oó]n)"
        rf"[\s:()+-]*\$?\s*{number_pattern}",
        normalized,
        re.IGNORECASE,
    )

    if commission_match:
        result["commission"] = parse_amount(commission_match.group(1))

    tax_match = re.search(
        rf"(?:ITBMS|IVA|impuesto)[\s:()+-]*\$?\s*{number_pattern}",
        normalized,
        re.IGNORECASE,
    )

    if tax_match:
        result["tax"] = parse_amount(tax_match.group(1))

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

    # Respaldo: valores acompañados por símbolo o moneda.
    currency_amounts = re.findall(
        rf"(?:\$|USD|US\$|DOP|CRC|PAB|MXN|GTQ|HNL|NIO|PEN|COP)"
        rf"\s*[:.-]?\s*{number_pattern}",
        normalized,
        re.IGNORECASE,
    )

    parsed_candidates = [
        amount
        for amount in (parse_amount(value) for value in currency_amounts)
        if amount is not None and amount > 0
    ]

    if result["amount"] is None and parsed_candidates:
        excluded_values = {
            result["commission"],
            result["tax"],
            result["total"],
        }
        candidates = [
            amount for amount in parsed_candidates
            if amount not in excluded_values
        ]
        result["amount"] = candidates[0] if candidates else parsed_candidates[0]

    return result


# ============================================================
# REFERENCIA
# ============================================================

def normalize_search_text(value: Any) -> str:
    """Normaliza texto para comparar etiquetas aunque OCR altere acentos."""
    import unicodedata

    normalized = clean_text(value).lower()
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(character) != "Mn"
    )
    normalized = normalized.replace("º", "o").replace("°", "o")
    normalized = re.sub(r"[^a-z0-9#]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def clean_reference_candidate(value: Any) -> str:
    """
    Limpia una referencia preservando ceros iniciales y letras.

    Ejemplos válidos:
    - 008666
    - 205496894
    - BSALVSS20260721133529842861C767580
    """
    candidate = clean_text(value).upper()
    candidate = candidate.replace("#", "")
    candidate = re.sub(r"\s+", "", candidate)
    candidate = re.sub(r"[^A-Z0-9-]", "", candidate)
    return candidate.strip("-")


def build_positioned_items(
    detected_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrega coordenadas resumidas a los fragmentos detectados."""
    positioned: list[dict[str, Any]] = []

    for item in detected_items:
        box = item.get("box") or []
        if not box:
            continue

        x_values = [float(point[0]) for point in box]
        y_values = [float(point[1]) for point in box]
        positioned.append(
            {
                **item,
                "x_min": min(x_values),
                "x_max": max(x_values),
                "y_min": min(y_values),
                "y_max": max(y_values),
                "x_center": sum(x_values) / len(x_values),
                "y_center": sum(y_values) / len(y_values),
            }
        )

    return positioned


def group_items_into_lines(
    items: list[dict[str, Any]],
    vertical_tolerance: float = 26.0,
) -> list[list[dict[str, Any]]]:
    """Agrupa bloques OCR que pertenecen visualmente a una misma línea."""
    lines: list[list[dict[str, Any]]] = []

    for item in sorted(items, key=lambda current: (current["y_center"], current["x_min"])):
        selected_line: list[dict[str, Any]] | None = None

        for line in lines:
            average_y = sum(current["y_center"] for current in line) / len(line)
            if abs(item["y_center"] - average_y) <= vertical_tolerance:
                selected_line = line
                break

        if selected_line is None:
            lines.append([item])
        else:
            selected_line.append(item)

    for line in lines:
        line.sort(key=lambda current: current["x_min"])

    return lines


REFERENCE_LABEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "authorization",
        re.compile(r"\b(?:autorizacion|authorization|auth)\b", re.IGNORECASE),
    ),
    (
        "receipt_number",
        re.compile(
            r"\b(?:n(?:o|0)?\s*(?:de\s*)?comprobante|"
            r"numero\s+de\s+comprobante|comprobante)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reference",
        re.compile(
            r"\b(?:referencia|numero\s+de\s+referencia|ref)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "confirmation",
        re.compile(r"\b(?:confirmacion|confirmation)\b", re.IGNORECASE),
    ),
    (
        "operation",
        re.compile(
            r"\b(?:numero\s+de\s+operacion|operacion|"
            r"numero\s+de\s+transaccion|transaccion)\b",
            re.IGNORECASE,
        ),
    ),
]


def detect_reference_label(value: Any) -> tuple[str, re.Match[str]] | None:
    """Identifica el tipo de etiqueta que precede a la referencia."""
    normalized = normalize_search_text(value)

    for label_type, pattern in REFERENCE_LABEL_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return label_type, match

    return None


def is_valid_reference_candidate(value: Any, label_type: str) -> bool:
    """Valida candidatos sin imponer una longitud única para todos los bancos."""
    candidate = clean_reference_candidate(value)

    if not candidate or not re.search(r"\d", candidate):
        return False

    if label_type == "authorization":
        return 8 <= len(candidate) <= 50

    return 5 <= len(candidate) <= 25


def extract_reference(text: str) -> str:
    """Respaldo textual para referencias de Panamá y El Salvador."""
    normalized_lines = [clean_text(line) for line in str(text).splitlines() if clean_text(line)]

    patterns: list[tuple[str, re.Pattern[str]]] = [
        (
            "authorization",
            re.compile(
                r"(?:autorizaci[oó]n|authorization|auth)\s*[:#-]?\s*"
                r"([A-Z0-9-]{8,50})",
                re.IGNORECASE,
            ),
        ),
        (
            "receipt_number",
            re.compile(
                r"(?:N\s*[°ºo0]?\s*(?:de\s*)?comprobante|"
                r"n[uú]mero\s+de\s+comprobante|comprobante)"
                r"\s*[:#-]?\s*([A-Z0-9-]{5,25})",
                re.IGNORECASE,
            ),
        ),
        (
            "reference",
            re.compile(
                r"(?:referencia|n[uú]mero\s+de\s+referencia|ref)"
                r"\s*[:#-]?\s*([A-Z0-9-]{5,25})",
                re.IGNORECASE,
            ),
        ),
        (
            "confirmation",
            re.compile(
                r"(?:confirmaci[oó]n|confirmation)"
                r"\s*[:#-]?\s*([A-Z0-9-]{5,25})",
                re.IGNORECASE,
            ),
        ),
    ]

    joined_text = "\n".join(normalized_lines)
    for label_type, pattern in patterns:
        match = pattern.search(joined_text)
        if match:
            candidate = clean_reference_candidate(match.group(1))
            if is_valid_reference_candidate(candidate, label_type):
                return candidate

    return ""


def extract_reference_from_items(
    detected_items: list[dict[str, Any]],
    raw_text: str,
) -> str:
    """
    Extrae la referencia por etiqueta y posición.

    Soporta los formatos observados en El Salvador:
    - REFERENCIA: 008666
    - N° comprobante 205496894
    - Autorización BSALVSS...
    - Confirmación #1815312714
    """
    positioned_items = build_positioned_items(detected_items)
    lines = group_items_into_lines(positioned_items)

    # Se procesan por prioridad: autorización, número de comprobante,
    # referencia, confirmación y operación.
    for desired_type, _ in REFERENCE_LABEL_PATTERNS:
        for line_index, line in enumerate(lines):
            line_text = " ".join(item["text"] for item in line)
            label_info = detect_reference_label(line_text)

            if not label_info or label_info[0] != desired_type:
                continue

            label_items = [
                item for item in line
                if detect_reference_label(item["text"])
            ]
            label_x_max = max(
                (item["x_max"] for item in label_items),
                default=min(item["x_min"] for item in line),
            )

            # 1) Valor a la derecha de la etiqueta en la misma línea.
            same_line_candidates: list[str] = []
            for item in line:
                if detect_reference_label(item["text"]):
                    continue
                if item["x_min"] < label_x_max - 12:
                    continue

                candidate = clean_reference_candidate(item["text"])
                if candidate and re.search(r"\d", candidate):
                    same_line_candidates.append(candidate)

            combined_same_line = "".join(same_line_candidates)
            if is_valid_reference_candidate(combined_same_line, desired_type):
                return combined_same_line

            # 2) Valor inmediatamente debajo de la etiqueta.
            label_bottom = max(item["y_max"] for item in line)

            for next_line in lines[line_index + 1 : line_index + 3]:
                next_top = min(item["y_min"] for item in next_line)
                vertical_gap = next_top - label_bottom

                if vertical_gap < -10 or vertical_gap > 110:
                    continue

                parts: list[str] = []
                for item in next_line:
                    # Detenerse si la siguiente línea ya es otra etiqueta.
                    if detect_reference_label(item["text"]):
                        continue

                    candidate = clean_reference_candidate(item["text"])
                    if candidate and re.search(r"\d", candidate):
                        parts.append(candidate)

                combined_below = "".join(parts)
                if is_valid_reference_candidate(combined_below, desired_type):
                    return combined_below

    reconstructed_text = "\n".join(
        " ".join(item["text"] for item in line)
        for line in lines
    )
    return extract_reference(reconstructed_text) or extract_reference(raw_text)



def looks_like_label(value: Any, targets: tuple[str, ...], threshold: float = 0.66) -> bool:
    """Detecta etiquetas aunque EasyOCR cambie una o dos letras."""
    normalized = normalize_search_text(value)
    if not normalized:
        return False

    compact = normalized.replace(" ", "")
    for target in targets:
        normalized_target = normalize_search_text(target)
        compact_target = normalized_target.replace(" ", "")

        if normalized_target in normalized or compact_target in compact:
            return True

        for token in normalized.split():
            if SequenceMatcher(None, token, normalized_target).ratio() >= threshold:
                return True

        if SequenceMatcher(None, compact, compact_target).ratio() >= threshold:
            return True

    return False


def extract_atm_amount_from_items(
    detected_items: list[dict[str, Any]],
) -> float | None:
    """
    Respaldo específico para recibos ATM de El Salvador.

    Reconoce variaciones OCR como USD, USO, U5D y toma el decimal
    ubicado en la misma línea o inmediatamente después.
    """
    positioned = build_positioned_items(detected_items)
    lines = group_items_into_lines(positioned, vertical_tolerance=30.0)
    amount_pattern = re.compile(r"(?<!\d)(\d{1,6}[.,]\d{2})(?!\d)")

    for line_index, line in enumerate(lines):
        line_text = " ".join(item["text"] for item in line)
        normalized = normalize_search_text(line_text).upper()

        currency_label_found = (
            re.search(r"\bU[S5][D0O]\b", normalized) is not None
            or looks_like_label(line_text, ("USD",), threshold=0.62)
        )

        if not currency_label_found:
            continue

        # Primero intenta extraer el decimal de la misma línea completa.
        same_line_match = amount_pattern.search(line_text)
        if same_line_match:
            candidate = parse_amount(same_line_match.group(1))
            if candidate is not None and 0 < candidate <= 20000:
                return candidate

        # Luego revisa cada bloque de la línea.
        for item in line:
            match = amount_pattern.search(item["text"])
            if match:
                candidate = parse_amount(match.group(1))
                if candidate is not None and 0 < candidate <= 20000:
                    return candidate

        # Finalmente revisa hasta dos líneas inmediatamente inferiores.
        label_bottom = max(item["y_max"] for item in line)
        for next_line in lines[line_index + 1 : line_index + 3]:
            next_top = min(item["y_min"] for item in next_line)
            if next_top - label_bottom > 100:
                break

            next_text = " ".join(item["text"] for item in next_line)
            match = amount_pattern.search(next_text)
            if match:
                candidate = parse_amount(match.group(1))
                if candidate is not None and 0 < candidate <= 20000:
                    return candidate

    return None


def extract_atm_reference_from_items(
    detected_items: list[dict[str, Any]],
) -> str:
    """
    Respaldo específico para recibos ATM donde REFERENCIA y el valor
    pueden quedar dentro del mismo bloque OCR. Conserva ceros iniciales.
    """
    positioned = build_positioned_items(detected_items)
    lines = group_items_into_lines(positioned, vertical_tolerance=30.0)
    digits_pattern = re.compile(r"(?<!\d)(\d{5,25})(?!\d)")

    for line_index, line in enumerate(lines):
        line_text = " ".join(item["text"] for item in line)
        is_reference_line = looks_like_label(
            line_text,
            ("referencia", "referencia atm", "ref"),
            threshold=0.62,
        )

        if not is_reference_line:
            continue

        # Importante: analiza la línea completa, incluso cuando etiqueta y
        # referencia fueron reconocidas como un único bloque.
        matches = digits_pattern.findall(line_text)
        if matches:
            # La referencia suele ser el último grupo numérico de la línea.
            return matches[-1]

        # Revisa los bloques individuales por si EasyOCR separó el valor.
        for item in reversed(line):
            matches = digits_pattern.findall(item["text"])
            if matches:
                return matches[-1]

        # Respaldo: valor inmediatamente debajo de la etiqueta.
        label_bottom = max(item["y_max"] for item in line)
        for next_line in lines[line_index + 1 : line_index + 3]:
            next_top = min(item["y_min"] for item in next_line)
            if next_top - label_bottom > 100:
                break

            next_text = " ".join(item["text"] for item in next_line)
            matches = digits_pattern.findall(next_text)
            if matches:
                return matches[0]

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




def normalize_ocr_label(value: Any) -> str:
    """Normaliza etiquetas OCR sin modificar los valores numéricos."""
    normalized = normalize_search_text(value).upper()
    replacements = {
        "REFERENC1A": "REFERENCIA",
        "REFERENClA": "REFERENCIA",
        "REFERENCLA": "REFERENCIA",
        "USO": "USD",
        "US0": "USD",
        "U5D": "USD",
    }
    for wrong, correct in replacements.items():
        normalized = normalized.replace(wrong, correct)
    return normalized


def extract_reference_el_salvador_text(raw_text: str) -> str:
    """
    Extrae referencias salvadoreñas únicamente después de etiquetas válidas.
    DEP_ATM se excluye expresamente para evitar falsos positivos.
    """
    lines = [clean_text(line) for line in str(raw_text).splitlines() if clean_text(line)]

    patterns = [
        re.compile(r"\bREFERENCIA\s*[:#\-]?\s*([A-Z0-9\-]{5,40})\b", re.I),
        re.compile(r"\bN\s*[°ºO0]?\.?\s*(?:DE\s+)?COMPROBANTE\s*[:#\-]?\s*([A-Z0-9\-]{5,40})\b", re.I),
        re.compile(r"\bNUMERO\s+(?:DE\s+)?COMPROBANTE\s*[:#\-]?\s*([A-Z0-9\-]{5,40})\b", re.I),
        re.compile(r"\bAUTORIZACION\s*[:#\-]?\s*([A-Z0-9\-]{5,60})\b", re.I),
        re.compile(r"\bCONFIRMACION\s*[:#\-]?\s*([A-Z0-9\-]{5,40})\b", re.I),
    ]

    normalized_lines = [normalize_ocr_label(line) for line in lines]
    for line in normalized_lines:
        if "DEP_ATM" in line or "DEP ATM" in line:
            continue
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                candidate = clean_reference_candidate(match.group(1))
                if candidate:
                    return candidate

    # Cuando etiqueta y valor quedan en líneas separadas, revisar solo la línea inmediata siguiente.
    valid_labels = ("REFERENCIA", "NO COMPROBANTE", "N COMPROBANTE", "NUMERO DE COMPROBANTE", "AUTORIZACION", "CONFIRMACION")
    for i, line in enumerate(normalized_lines[:-1]):
        if "DEP_ATM" in line or "DEP ATM" in line:
            continue
        if not any(label in line for label in valid_labels):
            continue
        next_line = normalized_lines[i + 1]
        if "DEP_ATM" in next_line or "DEP ATM" in next_line:
            continue
        match = re.search(r"(?<![A-Z0-9])([A-Z0-9\-]{5,60})(?![A-Z0-9])", next_line)
        if match:
            candidate = clean_reference_candidate(match.group(1))
            if candidate:
                return candidate

    return ""


def extract_amount_el_salvador_text(raw_text: str) -> float | None:
    """Extrae montos salvadoreños tolerando USD/USO/US0/U5D y líneas separadas."""
    normalized = normalize_ocr_label(raw_text)
    amount = r"([0-9]{1,6}(?:[.,][0-9]{3})*[.,][0-9]{2}|[0-9]+[.,][0-9]{2})"
    patterns = [
        rf"\bUSD\b\s*[:\-]?\s*\$?\s*{amount}",
        rf"\bMONTO\s+DEBITADO\b\s*[:\-]?\s*\$?\s*{amount}",
        rf"\bMONTO\b\s*[:\-]?\s*\$?\s*{amount}",
        rf"\bTRANSFERISTE\b\s*[:\-]?\s*\$?\s*{amount}",
        rf"\bTOTAL\b\s*[:\-]?\s*\$?\s*{amount}",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.I)
        if match:
            value = parse_amount(match.group(1))
            if value is not None and 0 < value <= 20000:
                return value

    # Respaldo secuencial: localizar USD y revisar los siguientes tokens OCR.
    tokens = normalized.split()
    for i, token in enumerate(tokens):
        if token.rstrip(":.-") != "USD":
            continue
        for candidate_token in tokens[i + 1:i + 5]:
            match = re.search(amount, candidate_token)
            if match:
                value = parse_amount(match.group(1))
                if value is not None and 0 < value <= 20000:
                    return value
    return None


def extract_atm_reference_strict(detected_items: list[dict[str, Any]]) -> str:
    """
    Extrae el número de la línea REFERENCIA y nunca utiliza el valor de DEP_ATM.
    Conserva ceros iniciales.
    """
    positioned = build_positioned_items(detected_items)
    lines = group_items_into_lines(positioned, vertical_tolerance=34.0)
    digit_group = re.compile(r"(?<!\d)(\d{5,30})(?!\d)")

    for line_index, line in enumerate(lines):
        line_text = " ".join(item["text"] for item in line)
        normalized = normalize_ocr_label(line_text)
        if "DEP_ATM" in normalized or "DEP ATM" in normalized:
            continue
        if not looks_like_label(line_text, ("referencia",), threshold=0.60):
            continue

        # Tomar exclusivamente grupos numéricos de la línea de REFERENCIA.
        matches = digit_group.findall(line_text)
        if matches:
            return matches[-1]

        # Si el valor está separado, revisar solo la siguiente línea cercana.
        label_bottom = max(item["y_max"] for item in line)
        for next_line in lines[line_index + 1:line_index + 2]:
            next_top = min(item["y_min"] for item in next_line)
            if next_top - label_bottom > 85:
                continue
            next_text = " ".join(item["text"] for item in next_line)
            next_normalized = normalize_ocr_label(next_text)
            if "DEP_ATM" in next_normalized or "DEP ATM" in next_normalized:
                continue
            matches = digit_group.findall(next_text)
            if matches:
                return matches[0]
    return ""



def normalize_amount_label(value: Any) -> str:
    """Normaliza etiquetas de monto sin alterar los valores numéricos."""
    normalized = normalize_search_text(value)

    replacements = {
        "m0nto": "monto",
        "mont0": "monto",
        "debitad0": "debitado",
        "debltado": "debitado",
        "debltad0": "debitado",
    }

    for wrong, correct in replacements.items():
        normalized = normalized.replace(wrong, correct)

    return normalized


def extract_money_from_block(value: Any) -> float | None:
    """Extrae un monto decimal de un bloque OCR."""
    text = clean_text(value)

    match = re.search(
        r"\$?\s*(\d{1,6}(?:[.,]\d{3})*[.,]\d{2}|\d+[.,]\d{2})",
        text,
    )

    if not match:
        return None

    amount = parse_amount(match.group(1))

    if amount is None or not (0 < amount <= 20000):
        return None

    return amount


def extract_labeled_amount_from_items(
    detected_items: list[dict[str, Any]],
) -> float | None:
    """
    Extrae montos cuando la etiqueta y el valor aparecen en bloques
    separados, por ejemplo:

        Monto debitado                         $10.00

    También reconoce Monto, Total y Transferiste. Se utilizan las
    coordenadas OCR para seleccionar el valor alineado a la derecha
    o inmediatamente debajo de la etiqueta.
    """
    positioned = build_positioned_items(detected_items)

    if not positioned:
        return None

    label_priorities = (
        "monto debitado",
        "monto transferido",
        "monto depositado",
        "transferiste",
        "monto",
        "total",
    )

    for expected_label in label_priorities:
        labels = [
            item
            for item in positioned
            if expected_label in normalize_amount_label(item["text"])
        ]

        for label in labels:
            # Caso 1: etiqueta y monto fueron reconocidos en el mismo bloque.
            amount_in_label = extract_money_from_block(label["text"])

            if amount_in_label is not None:
                return amount_in_label

            candidates: list[dict[str, Any]] = []

            for item in positioned:
                if item is label:
                    continue

                amount = extract_money_from_block(item["text"])

                if amount is None:
                    continue

                horizontal_gap = item["x_min"] - label["x_max"]
                vertical_distance = abs(
                    item["y_center"] - label["y_center"]
                )

                # Valor alineado a la derecha en la misma fila.
                same_row = vertical_distance <= 38
                right_of_label = horizontal_gap >= -12

                if same_row and right_of_label:
                    candidates.append(
                        {
                            "amount": amount,
                            "score": (
                                vertical_distance
                                + max(horizontal_gap, 0) * 0.025
                                - float(item.get("confidence", 0.0)) * 8
                            ),
                        }
                    )
                    continue

                # Respaldo: monto inmediatamente debajo de la etiqueta.
                vertical_gap = item["y_min"] - label["y_max"]
                horizontally_related = (
                    item["x_center"] >= label["x_min"] - 30
                )

                if (
                    0 <= vertical_gap <= 85
                    and horizontally_related
                ):
                    candidates.append(
                        {
                            "amount": amount,
                            "score": (
                                50
                                + vertical_gap
                                + abs(item["x_center"] - label["x_center"]) * 0.02
                                - float(item.get("confidence", 0.0)) * 8
                            ),
                        }
                    )

            if candidates:
                best_candidate = min(
                    candidates,
                    key=lambda candidate: candidate["score"],
                )
                return best_candidate["amount"]

    return None


def extract_atm_amount_strict(detected_items: list[dict[str, Any]]) -> float | None:
    """Busca el decimal en la línea USD o en la línea inmediatamente siguiente."""
    positioned = build_positioned_items(detected_items)
    lines = group_items_into_lines(positioned, vertical_tolerance=34.0)
    amount_pattern = re.compile(r"(?<!\d)(\d{1,6}[.,]\d{2})(?!\d)")

    for line_index, line in enumerate(lines):
        line_text = " ".join(item["text"] for item in line)
        normalized = normalize_ocr_label(line_text)
        if not (re.search(r"\bUSD\b", normalized) or looks_like_label(line_text, ("USD",), threshold=0.58)):
            continue

        match = amount_pattern.search(line_text)
        if match:
            value = parse_amount(match.group(1))
            if value is not None and 0 < value <= 20000:
                return value

        label_bottom = max(item["y_max"] for item in line)
        for next_line in lines[line_index + 1:line_index + 2]:
            next_top = min(item["y_min"] for item in next_line)
            if next_top - label_bottom > 90:
                continue
            next_text = " ".join(item["text"] for item in next_line)
            match = amount_pattern.search(next_text)
            if match:
                value = parse_amount(match.group(1))
                if value is not None and 0 < value <= 20000:
                    return value
    return None

@st.cache_resource
def load_reader() -> easyocr.Reader:
    """Carga EasyOCR una sola vez."""
    return easyocr.Reader(
        ["es", "en"],
        gpu=False,
    )


@st.cache_data(show_spinner=False)
def process_receipt(file_bytes: bytes) -> dict[str, Any]:
    """Ejecuta OCR y devuelve monto, referencia y fecha."""
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    processed_image = preprocess_image(image)
    reader = load_reader()

    results = reader.readtext(
        np.array(processed_image),
        detail=1,
        paragraph=False,
        decoder="beamsearch",
    )

    # Ordenar por posición para conservar el orden visual del comprobante.
    sorted_results = sorted(
        results,
        key=lambda result: (
            min(float(point[1]) for point in result[0]),
            min(float(point[0]) for point in result[0]),
        ),
    )

    detected_lines: list[str] = []
    detected_items: list[dict[str, Any]] = []
    confidences: list[float] = []

    for box, detected_text, confidence in sorted_results:
        detected_text = clean_text(detected_text)
        if not detected_text:
            continue
        numeric_confidence = float(confidence)
        detected_lines.append(detected_text)
        confidences.append(numeric_confidence)
        detected_items.append({
            "box": box,
            "text": detected_text,
            "confidence": numeric_confidence,
        })

    raw_text = "\n".join(detected_lines)
    amounts = extract_amounts(raw_text, detected_items=detected_items)

    # Prioridad de monto:
    # 1) etiqueta y valor alineados por coordenadas (Monto debitado / Monto);
    # 2) recibos ATM asociados a USD;
    # 3) respaldo mediante expresiones regulares sobre el texto completo.
    strict_amount = extract_labeled_amount_from_items(detected_items)
    if strict_amount is None:
        strict_amount = extract_atm_amount_strict(detected_items)
    if strict_amount is None:
        strict_amount = extract_amount_el_salvador_text(raw_text)
    if strict_amount is not None:
        amounts["amount"] = strict_amount
        amounts["original_amount"] = strict_amount
        amounts["amount_corrected"] = False
        amounts["amount_warning"] = ""

    # Prioridad de referencia:
    # 1) línea REFERENCIA estricta; 2) etiquetas salvadoreñas en texto;
    # 3) extractor general para comprobantes digitales.
    final_reference = extract_atm_reference_strict(detected_items)
    if not final_reference:
        final_reference = extract_reference_el_salvador_text(raw_text)
    if not final_reference:
        final_reference = extract_reference_from_items(detected_items, raw_text)

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences else 0.0
    )

    return {
        "raw_text": raw_text,
        "amount": format_amount(amounts["amount"]),
        "original_amount": format_amount(amounts["original_amount"]),
        "amount_corrected": bool(amounts["amount_corrected"]),
        "amount_warning": amounts["amount_warning"],
        "amount_confidence": float(amounts["amount_confidence"]),
        "reference": final_reference,
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

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if "show_success_dialog" not in st.session_state:
    st.session_state.show_success_dialog = False

if "last_report_result" not in st.session_state:
    st.session_state.last_report_result = None



def show_deposit_success_dialog() -> None:
    """Muestra la confirmación y mantiene el formulario limpio."""
    st.success(
        "El depósito fue reportado correctamente. "
        "Los fondos serán acreditados a tu cuenta tan pronto "
        "la transacción sea confirmada."
    )

    if st.button("Aceptar", type="primary", width="stretch"):
        st.session_state.show_success_dialog = False
        st.rerun()


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
        key=f"deposit_account_{st.session_state.form_version}",
    )

    uploaded_file = st.file_uploader(
        "Sube el comprobante del depósito",
        type=["jpg", "jpeg", "png"],
        help="Tamaño máximo recomendado: 3 MB.",
        key=f"receipt_uploader_{st.session_state.form_version}",
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
        Revisa y corrige los datos antes de reportar el depósito.
</div>
"""
        )


        with st.expander(
            "Ver comprobante"
        ):
            st.image(
                uploaded_file,
                caption="Comprobante cargado",
                width="stretch",
            )

    amount_widget_key = (
        f"amount_{st.session_state.form_version}_"
        f"{st.session_state.current_file_id or 'empty'}"
    )

    reference_widget_key = (
        f"reference_{st.session_state.form_version}_"
        f"{st.session_state.current_file_id or 'empty'}"
    )

    date_widget_key = (
        f"date_{st.session_state.form_version}_"
        f"{st.session_state.current_file_id or 'empty'}"
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
        "Número de referencia",
        value=st.session_state.ocr_data["reference"],
        placeholder="Número de referencia",
        key=reference_widget_key,
    )

    deposit_date = st.text_input(
        "Fecha del depósito",
        value=st.session_state.ocr_data["date"],
        placeholder="DD / MM / YYYY",
        key=date_widget_key,
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

    # Conserva el último resultado únicamente para fines internos
    # del prototipo y reinicia por completo el formulario.
    st.session_state.last_report_result = result
    st.session_state.current_file_id = None
    st.session_state.ocr_data = DEFAULT_OCR_DATA.copy()
    st.session_state.form_version += 1
    st.session_state.show_success_dialog = True

    # El rerun carga un formulario nuevo y vacío. La ventana emergente
    # se muestra inmediatamente después de que la interfaz se reinicia.
    st.rerun()


if st.session_state.show_success_dialog:
    show_deposit_success_dialog()