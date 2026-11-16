import re
from typing import Optional, Tuple
from urllib.parse import quote, urlencode
import qrcode
from PIL import Image, ImageDraw



def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts a hex string like #8B5CF6 to RGB tuple (139, 92, 246)."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return (r, g, b)


def create_linear_gradient(
    width: int, height: int, start_hex: str, end_hex: str, direction: str = "Horizontal"
) -> Image.Image:
    """Creates a smooth linear gradient image of specified dimensions and direction."""
    r1, g1, b1 = hex_to_rgb(start_hex)
    r2, g2, b2 = hex_to_rgb(end_hex)

    gradient = Image.new("RGB", (width, height), (r1, g1, b1))
    draw = ImageDraw.Draw(gradient)

    if direction == "Vertical":
        for y in range(height):
            ratio = y / max(1, height - 1)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

    elif direction == "Diagonal":
        max_dist = max(1, width + height)
        for i in range(max_dist):
            ratio = i / max_dist
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, i), (i, 0)], fill=(r, g, b))

    else:  # Horizontal default
        for x in range(width):
            ratio = x / max(1, width - 1)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))

    return gradient


def generate_qr_image(
    payload: str,
    fill_color: str = "#8B5CF6",
    back_color: str = "#FFFFFF",
    size: int = 256,
    error_correction_level: str = "H",
    gradient_type: str = "Solid",
    gradient_end_color: Optional[str] = None,
    logo_image: Optional[Image.Image] = None,
    logo_padding: bool = True,
    border_size: int = 3,
) -> Image.Image:
    """
    Generates a high-quality QR code PIL Image with support for:
    - High / customizable error correction
    - Solid or linear gradient foregrounds
    - Custom background color
    - Center logo overlay with protective background
    - Precise pixel dimension scaling
    """
    # Map error correction
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    # If a logo is embedded, always force High (H) error correction for scannability
    ec_level = qrcode.constants.ERROR_CORRECT_H if logo_image else ec_map.get(error_correction_level, qrcode.constants.ERROR_CORRECT_H)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=10,
        border=border_size,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    # Base QR monochrome image (Black modules, White background)
    base_img = qr.make_image(fill_color="black", back_color="white").convert("L")
    base_img = base_img.resize((size, size), Image.Resampling.NEAREST)

    # Apply Color or Gradient
    bg_rgb = hex_to_rgb(back_color)
    output_img = Image.new("RGB", (size, size), bg_rgb)

    if gradient_type != "Solid" and gradient_end_color:
        direction = "Horizontal"
        if "Vertical" in gradient_type:
            direction = "Vertical"
        elif "Diagonal" in gradient_type:
            direction = "Diagonal"

        fg_layer = create_linear_gradient(size, size, fill_color, gradient_end_color, direction)
    else:
        fg_rgb = hex_to_rgb(fill_color)
        fg_layer = Image.new("RGB", (size, size), fg_rgb)

    # Mask: Dark modules in base_img (0 = black) become foreground, (255 = white) become background
    # Invert mask so black modules have value 255 (opaque in mask)
    mask = Image.eval(base_img, lambda a: 255 - a)
    output_img.paste(fg_layer, (0, 0), mask)

    # Embed Center Logo if provided
    if logo_image:
        logo = logo_image.convert("RGBA")
        # Keep logo to ~22% of total QR size to ensure scannability without obscuring timing patterns
        max_logo_size = int(size * 0.22)
        logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)
        lw, lh = logo.size

        pos_x = (size - lw) // 2
        pos_y = (size - lh) // 2

        if logo_padding:
            pad = max(4, int(max_logo_size * 0.12))
            # Draw rounded white background plate
            plate = Image.new("RGBA", (lw + pad * 2, lh + pad * 2), (255, 255, 255, 255))
            output_img.paste(plate, (pos_x - pad, pos_y - pad))

        # Paste logo
        output_img.paste(logo, (pos_x, pos_y), logo)

    return output_img


# ---------------------------------------------------------------------------
# Standard QR Payload Formatters
# ---------------------------------------------------------------------------

def format_vcard(name: str, phone: str, email: str, company: str) -> str:
    """Formats contact information into standard vCard 3.0 format."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{name.strip()}",
        f"FN:{name.strip()}",
        f"ORG:{company.strip()}",
        f"TEL:{phone.strip()}",
        f"EMAIL:{email.strip()}",
        "END:VCARD",
    ]
    return "\n".join(lines)


def format_wifi(ssid: str, password: str, security: str = "WPA/WPA2", hidden: bool = False) -> str:
    """Formats Wi-Fi credentials into standard WIFI: protocol."""
    sec_code = "WPA"
    if security == "WEP":
        sec_code = "WEP"
    elif security in ("No Password", "nopass", "None"):
        sec_code = "nopass"
        password = ""

    hidden_str = "true" if hidden else "false"
    # Format: WIFI:T:<sec>;S:<ssid>;P:<password>;H:<hidden>;;
    return f"WIFI:T:{sec_code};S:{ssid};P:{password};H:{hidden_str};;"


def format_whatsapp(country_code: str, phone_number: str, message: str = "") -> str:
    """Formats WhatsApp click-to-chat URI."""
    cc = re.sub(r"[^\d]", "", country_code)
    num = re.sub(r"[^\d]", "", phone_number)
    full_num = f"{cc}{num}"
    base_url = f"https://wa.me/{full_num}"
    if message.strip():
        encoded_msg = quote(message.strip())
        return f"{base_url}?text={encoded_msg}"
    return base_url


def format_upi(payee_name: str, upi_id: str, amount: Optional[float] = None, note: str = "") -> str:
    """Formats Indian UPI payment URI according to NPCI specifications."""
    params = {
        "pa": upi_id.strip(),
        "pn": payee_name.strip(),
        "cu": "INR",
    }
    if amount and amount > 0:
        params["am"] = f"{amount:.2f}"
    if note.strip():
        params["tn"] = note.strip()

    query_str = urlencode(params, quote_via=quote)
    return f"upi://pay?{query_str}"


def format_maps(lat: Optional[float] = None, lng: Optional[float] = None, direct_url: str = "") -> str:
    """Formats Google Maps location URL."""
    if direct_url.strip():
        url = direct_url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url
    if lat is not None and lng is not None:
        return f"https://www.google.com/maps?q={lat},{lng}"
    return "https://www.google.com/maps"


def format_social(platform: str, username_or_url: str) -> str:
    """Formats social media profile links into verified URLs."""
    raw = username_or_url.strip()
    if raw.startswith(("http://", "https://")):
        return raw

    clean_user = raw.lstrip("@").strip()
    routes = {
        "Instagram": f"https://instagram.com/{clean_user}",
        "Facebook": f"https://facebook.com/{clean_user}",
        "YouTube": f"https://youtube.com/@{clean_user}",
        "LinkedIn": f"https://linkedin.com/in/{clean_user}",
        "X (Twitter)": f"https://x.com/{clean_user}",
        "Website": f"https://{raw}",
    }
    return routes.get(platform, f"https://{raw}")


def format_google_forms(form_url: str) -> str:
    """Validates and formats a Google Forms responder link."""
    clean = form_url.strip()
    if not clean:
        return ""
    if not clean.startswith(("http://", "https://")):
        clean = "https://" + clean
    return clean

