# -*- coding: utf-8 -*-
import os
import subprocess
import time

# ========= RUTAS =========

# Imagen de la infografía (salida del Totem)
IMAGE_PATH = r"C:\Users\joses\Documents\Totem\infografias\infografia_totem.png"

# PDF temporal/definitivo para imprimir (media carta)
PDF_PATH = r"C:\Users\joses\Documents\Totem\infografias\infografia_Chur_Industries_MEDIACARTA.pdf"

# Ruta donde tienes SumatraPDF portable
SUMATRA_PATH = r"C:\Users\joses\OneDrive\Escritorio\SumatraPDF-3.5.2-64\SumatraPDF-3.5.2-64.exe"

# Nombre EXACTO de la impresora en Windows
PRINTER_NAME = r"HP Color LaserJet MFP M477fdw (3F853F)"


# ========= 1) CONVERTIR PNG -> PDF MEDIA CARTA =========

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def png_a_pdf_mediacarta(path_png: str, path_pdf: str) -> None:
    """
    Convierte un PNG a un PDF tamaño Media Carta (5.5 x 8.5 pulgadas)
    en horizontal (landscape), ocupando toda la página.
    """
    if not os.path.isfile(path_png):
        print(f"⚠️ La imagen NO existe: {path_png}")
        return

    # Media carta (5.5 x 8.5) pero en horizontal: 8.5 de ancho x 5.5 de alto
    width = 8.5 * inch
    height = 5.5 * inch

    c = canvas.Canvas(path_pdf, pagesize=(width, height))

    # Dibujar la imagen ocupando toda la página
    # (si la proporción no es exacta, se estira un poquito)
    c.drawImage(path_png, 0, 0, width=width, height=height)

    c.showPage()
    c.save()

    print(f"✅ PDF media carta generado: {path_pdf}")


# ========= 2) LIMPIAR COLA DE IMPRESIÓN =========

def limpiar_cola_impresora(printer_name: str) -> None:
    """Borra TODOS los trabajos pendientes de la cola de la impresora indicada."""
    print(f"🧹 Limpiando cola de impresión de: {printer_name!r}")
    cmd = [
        "powershell",
        "-Command",
        (
            f"Get-PrintJob -PrinterName '{printer_name}' "
            "| Remove-PrintJob -Confirm:$false"
        ),
    ]
    try:
        subprocess.run(cmd, check=False)
        print("✅ Cola de impresión limpiada (o ya estaba vacía).")
    except Exception as e:
        print(f"⚠️ No se pudo limpiar la cola de impresión: {e}")


# ========= 3) IMPRIMIR PDF CON SUMATRA (1 COPIA, AJUSTADO) =========

def imprimir_pdf_una_copia(path_pdf: str) -> None:
    print("=== IMPRESIÓN PDF (Sumatra, 1 copia, fit) ===")
    print(f"os.name       : {os.name}")
    print(f"PDF           : {path_pdf}")
    print(f"Sumatra exe   : {SUMATRA_PATH}")

    if not os.path.isfile(path_pdf):
        print(f"⚠️ El archivo PDF NO existe: {path_pdf}")
        return

    if os.name != "nt":
        print(f"⚠️ Solo implementado para Windows (os.name={os.name})")
        return

    if not os.path.isfile(SUMATRA_PATH):
        print(f"⚠️ SumatraPDF no encontrado en: {SUMATRA_PATH}")
        return

    # 1) Limpiar cola antes de imprimir
    limpiar_cola_impresora(PRINTER_NAME)
    time.sleep(1)

    # 2) Mandar SOLO 1 copia, ajustada a la hoja
    try:
        print('\n--- SumatraPDF -print-to-default -print-settings "fit,1x" ---')
        subprocess.run(
            [
                SUMATRA_PATH,
                "-print-to-default",
                "-exit-on-print",
                "-print-settings",
                "fit,1x",   # ajusta a la hoja + UNA sola copia
                path_pdf,
            ],
            check=True,
            shell=False,
        )
        print("🖨 (Sumatra) PDF enviado a la impresora (1 copia, media carta).")
    except Exception as e:
        print(f"❌ Error al imprimir con SumatraPDF: {e}")


# ========= 4) ORQUESTADOR =========

def imprimir_infografia_desde_png() -> None:
    # 1) Convertir PNG a PDF media carta
    png_a_pdf_mediacarta(IMAGE_PATH, PDF_PATH)

    # 2) Imprimir ese PDF una sola vez
    imprimir_pdf_una_copia(PDF_PATH)


if __name__ == "__main__":
    imprimir_infografia_desde_png()
