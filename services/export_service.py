import io
from typing import Optional
from PIL import Image
import qrcode
from qrcode.image.svg import SvgPathImage


def export_png(pil_img: Image.Image) -> bytes:
    """Exports PIL image as PNG bytes."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def export_jpg(pil_img: Image.Image, quality: int = 95) -> bytes:
    """Exports PIL image as JPG bytes with high quality."""
    buf = io.BytesIO()
    # Convert RGBA to RGB for JPEG compatibility
    rgb_img = pil_img.convert("RGB")
    rgb_img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def export_svg(payload: str, fill_color: str = "#8B5CF6", back_color: str = "#FFFFFF") -> bytes:
    """Exports QR code as vector SVG markup bytes."""
    factory = SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
        image_factory=factory,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    svg_img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buf = io.BytesIO()
    svg_img.save(buf)
    return buf.getvalue()


def export_pdf(
    pil_img: Image.Image,
    title: str = "QR Code",
    subtitle: Optional[str] = None,
) -> bytes:
    """
    Creates a clean, print-ready PDF containing the QR code.
    Uses ReportLab if available, with Pillow fallback.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=letter)
        page_width, page_height = letter

        # Header Title
        c.setFont("Helvetica-Bold", 20)
        c.setFillColorRGB(0.18, 0.1, 0.4)  # Deep purple
        c.drawCentredString(page_width / 2.0, page_height - 80, title)

        if subtitle:
            c.setFont("Helvetica", 11)
            c.setFillColorRGB(0.4, 0.4, 0.45)
            c.drawCentredString(page_width / 2.0, page_height - 102, subtitle)

        # Draw QR Code centered
        qr_size = min(340, page_width - 160)
        qr_x = (page_width - qr_size) / 2.0
        qr_y = (page_height - qr_size) / 2.0 - 20

        # Memory buffer of PNG for reportlab
        img_buf = io.BytesIO()
        pil_img.save(img_buf, format="PNG")
        img_buf.seek(0)

        c.drawImage(ImageReader(img_buf), qr_x, qr_y, width=qr_size, height=qr_size)

        # Footer watermark
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.6, 0.6, 0.65)
        c.drawCentredString(
            page_width / 2.0,
            50,
            "Generated with Advanced QR Code Generator",
        )

        c.showPage()
        c.save()
        return pdf_buf.getvalue()

    except Exception:
        # Fallback to direct Pillow PDF generation
        pdf_buf = io.BytesIO()
        rgb_img = pil_img.convert("RGB")
        rgb_img.save(pdf_buf, format="PDF", resolution=150.0)
        return pdf_buf.getvalue()

