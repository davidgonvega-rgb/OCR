import hashlib
import re
from datetime import datetime
from io import BytesIO
from textwrap import dedent
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

st.markdown(
    dedent(
        """
        <style>
            #MainMenu {
                visibility: hidden;
            }

            footer {
                visibility: hidden;
            }

            header[data-testid="stHeader"] {
                display: none;
            }

            .stApp {
                background-color: #ffffff;
            }

            .block-container {
                max-width: 1050px;
                padding-top: 0;
                padding-bottom: 60px;
            }

            .top-header {
                position: relative;
                left: 50%;
                width: 100vw;
                margin-left: -50vw;
                background-color: #1d3f69;
                min-height: 80px;
                margin-bottom: 10px;
            }

            .top-header-inner {
                max-width: 1050px;
                min-height: 80px;
                margin: 0 auto;
                padding: 0 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-sizing: border-box;
            }

            .brand {
                color: #ffffff;
                font-size: 42px;
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
                background-color: #1763b4;
                color: #ffffff;
                padding: 12px 18px;
                border-radius: 3px;
                font-size: 16px;
                font-weight: 700;
            }

            .nav-item.active {
                background-color: #e9f2ff;
                color: #15539a;
            }

            .nav-icons {
                display: flex;
                gap: 10px;
            }

            .nav-icon {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #1763b4;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }

            .cashier-shell {
                width: 100%;
                max-width: 550px;
                margin: 0 auto;
            }

            .utility-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-top: 8px;
                margin-bottom: 34px;
            }

            .back-pill {
                display: inline-block;
                background-color: #e8f5ff;
                color: #17528c;
                border-radius: 20px;
                padding: 4px 9px;
                font-size: 12px;
            }

            .balance-pill {
                min-width: 145px;
                text-align: center;
                color: #15539a;
                background-color: #ffffff;
                border: 2px solid #b7d5fb;
                border-radius: 16px;
                padding: 2px 10px;
                font-size: 12px;
            }

            .section-title {
                position: relative;
                color: #102f58;
                font-size: 20px;
                font-weight: 800;
                margin-bottom: 24px;
                padding-bottom: 9px;
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

            div[data-testid="stSelectbox"],
            div[data-testid="stTextInput"],
            div[data-testid="stFileUploader"] {
                margin-bottom: 14px;
            }

            div[data-testid="stSelectbox"] label,
            div[data-testid="stTextInput"] label,
            div[data-testid="stFileUploader"] label {
                color: #6c625c !important;
                font-size: 16px !important;
                font-weight: 700 !important;
            }

            div[data-baseweb="select"] > div {
                min-height: 50px;
                background-color: #edf4fd !important;
                border: 1px solid #aeb8c5 !important;
                border-radius: 2px !important;
            }

            .stTextInput input {
                height: 50px;
                color: #183758 !important;
                background-color: #edf4fd !important;
                border: none !important;
                border-radius: 2px !important;
                font-weight: 600;
            }

            .stTextInput input::placeholder {
                color: #a8aaad !important;
            }

            div[data-testid="stFileUploaderDropzone"] {
                min-height: 72px;
                padding: 10px 12px;
                background-color: #f3f7fd;
                border: 1px dashed #1c497c;
                border-radius: 2px;
            }

            div[data-testid="stFileUploaderDropzone"] button {
                color: #17528c !important;
                background-color: transparent !important;
            }

            .ocr-message {
                margin: 10px 0 18px 0;
                padding: 12px 14px;
                color: #143d68;
                background-color: #edf5ff;
                border-left: 4px solid #1763b4;
                border-radius: 3px;
                font-size: 14px;
            }

            .required-message {
                color: #003b70;
                font-size: 14px;
                margin-top: -7px;
                margin-bottom: 18px;
            }

            .cancel-link {
                text-align: center;
                color: #725246;
                font-size: 14px;
                margin-top: 9px;
            }

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

                .cashier-shell {
                    max-width: 100%;
                }
            }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def parse_amount(value: Any) -> float | None:
    """
    Convierte formatos como:
    62.50
    $62.50
    1,250.50
    1.250,50
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
            last_part = normalized.split(",")[-1]

            if len(last_part) == 2:
                normalized = normalized.replace(",", ".")
            else:
                normalized = normalized.replace(",", "")

        return float(normalized)

    except (ValueError, TypeError):
        return None


def format_amount(value: float | None) -> str:
    if value is None:
        return ""

    return f"{value:.2f}"


def get_file_id(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


# ============================================================
# FECHAS
# ============================================================

def normalize_date(value: str | None) -> str:
    if not value:
        return ""

    normalized = clean_text(value).lower()
    month_pattern = "|".join(MONTHS_ES.keys())

    text_date = re.search(
        rf"(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})",
        normalized,
        re.IGNORECASE,
    )

    if text_date:
        day = text_date.group(1).zfill(2)
        month = MONTHS_ES[text_date.group(2).lower()]
        year = text_date.group(3)

        return f"{day}/{month}/{year}"

    numeric_date = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        normalized,
    )

    if numeric_date:
        day = numeric_date.group(1).zfill(2)
        month = numeric_date.group(2).zfill(2)
        year = numeric_date.group(3)

        if len(year) == 2:
            year = f"20{year}"

        return f"{day}/{month}/{year}"

    iso_date = re.search(
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
        normalized,
    )

    if iso_date:
        year = iso_date.group(1)
        month = iso_date.group(2).zfill(2)
        day = iso_date.group(3).zfill(2)

        return f"{day}/{month}/{year}"

    return clean_text(value)


def extract_date(text: str) -> str:
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

def extract_amounts(text: str) -> dict[str, float | None]:
    normalized = clean_text(text)

    result = {
        "amount": None,
        "commission": None,
        "tax": None,
        "total": None,
    }

    number_pattern = r"([\d.,]+)"

    main_patterns = [
        rf"(?:¡?listo!?[\s,:-]*)?transferiste"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"monto\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"importe\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number_pattern}",

        rf"(?:monto|importe|valor)"
        rf"[\s:]*\$?\s*{number_pattern}",
    ]

    for pattern in main_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if match:
            candidate = parse_amount(match.group(1))

            if candidate is not None:
                result["amount"] = candidate
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
        rf"total[\s:]*\$?\s*{number_pattern}",
    ]

    for pattern in total_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)

        if match:
            candidate = parse_amount(match.group(1))

            if candidate is not None:
                result["total"] = candidate
                break

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

        if candidates:
            result["amount"] = max(candidates)
        else:
            result["amount"] = max(parsed_candidates)

    return result


# ============================================================
# REFERENCIA
# ============================================================

def extract_reference(text: str) -> str:
    patterns = [
        r"(?:confirmaci[oó]n|referencia|n[uú]mero\s+de\s+referencia|"
        r"transacci[oó]n|n[uú]mero\s+de\s+operaci[oó]n|operaci[oó]n)"
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
    return easyocr.Reader(
        ["es", "en"],
        gpu=False,
    )


@st.cache_data(show_spinner=False)
def process_receipt(file_bytes: bytes) -> dict[str, Any]:
    image = Image.open(
        BytesIO(file_bytes)
    ).convert("RGB")

    processed_image = preprocess_image(image)
    reader = load_reader()

    results = reader.readtext(
        np.array(processed_image),
        detail=1,
        paragraph=False,
    )

    detected_lines: list[str] = []
    confidences: list[float] = []

    for _, detected_text, confidence in results:
        detected_text = clean_text(detected_text)

        if detected_text:
            detected_lines.append(detected_text)
            confidences.append(float(confidence))

    raw_text = "\n".join(detected_lines)
    amounts = extract_amounts(raw_text)

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return {
        "raw_text": raw_text,
        "amount": format_amount(amounts["amount"]),
        "reference": extract_reference(raw_text),
        "date": extract_date(raw_text),
        "confidence": average_confidence,
    }


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

if "ocr_amount" not in st.session_state:
    st.session_state.ocr_amount = ""

if "ocr_reference" not in st.session_state:
    st.session_state.ocr_reference = ""

if "ocr_date" not in st.session_state:
    st.session_state.ocr_date = ""

if "ocr_raw_text" not in st.session_state:
    st.session_state.ocr_raw_text = ""

if "ocr_confidence" not in st.session_state:
    st.session_state.ocr_confidence = 0.0


# ============================================================
# ENCABEZADO
# ============================================================

header_html = dedent(
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
).strip()

st.markdown(
    header_html,
    unsafe_allow_html=True,
)


# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

st.markdown(
    dedent(
        """
        <div class="cashier-shell">
            <div class="utility-row">
                <span class="back-pill">← Atrás</span>
                <span class="balance-pill">Saldo&nbsp;&nbsp; USD $0.00</span>
            </div>

            <div class="section-title">REPORTAR UN DEPÓSITO</div>
        </div>
        """
    ).strip(),
    unsafe_allow_html=True,
)


# Mantener los componentes de Streamlit centrados y con ancho similar.
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

            with st.spinner(
                "Leyendo la información del comprobante..."
            ):
                try:
                    ocr_result = process_receipt(file_bytes)

                    st.session_state.ocr_amount = (
                        ocr_result["amount"]
                    )

                    st.session_state.ocr_reference = (
                        ocr_result["reference"]
                    )

                    st.session_state.ocr_date = (
                        ocr_result["date"]
                    )

                    st.session_state.ocr_raw_text = (
                        ocr_result["raw_text"]
                    )

                    st.session_state.ocr_confidence = (
                        ocr_result["confidence"]
                    )

                except Exception as exc:
                    st.session_state.ocr_amount = ""
                    st.session_state.ocr_reference = ""
                    st.session_state.ocr_date = ""
                    st.session_state.ocr_raw_text = ""
                    st.session_state.ocr_confidence = 0.0

                    st.error(
                        "No fue posible procesar el comprobante."
                    )

                    with st.expander(
                        "Ver detalle técnico"
                    ):
                        st.exception(exc)

        confidence_percentage = (
            st.session_state.ocr_confidence * 100
        )

        st.markdown(
            dedent(
                f"""
                <div class="ocr-message">
                    El comprobante fue procesado automáticamente.
                    Revisa y corrige los datos antes de reportar
                    el depósito.
                    <br>
                    <strong>Confianza promedio del OCR:</strong>
                    {confidence_percentage:.1f}%
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    amount = st.text_input(
        "Monto depositado",
        value=st.session_state.ocr_amount,
        placeholder="USD 0.00",
        help=(
            "Monto mínimo: USD 10.00. "
            "Monto máximo: USD 20,000.00."
        ),
        key=f"amount_{st.session_state.current_file_id}",
    )

    reference = st.text_input(
        "Ingresa el número de referencia",
        value=st.session_state.ocr_reference,
        placeholder="Número de referencia",
        key=f"reference_{st.session_state.current_file_id}",
    )

    deposit_date = st.text_input(
        "Selecciona la fecha del depósito",
        value=st.session_state.ocr_date,
        placeholder="DD / MM / YYYY",
        key=f"date_{st.session_state.current_file_id}",
    )

    if uploaded_file is None:
        st.markdown(
            (
                '<div class="required-message">'
                "Este documento es obligatorio"
                "</div>"
            ),
            unsafe_allow_html=True,
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
        use_container_width=True,
    )

    st.markdown(
        '<div class="cancel-link">Cancelar</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# RESULTADO
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
            st.session_state.ocr_confidence,
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


if uploaded_file is not None:
    with st.expander(
        "Ver comprobante y texto detectado por OCR"
    ):
        preview_column, text_column = st.columns(2)

        with preview_column:
            st.image(
                uploaded_file,
                caption="Comprobante cargado",
                use_container_width=True,
            )

        with text_column:
            st.text_area(
                "Texto detectado",
                value=st.session_state.ocr_raw_text,
                height=350,
                disabled=True,
            )