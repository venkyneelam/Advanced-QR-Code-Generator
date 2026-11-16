import base64
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st
from PIL import Image

from services.export_service import export_png, export_jpg, export_pdf
from services.history_service import log_qr_creation, log_download


@st.cache_data
def get_app_icon_base64() -> str:
    """Returns base64 data URI for the project app icon."""
    base_dir = Path(__file__).resolve().parent.parent
    icon_path = base_dir / "assets" / "app_icon_small.png"
    if not icon_path.exists():
        icon_path = base_dir / "assets" / "app_icon.png"
    if icon_path.exists():
        try:
            with open(icon_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return ""


def load_css(css_file: Optional[Path] = None) -> None:
    """Loads external CSS file and injects into Streamlit markdown."""
    base_dir = Path(__file__).resolve().parent.parent
    candidates = []
    if css_file:
        candidates.append(Path(css_file))
    candidates.extend([
        base_dir / "assets" / "style.css",
        Path("assets/style.css"),
    ])

    for path in candidates:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    css_content = f.read()
                    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
                    return
            except Exception:
                continue


def render_header(
    title: str = "Advanced QR Code Generator",
    subtitle: str = "Enterprise-grade QR design, real-time preview, vector & print exports",
    badge: str = "PRO SUITE",
) -> None:
    """Renders the top navigation bar with a modern SaaS design."""
    icon_b64 = get_app_icon_base64()
    if icon_b64:
        icon_html = f'<img src="{icon_b64}" width="46" height="46" style="border-radius: 12px; box-shadow: 0 4px 14px rgba(109, 40, 217, 0.3); flex-shrink: 0;" />'
    else:
        icon_html = """
        <div style="background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35); font-size: 22px;">
            📱
        </div>
        """

    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FFFFFF;
            padding: 16px 24px;
            border-radius: 16px;
            border: 1px solid #ECEAFD;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.05);
            margin-bottom: 24px;
        ">
            <div style="display: flex; align-items: center; gap: 14px;">
                {icon_html}
                <div>
                    <div style="font-size: 1.45rem; font-weight: 800; color: #2E1065; letter-spacing: -0.02em; line-height: 1.2;">
                        {title}
                    </div>
                    <div style="font-size: 0.85rem; color: #6B7280; font-weight: 500; margin-top: 2px;">
                        {subtitle}
                    </div>
                </div>
            </div>
            <div style="
                background: #F3E8FF;
                color: #7C3AED;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.03em;
            ">
                {badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_customization_card(card_key_suffix: str = "") -> Dict[str, Any]:
    """
    Renders Card 2: Customization (Size, Colors, Gradient, Logo, and Error Correction).
    Returns a dictionary with all styling parameters.
    """
    with st.container(border=True):
        st.markdown(
            '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">🎨 Customization & Styling</div>',
            unsafe_allow_html=True,
        )

        # Tab for Colors & Gradient vs Logo & Advanced
        tab_style, tab_logo = st.tabs(["🖌️ Colors & Size", "🖼️ Center Logo"])

        with tab_style:
            # Color Mode
            color_mode = st.radio(
                "Foreground Fill Mode",
                options=["Solid Color", "Horizontal Gradient", "Vertical Gradient", "Diagonal Gradient"],
                horizontal=True,
                key=f"color_mode_{card_key_suffix}",
            )

            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.caption("**Primary Color**")
                fg_start = st.color_picker(
                    "Primary Color",
                    value="#8B5CF6",
                    label_visibility="collapsed",
                    key=f"fg_start_{card_key_suffix}",
                )
            with col_c2:
                st.caption("**Gradient End**" if color_mode != "Solid Color" else "**End Color (N/A)**")
                fg_end = st.color_picker(
                    "Gradient End Color",
                    value="#3B82F6",
                    label_visibility="collapsed",
                    disabled=(color_mode == "Solid Color"),
                    key=f"fg_end_{card_key_suffix}",
                )
            with col_c3:
                st.caption("**Background**")
                bg_color = st.color_picker(
                    "Background Color",
                    value="#FFFFFF",
                    label_visibility="collapsed",
                    key=f"bg_color_{card_key_suffix}",
                )

            # Size Slider
            qr_size = st.slider(
                "Dimensions",
                min_value=128,
                max_value=1024,
                value=256,
                step=64,
                format="Size: %dpx",
                key=f"qr_size_{card_key_suffix}",
            )

        with tab_logo:
            st.caption("Upload a PNG or JPG logo to embed in the center of the QR code.")
            uploaded_logo = st.file_uploader(
                "Upload Logo Image",
                type=["png", "jpg", "jpeg", "webp"],
                label_visibility="collapsed",
                key=f"logo_upload_{card_key_suffix}",
            )
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                logo_padding = st.checkbox("Add white logo background", value=True, key=f"logo_pad_{card_key_suffix}")
            with col_l2:
                ec_level = st.selectbox(
                    "Error Correction",
                    options=["H (High - 30%)", "Q (Quartile - 25%)", "M (Medium - 15%)", "L (Low - 7%)"],
                    index=0,
                    key=f"ec_level_{card_key_suffix}",
                )

            logo_img = None
            if uploaded_logo:
                try:
                    logo_img = Image.open(uploaded_logo)
                    st.success("✅ Logo attached successfully!")
                except Exception as e:
                    st.error(f"Invalid logo file: {e}")

        # Validation
        color_error = None
        if fg_start.lower() == bg_color.lower():
            color_error = "Foreground and Background colors cannot be identical."

        ec_code = ec_level[0] if ec_level else "H"

        return {
            "size": qr_size,
            "fill_color": fg_start,
            "gradient_end_color": fg_end if color_mode != "Solid Color" else None,
            "gradient_type": color_mode,
            "back_color": bg_color,
            "logo_image": logo_img,
            "logo_padding": logo_padding,
            "error_correction_level": ec_code,
            "border_size": 3,
            "color_error": color_error,
        }


def render_preview_and_exports(
    pil_img: Optional[Image.Image],
    payload: str,
    qr_name: str,
    qr_type: str,
    qr_size: int,
    error_message: Optional[str] = None,
) -> None:
    """
    Renders Card 3: Live Preview, Dimension metadata, and multi-format exports (PNG, JPG, SVG, PDF).
    """
    with st.container(border=True):
        st.markdown(
            '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">📱 Preview & Export</div>',
            unsafe_allow_html=True,
        )

        if error_message:
            st.warning(f"⚠️ {error_message}")
            st.button("📥 Download QR Code", disabled=True, key="disabled_preview_btn")
            st.markdown(
                f'<div style="text-align:center; color:#9CA3AF; font-size:0.85rem; margin-top:8px;">PNG • {qr_size}x{qr_size}px • High Quality</div>',
                unsafe_allow_html=True,
            )
            return

        if not pil_img or not payload:
            st.info("💡 Fill in the details on the left to generate a live QR code.")
            return

        # Elevated white box with QR Code
        st.markdown(
            """
            <div style="
                background: #FFFFFF;
                border-radius: 16px;
                box-shadow: 0 10px 28px rgba(139, 92, 246, 0.12);
                padding: 24px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 6px auto 14px auto;
                max-width: 300px;
                border: 1px solid #ECEAFD;
            ">
            """,
            unsafe_allow_html=True,
        )
        st.image(pil_img, width=240)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f'<div style="text-align:center; color:#9CA3AF; font-size:0.85rem; font-weight:500; margin-bottom:16px;">PNG • {qr_size}x{qr_size}px • High Quality</div>',
            unsafe_allow_html=True,
        )

        # Custom Filename
        custom_filename = st.text_input(
            "Custom Filename (without extension)",
            value=qr_name.lower().replace(" ", "_"),
            key=f"export_filename_{qr_type.lower().replace(' ', '_')}",
        )
        safe_name = custom_filename.strip() or "qr_code"

        # Multi-Format Export Buttons (PNG, JPG, PDF)
        st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#211B45; margin-bottom:6px;'>Choose Download Format:</p>", unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)

        # PNG
        png_bytes = export_png(pil_img)
        with col_f1:
            if st.download_button(
                label="⬇️ PNG",
                data=png_bytes,
                file_name=f"{safe_name}.png",
                mime="image/png",
                type="primary",
                use_container_width=True,
                key=f"dl_png_{qr_type}",
            ):
                log_qr_creation(safe_name, qr_type, payload, "PNG", qr_size)
                log_download()

        # JPG
        jpg_bytes = export_jpg(pil_img)
        with col_f2:
            if st.download_button(
                label="⬇️ JPG",
                data=jpg_bytes,
                file_name=f"{safe_name}.jpg",
                mime="image/jpeg",
                use_container_width=True,
                key=f"dl_jpg_{qr_type}",
            ):
                log_qr_creation(safe_name, qr_type, payload, "JPG", qr_size)
                log_download()

        # PDF
        pdf_bytes = export_pdf(pil_img, title=f"{qr_type} QR Code", subtitle=payload[:60])
        if st.download_button(
            label="⬇️ PDF",
            data=pdf_bytes,
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf_{qr_type}",
        ):
            log_qr_creation(safe_name, qr_type, payload, "PDF", qr_size)
            log_download()


def render_feature_cards() -> None:
    """Renders the 3 bottom feature cards in elevated container cards."""
    st.write("")
    col_feat1, col_feat2, col_feat3 = st.columns(3, gap="medium")

    with col_feat1:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align:center; padding:10px 6px;">
                    <div style="
                        background: #F3E8FF;
                        color: #8B5CF6;
                        width: 46px;
                        height: 46px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 12px auto;
                        font-size: 20px;
                    ">
                        ⚡
                    </div>
                    <div style="font-weight:700; font-size:1rem; color:#1E1B4B; margin-bottom:4px;">
                        Instant Generation
                    </div>
                    <div style="color:#6B7280; font-size:0.85rem; line-height:1.45;">
                        QR codes generated in real-time as you type
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_feat2:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align:center; padding:10px 6px;">
                    <div style="
                        background: #F3E8FF;
                        color: #8B5CF6;
                        width: 46px;
                        height: 46px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 12px auto;
                        font-size: 20px;
                    ">
                        🎨
                    </div>
                    <div style="font-weight:700; font-size:1rem; color:#1E1B4B; margin-bottom:4px;">
                        Full Customization
                    </div>
                    <div style="color:#6B7280; font-size:0.85rem; line-height:1.45;">
                        Choose colors and size to match your brand
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_feat3:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align:center; padding:10px 6px;">
                    <div style="
                        background: #F3E8FF;
                        color: #8B5CF6;
                        width: 46px;
                        height: 46px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 12px auto;
                        font-size: 20px;
                    ">
                        📥
                    </div>
                    <div style="font-weight:700; font-size:1rem; color:#1E1B4B; margin-bottom:4px;">
                        Easy Download
                    </div>
                    <div style="color:#6B7280; font-size:0.85rem; line-height:1.45;">
                        Export high-quality PNG, JPG, and PDF files
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
