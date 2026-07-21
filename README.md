# OCR de comprobantes bancarios

Prototipo desarrollado en Python y Streamlit para leer comprobantes
bancarios mediante OCR.

## Funcionalidades

- Carga de comprobantes en formato JPG, JPEG o PNG.
- Extracción automática de información mediante EasyOCR.
- Identificación de banco, cuenta, monto, fecha, hora y referencia.
- Corrección manual de los datos extraídos.
- Descarga del resultado revisado en formato JSON.

## Instalación

1. Crear un entorno virtual:

```bash
python -m venv .venv