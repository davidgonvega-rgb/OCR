import hashlib
import re
from datetime import datetime
from io import BytesIO
from typing import Any

import easyocr
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter


# =========================================================
# CONFIGURACIÓN
# =========================================================

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


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>
        /* Ocultar elementos predeterminados de Streamlit */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            display: none;
        }

        .stDeployButton {
            display: none;
        }

        /* Fondo principal */
        .stApp {
            background: #ffffff;
        }

        .block-container {
            max-width: 1050px;
            padding-top: 0;
            padding-bottom: 60px;
        }

        /* Barra superior */
        .top-header {
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            width: 100vw;
            min-height: 81px;
            background: #1b3b65;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 10px;
        }

        .top-header-inner {
            width: min(100%, 1050px);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 25px;
            box-sizing: border-box;
        }

        .brand {
            color: #ffffff;
            font-size: 43px;
            font-weight: 800;
            font-style: italic;
            letter-spacing: -3px;
            line-height: 1;
        }

        .nav-center {
            display: flex;
            align-items: center;
            gap: 11px;
        }

        .nav-item {
            background: #1763b4;
            color: #ffffff;
            padding: 12px 19px;
            border-radius: 3px;
            font-weight: 700;
            font-size: 16px;
        }

        .nav-item.active {
            background: #e9f2ff;
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
            background: #1763b4;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 19px;
        }

        /* Contenido */
        .cashier-shell {
            width: 100%;
            max-width: 550px;
            margin: 0 auto;
        }

        .utility-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 5px 0 34px 0;
        }

        .back-pill {
            display: inline-block;
            background: #e8f5ff;
            color: #17528c;
            border-radius: 20px;
            padding: 3px 8px;
            font-size: 12px;
        }

        .balance-pill {
            min-width: 145px;
            text-align: center;
            color: #15539a;
            background: white;
            border: 2px solid #b7d5fb;
            border-radius: 16px;
            padding: 1px 10px;
            font-size: 12px;
        }

        .section-title {
            color: #102f58;
            font-size: 20px;
            font-weight: 800;
            margin: 0 0 23px 0;
            padding-bottom: 8px;
            position: relative;
        }

        .section-title::after {
            content: "";
            width: 108px;
            height: 3px;
            background: #153e73;
            position: absolute;
            left: 0;
            bottom: 0;
        }

        .field-label {
            color: #6c625c;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .amount-limits {
            float: right;
            font-size: 10px;
            color: #6b6b6b;
            font-weight: 400;
            margin-top: 4px;
        }

        /* Widgets Streamlit */
        div[data-testid="stSelectbox"] {
            margin-bottom: 17px;
        }

        div[data-testid="stTextInput"] {
            margin-bottom: 17px;
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label {
            color: #6c625c !important;
            font-weight: 700 !important;
            font-size: 16px !important;
        }

        div[data-baseweb="select"] > div {
            min-height: 50px;
            background: #edf4fd !important;
            border: 1px solid #aeb8c5 !important;
            border-radius: 2px !important;
        }

        div[data-baseweb="select"] span {
            color: #8b8b8b;
            font-weight: 700;
        }

        .stTextInput input {
            height: 50px;
            background: #edf4fd !important;
            border: none !important;
            border-radius: 2px !important;
            color: #183758 !important;
            font-weight: 600;
        }

        .stTextInput input::placeholder {
            color: #a8aaad !important;
        }

        .amount-field input {
            text-align: center !important;
            letter-spacing: 4px;
            font-size: 17px !important;
            color: #8f8f8f !important;
        }

        /* Cargador */
        div[data-testid="stFileUploaderDropzone"] {
            background: #f3f7fd;
            border: 1px dashed #1c497c;
            border-radius: 2px;
            min-height: 72px;
            padding: 9px 12px;
        }

        div[data-testid="stFileUploaderDropzone"] button {
            background: transparent !important;
            color: #17528c !important;
            border: none !important;
        }

        div[data-testid="stFileUploaderDropzone"] small {
            color: #676767 !important;
        }

        div[data-testid="stFileUploaderFile"] {
            background: #edf4fd;
        }

        /* Botón */
        .stButton > button,
        .stFormSubmitButton > button {
            width: 100%;
            min-height: 49px;
            border-radius: 3px;
            border: none;
            font-size: 16px;
            font-weight: 600;
        }

        .stFormSubmitButton > button[kind="primary"] {
            background: #1763b4;
            color: white;
        }

        .stFormSubmitButton > button:disabled {
            background: #eef0f2 !important;
            color: #c3c3c3 !important;
        }

        .cancel-link {
            text-align: center;
            color: #725246;
            font-size: 14px;
            margin-top: 9px;
        }

        .required-message {
            color: #003b70;
            font-size: 14px;
            margin-top: -8px;
            margin-bottom: 20px;
        }

        .ocr-message {
            border-left: 4px solid #1763b4;
            background: #edf5ff;
            color: #143d68;
            padding: 12px 14px;
            border-radius: 3px;
            margin: 12px 0 18px 0;
            font-size: 14px;
        }

        /* Ocultar etiquetas vacías */
        .hidden-label {
            display: none;
        }

        @media (max-width: 760px) {
            .brand {
                font-size: 32px;
            }

            .nav-center {
                display: none;
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
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FUNCIONES OCR
# =========================================================

@st.cache_resource
def load_reader() -> easyocr.Reader:
    return easyocr.Reader(
        ["es", "en"],
        gpu=False,
    )


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def parse_amount(value: str | None) -> float | None:
    if not value:
        return None

    value = re.sub(r"[^\d,.\-]", "", value)

    if not value:
        return None

    try:
        if "," in value and "." in value:
            if value.rfind(",") > value.rfind("."):
                value = value.replace(".", "")
                value = value.replace(",", ".")
            else:
                value = value.replace(",", "")

        elif "," in value:
            if len(value.split(",")[-1]) == 2:
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


def normalize_date(value: str | None) -> str:
    if not value:
        return ""

    value = clean_text(value).lower()

    month_pattern = "|".join(MONTHS_ES.keys())

    text_date = re.search(
        rf"(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})",
        value,
        re.IGNORECASE,
    )

    if text_date:
        day = text_date.group(1).zfill(2)
        month = MONTHS_ES[text_date.group(2).lower()]
        year = text_date.group(3)

        return f"{day}/{month}/{year}"

    numeric_date = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        value,
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
        value,
    )

    if iso_date:
        return (
            f"{iso_date.group(3).zfill(2)}/"
            f"{iso_date.group(2).zfill(2)}/"
            f"{iso_date.group(1)}"
        )

    return clean_text(value)


def extract_amounts(text: str) -> dict[str, float | None]:
    normalized = clean_text(text)

    result = {
        "amount": None,
        "commission": None,
        "tax": None,
        "total": None,
    }

    number = r"([\d.,]+)"

    main_patterns = [
        rf"(?:¡?listo!?[\s,:-]*)?transferiste"
        rf"[\s:]*\$?\s*{number}",

        rf"monto\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number}",

        rf"importe\s+(?:transferido|depositado|enviado)"
        rf"[\s:]*\$?\s*{number}",

        rf"(?:monto|importe|valor)"
        rf"[\s:]*\$?\s*{number}",
    ]

    for pattern in main_patterns:
        match = re.search(
            pattern,
            normalized,
            re.IGNORECASE,
        )

        if match:
            result["amount"] = parse_amount(match.group(1))

            if result["amount"] is not None:
                break

    commission_match = re.search(
        rf"comisi[oó]n[\s:()+-]*\$?\s*{number}",
        normalized,
        re.IGNORECASE,
    )

    if commission_match:
        result["commission"] = parse_amount(
            commission_match.group(1)
        )

    tax_match = re.search(
        rf"(?:ITBMS|IVA|impuesto)"
        rf"[\s:()+-]*\$?\s*{number}",
        normalized,
        re.IGNORECASE,
    )

    if tax_match:
        result["tax"] = parse_amount(
            tax_match.group(1)
        )

    total_match = re.search(
        rf"total(?:\s+a\s+pagar|\s+pagado)?"
        rf"[\s:]*\$?\s*{number}",
        normalized,
        re.IGNORECASE,
    )

    if total_match:
        result["total"] = parse_amount(
            total_match.group(1)
        )

    all_currency_amounts = re.findall(
        r"(?:\$|USD|US\$|DOP|CRC|PAB|MXN|GTQ|HNL|NIO|PEN|COP)"
        r"\s*([\d.,]+)",
        normalized,
        re.IGNORECASE,
    )

    parsed_amounts = [
        amount
        for amount in (
            parse_amount(value)
            for value in all_currency_amounts
        )
        if amount is not None
    ]

    if result["amount"] is None and parsed_amounts:
        excluded = {
            result["commission"],
            result["tax"],
            result["total"],
        }

        candidates = [
            amount
            for amount in parsed_amounts
            if amount not in excluded
        ]

        if candidates:
            result["amount"] = max(candidates)
        else:
            result["amount"] = max(parsed_amounts)

    return result


def extract_reference(text: str) -> str:
    patterns = [
        r"(?:confirmaci[oó]n|referencia|n[uú]mero\s+de\s+referencia|"
        r"transacci[oó]n|operaci[oó]n)"
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

    return ""


def extract_date(text: str) -> str:
    month_pattern = "|".join(MONTHS_ES.keys())

    patterns = [
        rf"\b(\d{{1,2}}\s+(?:{month_pattern})\s+\d{{4}})\b",
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
            return normalize_date(match.group(1))

    return ""


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


@st.cache_data(show_spinner=False)
def process_receipt(file_bytes: bytes) -> dict[str, Any]:
    image = Image.open(
        BytesIO(file_bytes)
    ).convert("RGB")

    processed = preprocess_image(image)
    reader = load_reader()

    results = reader.readtext(
        np.array(processed),
        detail=1,
        paragraph=False,
    )

    lines: list[str] = []
    confidences: list[float] = []

    for _, detected_text, confidence in results:
        detected_text = clean_text(detected_text)

        if detected_text:
            lines.append(detected_text)
            confidences.append(float(confidence))

    raw_text = "\n".join(lines)
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


def get_file_id(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


# =========================================================
# ESTADO DE SESIÓN
# =========================================================

if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = {
        "amount": "",
        "reference": "",
        "date": "",
        "raw_text": "",
        "confidence": 0.0,
    }

if "deposit_submitted" not in st.session_state:
    st.session_state.deposit_submitted = False


# =========================================================
# HEADER
# =========================================================

st.markdown(
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
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FORMULARIO
# =========================================================

st.markdown('<div class="cashier-shell">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="utility-row">
        <span class="back-pill">← Atrás</span>
        <span class="balance-pill">Saldo&nbsp;&nbsp; USD $0.00</span>
    </div>

    <div class="section-title">REPORTAR UN DEPÓSITO</div>
    """,
    unsafe_allow_html=True,
)

account = st.selectbox(
    "Selecciona la cuenta donde depositaste",
    options=DEPOSIT_ACCOUNTS,
)

uploaded_file = st.file_uploader(
    "Sube el comprobante del depósito",
    type=["jpg", "jpeg", "png"],
    help="Tamaño máximo recomendado: 3 MB.",
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    current_file_id = get_file_id(file_bytes)

    if st.session_state.current_file_id != current_file_id:
        st.session_state.current_file_id = current_file_id
        st.session_state.deposit_submitted = False

        with st.spinner(
            "Leyendo la información del comprobante..."
        ):
            try:
                st.session_state.ocr_data = process_receipt(
                    file_bytes
                )

            except Exception as exc:
                st.session_state.ocr_data = {
                    "amount": "",
                    "reference": "",
                    "date": "",
                    "raw_text": "",
                    "confidence": 0.0,
                }

                st.error(
                    "No fue posible procesar el comprobante."
                )

                with st.expander(
                    "Ver detalle técnico"
                ):
                    st.exception(exc)

    confidence = (
        st.session_state.ocr_data["confidence"] * 100
    )

    st.markdown(
        f"""
        <div class="ocr-message">
            El comprobante fue procesado automáticamente.
            Revisa y corrige los campos antes de reportar el depósito.
            <br>
            <strong>Confianza promedio OCR:</strong>
            {confidence:.1f}%
        </div>
        """,
        unsafe_allow_html=True,
    )

amount = st.text_input(
    "Monto depositado",
    value=st.session_state.ocr_data["amount"],
    placeholder="USD 0.00",
    help="Monto mínimo: USD 10.00. Monto máximo: USD 20,000.00.",
)

reference = st.text_input(
    "Ingresa el número de referencia",
    value=st.session_state.ocr_data["reference"],
    placeholder="Número de referencia",
)

deposit_date = st.text_input(
    "Selecciona la fecha del depósito",
    value=st.session_state.ocr_data["date"],
    placeholder="DD / MM / YYYY",
)

if uploaded_file is None:
    st.markdown(
        '<div class="required-message">'
        "Este documento es obligatorio"
        "</div>",
        unsafe_allow_html=True,
    )

parsed_amount = parse_amount(amount)

required_fields_complete = all(
    [
        uploaded_file is not None,
        parsed_amount is not None,
        parsed_amount >= 10,
        bool(clean_text(reference)),
        bool(clean_text(deposit_date)),
    ]
)

if parsed_amount is not None and parsed_amount < 10:
    st.warning(
        "El monto mínimo permitido es USD 10.00."
    )

if parsed_amount is not None and parsed_amount > 20000:
    st.warning(
        "El monto máximo permitido es USD 20,000.00."
    )
    required_fields_complete = False

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

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# RESULTADO
# =========================================================

if submit_button:
    st.session_state.deposit_submitted = True

    deposit_result = {
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
        st.json(deposit_result)


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
                value=st.session_state.ocr_data["raw_text"],
                height=350,
                disabled=True,
            )