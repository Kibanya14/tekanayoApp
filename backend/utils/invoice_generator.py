from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _theme_colors(theme: str):
    t = (theme or "classic").lower()
    if t == "modern":
        return colors.HexColor("#0f766e"), colors.HexColor("#ccfbf1")
    if t == "minimal":
        return colors.HexColor("#334155"), colors.HexColor("#f8fafc")
    if t == "bold":
        return colors.HexColor("#7c2d12"), colors.HexColor("#ffedd5")
    return colors.HexColor("#1d4ed8"), colors.HexColor("#dbeafe")


def generate_seller_invoice_pdf(order, shop):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    accent, bg = _theme_colors(getattr(shop, "invoice_theme", "classic"))

    c.setFillColor(bg)
    c.rect(0, height - 75 * mm, width, 75 * mm, stroke=0, fill=1)

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 25 * mm, f"Facture - {shop.name}")

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 34 * mm, f"Commande: {order.order_number}")
    c.drawString(20 * mm, height - 40 * mm, f"Client: {order.customer_name}")
    c.drawString(20 * mm, height - 46 * mm, f"Adresse: {order.shipping_address or '-'}")
    c.drawString(20 * mm, height - 52 * mm, f"Date: {order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else datetime.utcnow().strftime('%d/%m/%Y %H:%M')}")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 78 * mm, "Résumé")
    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, height - 88 * mm, f"Montant total: {order.total_amount:.2f} {shop.currency}")
    c.drawString(20 * mm, height - 96 * mm, f"Statut: {order.status}")

    c.setStrokeColor(accent)
    c.setLineWidth(2)
    c.line(20 * mm, height - 100 * mm, width - 20 * mm, height - 100 * mm)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(20 * mm, 18 * mm, f"Tekanayo App - Thème facture: {getattr(shop, 'invoice_theme', 'classic')}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
