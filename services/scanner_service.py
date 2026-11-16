import re
from typing import Dict, Any
import numpy as np  # type: ignore
from PIL import Image  # type: ignore
import cv2  # type: ignore


def detect_qr_content_type(text: str) -> Dict[str, Any]:
    """Analyzes raw decoded text to detect its category, safety, and action link."""
    trimmed = text.strip()

    # URL Check
    if re.match(r"^https?://", trimmed, re.IGNORECASE):
        return {
            "type": "Website URL",
            "is_url": True,
            "action_url": trimmed,
            "badge": "🌐 URL",
            "safe_preview": f"Opens destination website: {trimmed}",
        }

    # WhatsApp Check
    if "wa.me/" in trimmed:
        return {
            "type": "WhatsApp Chat",
            "is_url": True,
            "action_url": trimmed,
            "badge": "💬 WhatsApp",
            "safe_preview": f"Starts chat at: {trimmed}",
        }

    # UPI Payment Check
    if trimmed.lower().startswith("upi://pay"):
        return {
            "type": "UPI Payment",
            "is_url": False,
            "action_url": trimmed,
            "badge": "💳 UPI Payment",
            "safe_preview": "Prompts payment on UPI-enabled mobile app (GPay/PhonePe/Paytm).",
        }

    # Wi-Fi Check
    if trimmed.startswith("WIFI:"):
        return {
            "type": "Wi-Fi Network",
            "is_url": False,
            "action_url": None,
            "badge": "📶 Wi-Fi Config",
            "safe_preview": "Contains Wi-Fi SSID and security keys for quick connection.",
        }

    # Phone Call Check
    if trimmed.startswith("tel:"):
        phone_num = trimmed.replace("tel:", "").strip()
        return {
            "type": "Phone Number",
            "is_url": False,
            "action_url": f"tel:{phone_num}",
            "badge": "📞 Phone Call",
            "safe_preview": f"Prompts dialing: {phone_num}",
        }
    elif re.match(r"^\+?[0-9\s\-()]{7,16}$", trimmed):
        return {
            "type": "Phone Number",
            "is_url": False,
            "action_url": f"tel:{trimmed}",
            "badge": "📞 Phone Call",
            "safe_preview": f"Prompts dialing: {trimmed}",
        }

    # Email Check
    if trimmed.startswith("mailto:"):
        return {
            "type": "Email Address",
            "is_url": False,
            "action_url": trimmed,
            "badge": "✉️ Email",
            "safe_preview": f"Opens mail client: {trimmed}",
        }
    elif re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", trimmed):
        return {
            "type": "Email Address",
            "is_url": False,
            "action_url": f"mailto:{trimmed}",
            "badge": "✉️ Email",
            "safe_preview": f"Opens mail client to: {trimmed}",
        }

    # Contact Card (vCard) Check
    if "BEGIN:VCARD" in trimmed:
        return {
            "type": "vCard Contact",
            "is_url": False,
            "action_url": None,
            "badge": "👤 Contact Card",
            "safe_preview": "Prompts adding contact card into smartphone contacts.",
        }

    # Default Plain Text
    return {
        "type": "Plain Text",
        "is_url": False,
        "action_url": None,
        "badge": "📝 Text",
        "safe_preview": "Standard alphanumeric text or code.",
    }


def scan_qr_image(image_file) -> Dict[str, Any]:
    """
    Decodes a QR code from an uploaded file object or PIL Image.
    Uses OpenCV QRCodeDetector.
    """
    try:
        # Open with PIL
        pil_img = Image.open(image_file).convert("RGB")
        # Convert to numpy array for OpenCV
        open_cv_image = np.array(pil_img)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()

        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(open_cv_image)

        if not data:
            # Try with grayscale enhancement
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            data, points, _ = detector.detectAndDecode(gray)

        if data and data.strip():
            content_meta = detect_qr_content_type(data.strip())
            return {
                "success": True,
                "text": data.strip(),
                "meta": content_meta,
                "points": points.tolist() if points is not None else None,
            }
        else:
            return {
                "success": False,
                "error": "No QR code could be detected in the uploaded image. Please ensure the code is clear, well-lit, and in focus.",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process image: {str(e)}",
        }

