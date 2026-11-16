import io
import zipfile
import sys
from pathlib import Path

# Add project root to sys.path so modules are always resolvable
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore

# UI Modules
from ui.components import (
    load_css,
    render_header,
    render_customization_card,
    render_preview_and_exports,
    render_feature_cards,
)
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard

# Service Modules
from services.qr_service import (
    generate_qr_image,
    format_vcard,
    format_wifi,
    format_whatsapp,
    format_upi,
    format_maps,
    format_social,
    format_google_forms,
)
from services.export_service import export_png, export_jpg, export_svg, export_pdf
from services.bulk_service import parse_uploaded_dataset, generate_bulk_qrs
from services.history_service import (
    init_db,
    get_history,
    delete_history_item,
    clear_all_history,
    log_download,
)

# ---------------------------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------------------------
APP_ICON_PATH = PROJECT_ROOT / "assets" / "app_icon_small.png"
page_icon_obj = str(APP_ICON_PATH) if APP_ICON_PATH.exists() else "📱"

st.set_page_config(
    page_title="Advanced QR Code Generator",
    page_icon=page_icon_obj,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
init_db()

# Load Stylesheet
BASE_DIR = Path(__file__).resolve().parent
load_css(BASE_DIR / "assets" / "style.css")

# Render Sidebar Navigation
active_page = render_sidebar()


# ---------------------------------------------------------------------------
# Helper: Standard Two-Column Generator Layout
# ---------------------------------------------------------------------------
def render_generator_layout(
    title: str,
    subtitle: str,
    badge: str,
    input_form_renderer,
    default_name: str,
    qr_type: str,
):
    """Generic high-level layout supporting Left Column (Input + Style) and Right Column (Preview + Multi-Export)."""
    render_header(title=title, subtitle=subtitle, badge=badge)

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        # Card 1: Content Specific Form
        payload, input_error, content_name = input_form_renderer()
        # Card 2: Advanced Customization
        style_cfg = render_customization_card(card_key_suffix=qr_type.lower().replace(" ", "_"))

    active_error = input_error or style_cfg["color_error"]
    pil_img = None

    if not active_error and payload:
        try:
            pil_img = generate_qr_image(
                payload=payload,
                fill_color=style_cfg["fill_color"],
                back_color=style_cfg["back_color"],
                size=style_cfg["size"],
                error_correction_level=style_cfg["error_correction_level"],
                gradient_type=style_cfg["gradient_type"],
                gradient_end_color=style_cfg["gradient_end_color"],
                logo_image=style_cfg["logo_image"],
                logo_padding=style_cfg["logo_padding"],
                border_size=style_cfg["border_size"],
            )
        except Exception as e:
            active_error = f"Generation error: {str(e)}"

    with col_right:
        render_preview_and_exports(
            pil_img=pil_img,
            payload=payload or "",
            qr_name=content_name or default_name,
            qr_type=qr_type,
            qr_size=style_cfg["size"],
            error_message=active_error,
        )

    render_feature_cards()


# ===========================================================================
# 1. PAGE: DASHBOARD
# ===========================================================================
if active_page == "Dashboard":
    render_header(
        title="QR Suite Dashboard",
        subtitle="Live metrics, recent creation logs, and generator shortcuts",
        badge="OVERVIEW",
    )
    render_dashboard()


# ===========================================================================
# 2. PAGE: CREATE QR (URL, Text, Contact)
# ===========================================================================
elif active_page == "Create QR":

    def content_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#211B45; margin-bottom:12px;">Content Selection</div>',
                unsafe_allow_html=True,
            )

            # Check if template pre-fill is active
            prefill = st.session_state.get("template_prefill", {})
            tab_override = st.session_state.get("create_qr_tab", None)

            default_tab = "🔗 URL"
            if tab_override:
                default_tab = tab_override
                st.session_state.pop("create_qr_tab")
            elif prefill.get("default_type") == "Contact":
                default_tab = "👤 Contact"
            elif prefill.get("default_type") == "Text":
                default_tab = "≡ Text"
            elif prefill.get("default_type") == "WhatsApp":
                default_tab = "💬 WhatsApp"
            elif prefill.get("default_type") == "Wi-Fi":
                default_tab = "📶 Wi-Fi"
            elif prefill.get("default_type") == "UPI Payment":
                default_tab = "💳 UPI"

            all_tabs = ["🔗 URL", "≡ Text", "👤 Contact", "💬 WhatsApp", "📶 Wi-Fi", "📋 Google Forms", "💳 UPI"]
            if default_tab not in all_tabs:
                default_tab = "🔗 URL"

            selected_tab = st.segmented_control(
                "Select Content Mode",
                options=all_tabs,
                default=default_tab,
                label_visibility="collapsed",
                key="gen_content_tab",
            )

            payload = ""
            error = None
            name = "my_qr"

            if selected_tab == "🔗 URL":
                default_url = prefill.get("sample_data", "https://blink.new") if prefill else "https://blink.new"
                url_val = st.text_input(
                    "Website URL",
                    value=default_url,
                    placeholder="https://example.com",
                    key="create_url_in",
                )
                if url_val.strip():
                    u_clean = url_val.strip()
                    if not u_clean.startswith(("http://", "https://")):
                        u_clean = "https://" + u_clean
                    payload = u_clean
                    name = "website_qr"
                else:
                    error = "Please enter a valid website URL."

            elif selected_tab == "≡ Text":
                text_val = st.text_area(
                    "Plain Text",
                    placeholder="Enter any text, code, or serial number...",
                    height=110,
                    key="create_text_in",
                )
                if text_val.strip():
                    payload = text_val.strip()
                    name = "text_qr"
                else:
                    error = "Please enter some text."

            elif selected_tab == "👤 Contact":
                c_name = st.text_input("Full Name", placeholder="e.g. Jane Doe", key="create_c_name")
                c_phone = st.text_input("Phone Number", placeholder="e.g. +1 555-123-4567", key="create_c_phone")
                c_email = st.text_input("Email", placeholder="e.g. jane@company.com", key="create_c_email")
                c_comp = st.text_input("Company", placeholder="e.g. Acme Corp", key="create_c_comp")

                if any([c_name.strip(), c_phone.strip(), c_email.strip(), c_comp.strip()]):
                    payload = format_vcard(c_name, c_phone, c_email, c_comp)
                    name = f"contact_{c_name.strip()}" if c_name.strip() else "contact_qr"
                else:
                    error = "Please fill in at least one contact field."

            elif selected_tab == "💬 WhatsApp":
                w_code = st.text_input("Country Code", value="+1", placeholder="+1 or +91", key="create_w_code")
                w_phone = st.text_input("Mobile Number", placeholder="1234567890", key="create_w_phone")
                w_msg = st.text_area("Pre-filled Message", placeholder="Hello! I am inquiring about...", height=80, key="create_w_msg")
                if w_phone.strip():
                    payload = format_whatsapp(w_code, w_phone, w_msg)
                    name = f"whatsapp_{w_phone.strip()}"
                else:
                    error = "Please enter a valid mobile number."

            elif selected_tab == "📶 Wi-Fi":
                wf_ssid = st.text_input("Network Name (SSID)", placeholder="e.g. Office_WiFi", key="create_wf_ssid")
                wf_sec = st.selectbox("Security Type", ["WPA/WPA2", "WEP", "No Password"], key="create_wf_sec")
                wf_pass = st.text_input("Password", type="password", key="create_wf_pass")
                wf_hidden = st.checkbox("Hidden Network", key="create_wf_hidden")
                if wf_ssid.strip():
                    payload = format_wifi(wf_ssid, wf_pass, wf_sec, wf_hidden)
                    name = f"wifi_{wf_ssid.strip()}"
                else:
                    error = "Please enter the Wi-Fi network name (SSID)."

            elif selected_tab == "📋 Google Forms":
                gf_title = st.text_input("Form Title", value="Event Registration", key="create_gf_title")
                gf_url = st.text_input("Google Forms Responder URL", value="https://forms.gle/sampleResponder123", key="create_gf_url")
                if gf_url.strip():
                    payload = format_google_forms(gf_url)
                    name = f"gform_{gf_title.strip().lower().replace(' ', '_')}"
                else:
                    error = "Please enter a Google Forms responder URL."

            elif selected_tab == "💳 UPI":
                u_name = st.text_input("Payee Name", placeholder="e.g. Acme Stores", key="create_upi_name")
                u_id = st.text_input("UPI ID / VPA", placeholder="e.g. business@okaxis", key="create_upi_id")
                u_amt = st.number_input("Amount (INR)", min_value=0.0, value=0.0, step=10.0, key="create_upi_amt")
                u_note = st.text_input("Transaction Note", placeholder="e.g. Invoice #1024", key="create_upi_note")
                if u_id.strip() and u_name.strip():
                    payload = format_upi(u_name, u_id, u_amt if u_amt > 0 else None, u_note)
                    name = f"upi_{u_name.strip().lower().replace(' ', '_')}"
                else:
                    error = "Payee name and valid UPI ID are required."

            # Clear template prefill once consumed
            if "template_prefill" in st.session_state:
                st.session_state.pop("template_prefill")

            return payload, error, name

    render_generator_layout(
        title="QR Code Generator",
        subtitle="Create custom QR codes for websites, plain text, and contact vCards",
        badge="STANDARD",
        input_form_renderer=content_inputs,
        default_name="qr_code",
        qr_type="Standard",
    )


# ===========================================================================
# 3. PAGE: WHATSAPP QR (Module 1)
# ===========================================================================
elif active_page == "WhatsApp QR":

    def whatsapp_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">💬 WhatsApp Configuration</div>',
                unsafe_allow_html=True,
            )

            col_w1, col_w2 = st.columns([1, 2.5])
            with col_w1:
                cc = st.text_input("Country Code", value="1", placeholder="1 or 91", key="wa_cc")
            with col_w2:
                phone = st.text_input("Mobile Number", placeholder="e.g. 5551234567", key="wa_phone")

            msg = st.text_area(
                "Pre-filled Message (Optional)",
                placeholder="Hi, I am reaching out regarding...",
                height=90,
                key="wa_msg",
            )

            payload = ""
            error = None
            if not cc.strip() or not phone.strip():
                error = "Please enter both country code and mobile number."
            else:
                payload = format_whatsapp(cc, phone, msg)

            return payload, error, f"whatsapp_{phone.strip()}"

    render_generator_layout(
        title="WhatsApp QR Generator",
        subtitle="Generate instant click-to-chat WhatsApp QR codes with pre-filled messages",
        badge="WHATSAPP",
        input_form_renderer=whatsapp_inputs,
        default_name="whatsapp_qr",
        qr_type="WhatsApp",
    )


# ===========================================================================
# 4. PAGE: WI-FI QR (Module 2)
# ===========================================================================
elif active_page == "Wi-Fi QR":

    def wifi_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">📶 Wi-Fi Credentials</div>',
                unsafe_allow_html=True,
            )

            ssid = st.text_input("Network Name (SSID)", placeholder="e.g. Office_Guest_WiFi", key="wifi_ssid")
            sec = st.selectbox("Security Type", options=["WPA/WPA2", "WEP", "No Password"], key="wifi_sec")

            password = ""
            if sec != "No Password":
                password = st.text_input("Network Password", type="password", placeholder="Enter Wi-Fi password", key="wifi_pwd")

            hidden = st.checkbox("Hidden Network (SSID is not broadcasting)", value=False, key="wifi_hidden")

            payload = ""
            error = None
            if not ssid.strip():
                error = "Please enter the Wi-Fi Network SSID."
            else:
                payload = format_wifi(ssid.strip(), password.strip(), sec, hidden)

            return payload, error, f"wifi_{ssid.strip()}"

    render_generator_layout(
        title="Wi-Fi QR Generator",
        subtitle="Let guests and customers scan to join your Wi-Fi network without typing passwords",
        badge="WI-FI",
        input_form_renderer=wifi_inputs,
        default_name="wifi_qr",
        qr_type="Wi-Fi",
    )


# ===========================================================================
# 5. PAGE: UPI PAYMENT QR (Module 3)
# ===========================================================================
elif active_page == "UPI Payment QR":

    def upi_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">💳 UPI Payment Details</div>',
                unsafe_allow_html=True,
            )

            p_name = st.text_input("Payee / Merchant Name", placeholder="e.g. Apex Retail Store", key="upi_pname")
            p_id = st.text_input("UPI ID (VPA)", placeholder="e.g. store@okhdfcbank or 9876543210@paytm", key="upi_id")

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                amt = st.number_input("Amount in INR (0 for open amount)", min_value=0.0, step=10.0, value=0.0, key="upi_amt")
            with col_u2:
                desc = st.text_input("Transaction Note", placeholder="e.g. Invoice #1024", key="upi_note")

            st.caption(
                "🔒 **Notice:** Generating a QR code encodes payment coordinates only. It does not verify or execute funds transfer."
            )

            payload = ""
            error = None
            if not p_name.strip() or not p_id.strip():
                error = "Please enter both Payee Name and a valid UPI ID."
            elif "@" not in p_id:
                error = "Invalid UPI ID format. A valid UPI ID contains an '@' symbol (e.g. user@bank)."
            else:
                payload = format_upi(p_name, p_id, amt if amt > 0 else None, desc)

            return payload, error, f"upi_{p_name.strip().replace(' ', '_')}"

    render_generator_layout(
        title="UPI Payment QR Generator",
        subtitle="Indian UPI QR generator compatible with Google Pay, PhonePe, Paytm, and BHIM",
        badge="UPI PAY",
        input_form_renderer=upi_inputs,
        default_name="upi_payment_qr",
        qr_type="UPI Payment",
    )


# ===========================================================================
# 6. PAGE: GOOGLE MAPS LOCATION QR (Module 4)
# ===========================================================================
elif active_page == "Location QR":

    def location_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">📍 Location Coordinates</div>',
                unsafe_allow_html=True,
            )

            loc_mode = st.radio("Input Method", options=["Coordinates (Latitude / Longitude)", "Google Maps Share URL"], horizontal=True, key="loc_mode")

            payload = ""
            error = None
            name = "location_qr"

            if "Coordinates" in loc_mode:
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    lat = st.number_input("Latitude", value=37.7749, format="%.6f", key="loc_lat")
                with col_l2:
                    lng = st.number_input("Longitude", value=-122.4194, format="%.6f", key="loc_lng")
                payload = format_maps(lat=lat, lng=lng)
                name = f"location_{lat:.3f}_{lng:.3f}"
            else:
                map_url = st.text_input("Google Maps Link", placeholder="https://maps.app.goo.gl/...", key="loc_url")
                if map_url.strip():
                    payload = format_maps(direct_url=map_url.strip())
                    name = "location_map_qr"
                else:
                    error = "Please enter a valid Google Maps URL."

            return payload, error, name

    render_generator_layout(
        title="Google Maps Location QR",
        subtitle="Direct your guests or clients to exact GPS coordinates or business locations",
        badge="MAPS",
        input_form_renderer=location_inputs,
        default_name="location_qr",
        qr_type="Location",
    )


# ===========================================================================
# 7. PAGE: SOCIAL MEDIA QR (Module 5)
# ===========================================================================
elif active_page == "Social Media QR":

    def social_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">🌐 Social Media Channel</div>',
                unsafe_allow_html=True,
            )

            platform = st.selectbox(
                "Social Media Platform",
                options=["Instagram", "Facebook", "YouTube", "LinkedIn", "X (Twitter)", "Website"],
                key="social_platform",
            )

            handle = st.text_input(
                f"{platform} Handle or Full URL",
                placeholder="e.g. username or https://...",
                key="social_handle",
            )

            payload = ""
            error = None
            if not handle.strip():
                error = f"Please enter your {platform} profile handle or link."
            else:
                payload = format_social(platform, handle)

            return payload, error, f"social_{platform.lower().replace(' ', '_')}"

    render_generator_layout(
        title="Social Media QR Generator",
        subtitle="Grow your follower base across Instagram, YouTube, LinkedIn, X, and Facebook",
        badge="SOCIAL",
        input_form_renderer=social_inputs,
        default_name="social_qr",
        qr_type="Social Media",
    )


# ===========================================================================
# 8. PAGE: BULK QR GENERATOR (Module 9)
# ===========================================================================
elif active_page == "Bulk QR Generator":
    render_header(
        title="Bulk QR Generator",
        subtitle="Batch generate hundreds of QR codes from CSV or Excel files with instant ZIP download",
        badge="BATCH PRO",
    )

    with st.container(border=True):
        st.markdown(
            '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:8px;">1. Upload Dataset</div>',
            unsafe_allow_html=True,
        )
        st.caption("Upload a .csv or .xlsx file containing URLs, serial codes, names, or arbitrary content.")

        uploaded_file = st.file_uploader("Upload CSV / Excel File", type=["csv", "xlsx", "xls"], key="bulk_uploader")

        if uploaded_file:
            try:
                df = parse_uploaded_dataset(uploaded_file, uploaded_file.name)
                st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns.")

                # Data Preview
                with st.expander("👁️ View Uploaded Data Preview", expanded=True):
                    st.dataframe(df.head(5), use_container_width=True)

                st.markdown(
                    '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-top:16px; margin-bottom:8px;">2. Configure Columns & Styling</div>',
                    unsafe_allow_html=True,
                )

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    content_col = st.selectbox("Content Column (Required)", options=df.columns, key="bulk_c_col")
                with col_b2:
                    name_options = ["None (Auto-Index)"] + list(df.columns)
                    selected_name = st.selectbox("Filename Column (Optional)", options=name_options, key="bulk_n_col")
                    name_col = None if selected_name == "None (Auto-Index)" else selected_name

                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    b_fg = st.color_picker("QR Color", value="#8B5CF6", key="bulk_fg")
                with col_c2:
                    b_bg = st.color_picker("Background", value="#FFFFFF", key="bulk_bg")
                with col_c3:
                    b_size = st.slider("Pixel Size", min_value=128, max_value=512, value=256, step=64, key="bulk_size")

                st.write("")
                run_bulk_btn = st.button("🚀 Generate All QR Codes & Build ZIP", type="primary", use_container_width=True)

                if run_bulk_btn:
                    with st.spinner("Processing batch generation..."):
                        bulk_res = generate_bulk_qrs(
                            df=df,
                            content_col=content_col,
                            name_col=name_col,
                            fill_color=b_fg,
                            back_color=b_bg,
                            size=b_size,
                        )

                        st.success(f"🎉 Successfully generated {bulk_res['total_generated']} QR codes! ({bulk_res['total_skipped']} skipped)")

                        # Download All Button
                        st.download_button(
                            label=f"📦 Download All {bulk_res['total_generated']} QRs (ZIP Archive)",
                            data=bulk_res["zip_bytes"],
                            file_name="bulk_qr_codes.zip",
                            mime="application/zip",
                            type="primary",
                            key="dl_bulk_zip",
                        )

                        # Results table
                        st.subheader("Generated QR Codes")
                        res_df = pd.DataFrame(bulk_res["items"])[["Index", "Filename", "Content", "Status"]]
                        st.dataframe(res_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ Error processing dataset: {str(e)}")


# ===========================================================================
# 9. PAGE: QR CODE SCANNER (Module 10)
# ===========================================================================
elif active_page == "QR Scanner":
    try:
        from services.scanner_service import scan_qr_image
        scanner_import_error = None
    except Exception as exc:
        scan_qr_image = None
        scanner_import_error = str(exc)

    render_header(
        title="QR Code Scanner & Decoder",
        subtitle="Upload QR images to extract text, inspect links, and detect phone, email, and UPI actions",
        badge="SCANNER",
    )

    if scanner_import_error:
        st.warning(
            f"⚠️ **QR Scanner module is currently unavailable:** {scanner_import_error}\n\n"
            "Please ensure `opencv-python-headless` is properly installed."
        )

    col_s_left, col_s_right = st.columns([1, 1], gap="medium")

    with col_s_left:
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">📤 Upload QR Code Image</div>',
                unsafe_allow_html=True,
            )
            sc_upload = st.file_uploader(
                "Choose an image file (PNG, JPG, JPEG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
                key="scanner_file_up",
            )

            if sc_upload:
                st.image(sc_upload, caption="Uploaded Image", use_container_width=True)

    with col_s_right:
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#1E1B4B; margin-bottom:12px;">🔍 Decoded Information</div>',
                unsafe_allow_html=True,
            )

            if sc_upload:
                if scan_qr_image is None:
                    st.error(
                        f"Cannot process image because the QR scanner module could not be loaded: {scanner_import_error}"
                    )
                else:
                    with st.spinner("Analyzing image..."):
                        scan_res = scan_qr_image(sc_upload)

                    if scan_res["success"]:
                        meta = scan_res["meta"]
                        st.success(f"✅ Decoded Successfully • **{meta['badge']}**")

                        st.markdown(
                            f"""
                            <div style="background: #F9FAFB; padding: 14px; border-radius: 10px; border: 1px solid #E5E7EB; word-break: break-all; font-family: monospace; font-size: 0.95rem; margin-bottom: 14px;">
                                {scan_res['text']}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.info(f"🛡️ **Safety Preview:** {meta['safe_preview']}")

                        if meta.get("is_url") and meta.get("action_url"):
                            st.link_button("🌐 Open External Link (Safe New Tab)", url=meta["action_url"], type="primary")

                        # Copy assistance
                        st.text_area("Raw Text (Select and Copy)", value=scan_res["text"], height=80)
                    else:
                        st.error(scan_res["error"])
            else:
                st.info("Upload an image on the left to extract and inspect its QR data.")


# ===========================================================================
# 10. PAGE: QR CODE HISTORY (Module 11)
# ===========================================================================
elif active_page == "QR History":
    render_header(
        title="QR Generation History",
        subtitle="Search, review, re-download, and manage your previously generated QR codes",
        badge="PERSISTENT",
    )

    with st.container(border=True):
        col_h1, col_h2, col_h3 = st.columns([2, 1.2, 0.8])
        with col_h1:
            h_search = st.text_input("🔍 Search by Name or Content", placeholder="Type keywords...", key="hist_search")
        with col_h2:
            h_filter = st.selectbox(
                "Filter by Type",
                options=["All", "Standard", "WhatsApp", "Wi-Fi", "UPI Payment", "Location", "Social Media"],
                key="hist_filter",
            )
        with col_h3:
            st.write("")
            st.write("")
            if st.button("🗑️ Clear History", key="clear_hist_btn"):
                clear_all_history()
                st.rerun()

    history_records = get_history(search_query=h_search, type_filter=h_filter)

    if history_records:
        st.markdown(f"**Found {len(history_records)} historical records:**")

        for rec in history_records:
            with st.container(border=True):
                h_c1, h_c2, h_c3, h_c4 = st.columns([2, 3, 1.5, 1])
                with h_c1:
                    st.markdown(f"**{rec['name']}**")
                    st.caption(f"Type: `{rec['qr_type']}` | Size: {rec['size']}px")
                with h_c2:
                    st.code(rec["content"][:60] + ("..." if len(rec["content"]) > 60 else ""))
                with h_c3:
                    st.caption(f"Created:\n{rec['created_at']}")
                with h_c4:
                    if st.button("❌ Delete", key=f"del_rec_{rec['id']}"):
                        delete_history_item(rec["id"])
                        st.rerun()
    else:
        st.info("No records found in history. Generated QR codes will automatically log here.")


# ===========================================================================
# 11. PAGE: GOOGLE FORMS QR (Section 6)
# ===========================================================================
elif active_page == "Google Forms QR":

    def google_forms_inputs():
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem; font-weight:700; color:#211B45; margin-bottom:12px;">Google Forms Setup</div>',
                unsafe_allow_html=True,
            )
            gf_title = st.text_input(
                "Form Title",
                value="Event Registration Form",
                placeholder="e.g. Workshop Sign-up or Feedback Survey",
                key="gf_page_title",
            )
            gf_url = st.text_input(
                "Google Forms Responder URL",
                value="https://forms.gle/sampleResponder123",
                placeholder="https://forms.gle/... or https://docs.google.com/forms/d/e/.../viewform",
                help="Paste the exact responder link to your Google Form",
                key="gf_page_url",
            )
            gf_desc = st.text_area(
                "Description (Optional)",
                placeholder="Brief instructions for respondents...",
                height=80,
                key="gf_page_desc",
            )

            payload = ""
            error = None
            clean_name = gf_title.strip().lower().replace(" ", "_") if gf_title.strip() else "google_form"
            name = f"gform_{clean_name}"

            raw_url = gf_url.strip()
            if not raw_url:
                error = "Please enter your Google Forms responder link."
            else:
                formatted = format_google_forms(raw_url)
                if not (("forms.gle" in formatted) or ("docs.google.com/forms" in formatted) or formatted.startswith("http")):
                    error = "Please provide a valid Google Forms responder URL."
                else:
                    payload = formatted

            return payload, error, name

    render_generator_layout(
        title="Google Forms QR Code",
        subtitle="Generate instant QR codes for Google Forms questionnaires, event registrations, and feedback surveys",
        badge="FORMS",
        input_form_renderer=google_forms_inputs,
        default_name="google_form_qr",
        qr_type="Google Forms",
    )


# ===========================================================================
# 12. PAGE: DOWNLOAD CENTER (Section 5)
# ===========================================================================
elif active_page == "Download Center":
    render_header(
        title="Download & Export Center",
        subtitle="Access, re-download, and batch export all previously created QR codes in PNG, JPG, SVG, and PDF",
        badge="EXPORT HUB",
    )

    with st.container(border=True):
        dc_c1, dc_c2, dc_c3 = st.columns([2, 1.2, 1.2])
        with dc_c1:
            dc_search = st.text_input("🔍 Search Logs", placeholder="Filter by name or content...", key="dc_search")
        with dc_c2:
            dc_filter = st.selectbox(
                "Filter by Type",
                options=["All", "Standard", "WhatsApp", "Wi-Fi", "UPI Payment", "Location", "Social Media", "Google Forms"],
                key="dc_filter",
            )
        with dc_c3:
            st.write("")
            st.write("")
            all_records = get_history(search_query=dc_search, type_filter=dc_filter)
            if all_records:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for rec in all_records:
                        try:
                            rec_img = generate_qr_image(payload=rec["content"], fill_color="#8B5CF6", back_color="#FFFFFF", size=rec["size"])
                            img_bytes = export_png(rec_img)
                            safe_file = f"{rec['name'].lower().replace(' ', '_')}_{rec['id']}.png"
                            zip_file.writestr(safe_file, img_bytes)
                        except Exception:
                            continue
                zip_buf.seek(0)
                st.download_button(
                    label=f"📦 Export All ({len(all_records)}) as ZIP",
                    data=zip_buf.getvalue(),
                    file_name="all_qr_codes.zip",
                    mime="application/zip",
                    type="primary",
                    key="dc_dl_all_zip",
                )

    records = get_history(search_query=dc_search, type_filter=dc_filter)
    if records:
        st.markdown(f"**Showing {len(records)} QR Codes available for instant export:**")
        for rec in records:
            with st.container(border=True):
                r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2, 2.5, 1, 1, 1])
                with r_c1:
                    st.markdown(f"**{rec['name']}**")
                    st.caption(f"Type: `{rec['qr_type']}` | Size: {rec['size']}px")
                with r_c2:
                    st.code(rec["content"][:55] + ("..." if len(rec["content"]) > 55 else ""))

                try:
                    re_img = generate_qr_image(payload=rec["content"], fill_color="#8B5CF6", back_color="#FFFFFF", size=rec["size"])
                    with r_c3:
                        st.download_button("⬇️ PNG", data=export_png(re_img), file_name=f"{rec['name']}.png", mime="image/png", key=f"dc_png_{rec['id']}")
                    with r_c4:
                        st.download_button("⬇️ SVG", data=export_svg(rec["content"]), file_name=f"{rec['name']}.svg", mime="image/svg+xml", key=f"dc_svg_{rec['id']}")
                    with r_c5:
                        st.download_button("⬇️ PDF", data=export_pdf(re_img, title=rec["name"], subtitle=rec["content"][:50]), file_name=f"{rec['name']}.pdf", mime="application/pdf", key=f"dc_pdf_{rec['id']}")
                except Exception as e:
                    st.caption(f"Export error: {e}")
    else:
        st.info("No QR codes logged yet. Use any generator to create and export your first QR code!")


# ===========================================================================
# 14. PAGE: ABOUT (Section 5)
# ===========================================================================
elif active_page == "About":
    render_header(
        title="About Advanced QR Code Generator",
        subtitle="Professional, private, and high-performance QR code creation suite",
        badge="SUITE v2.0",
    )

    with st.container(border=True):
        st.markdown(
            """
            <div style="padding: 10px 4px;">
                <h3 style="color: #211B45; font-weight: 800; margin-bottom: 8px;">🚀 Advanced QR Code Generator Suite</h3>
                <p style="color: #4B5563; font-size: 0.95rem; line-height: 1.6;">
                    Advanced QR Code Generator is an enterprise-grade SaaS web application built with Python and Streamlit.
                    Designed for businesses, marketers, and developers, it delivers scannable, high-contrast, customizable QR codes
                    across standard and specialized workflows.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        col_a1, col_a2 = st.columns(2, gap="medium")
        with col_a1:
            st.markdown(
                """
                <div style="background: #F8F7FF; border: 1px solid #E9DFFF; border-radius: 12px; padding: 16px;">
                    <h4 style="color: #6D28D9; font-weight: 700; margin-bottom: 8px;">✨ Key Capabilities</h4>
                    <ul style="color: #4B5563; font-size: 0.9rem; line-height: 1.7; padding-left: 20px;">
                        <li><b>14 Specialized Modules:</b> URL, WhatsApp, Wi-Fi, UPI, Location, Social Media, Google Forms, Scanner & Bulk.</li>
                        <li><b>Vector & High-Res Formats:</b> Export directly to PNG, JPG, vector SVG, and print-ready PDF.</li>
                        <li><b>Custom Branding:</b> Embed custom center logos with automatic positioning pattern protection.</li>
                        <li><b>Linear Gradients:</b> Horizontal, vertical, and diagonal dual-tone color transitions.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_a2:
            st.markdown(
                """
                <div style="background: #F8F7FF; border: 1px solid #E9DFFF; border-radius: 12px; padding: 16px;">
                    <h4 style="color: #6D28D9; font-weight: 700; margin-bottom: 8px;">🔒 Privacy & Tech Architecture</h4>
                    <ul style="color: #4B5563; font-size: 0.9rem; line-height: 1.7; padding-left: 20px;">
                        <li><b>Zero Cloud Telemetry:</b> All QR matrices and images are generated locally in-memory.</li>
                        <li><b>Local SQLite Persistence:</b> Creation metrics and logs stay completely on your machine.</li>
                        <li><b>Engineered in Python:</b> Powered by Streamlit, Pillow, QRCode, ReportLab, OpenCV, and NumPy.</li>
                        <li><b>Modern SaaS Design:</b> Styled with Plus Jakarta Sans and a purple-white design system.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )




