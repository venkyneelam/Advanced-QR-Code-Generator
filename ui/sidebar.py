import streamlit as st
from services.history_service import get_stats
from ui.components import get_app_icon_base64


NAVIGATION_OPTIONS = [
    ("🏠 Dashboard", "Dashboard"),
    ("➕ Create QR", "Create QR"),
    ("💬 WhatsApp QR", "WhatsApp QR"),
    ("📶 Wi-Fi QR", "Wi-Fi QR"),
    ("💳 UPI Payment QR", "UPI Payment QR"),
    ("📍 Location QR", "Location QR"),
    ("🔗 Social Media QR", "Social Media QR"),
    ("📋 Google Forms QR", "Google Forms QR"),
    ("📦 Bulk QR Generator", "Bulk QR Generator"),
    ("🔍 QR Scanner", "QR Scanner"),
    ("🕒 QR History", "QR History"),
    ("📥 Download Center", "Download Center"),
    ("ℹ️ About", "About"),
]


def render_sidebar() -> str:
    """Renders the clean left sidebar navigation matching the reference design."""
    with st.sidebar:
        # App Branding Header with Purple Gradient Accent & Official 3D Icon
        icon_b64 = get_app_icon_base64()
        if icon_b64:
            icon_badge = f'<img src="{icon_b64}" width="44" height="44" style="border-radius: 12px; box-shadow: 0 4px 14px rgba(109, 40, 217, 0.3); flex-shrink: 0;" />'
        else:
            icon_badge = """
            <div style="background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(109, 40, 217, 0.3);">
                📱
            </div>
            """

        st.markdown(
            f"""
            <div style="background: linear-gradient(180deg, #F3E8FF 0%, #FFFFFF 100%); border-radius: 14px; padding: 12px 10px 14px 10px; margin-bottom: 8px; border: 1px solid #ECEAFD;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        {icon_badge}
                        <div>
                            <div style="font-weight: 800; font-size: 1.12rem; color: #211B45; line-height: 1.15; letter-spacing: -0.02em;">QR Code Generator</div>
                            <div style="font-size: 0.74rem; color: #6D28D9; font-weight: 600; margin-top: 2px;">Create • Customize • Download</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Initialize current page in session state if missing
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        # Determine index for radio selector
        current_labels = [label for label, key in NAVIGATION_OPTIONS]
        current_keys = [key for label, key in NAVIGATION_OPTIONS]

        try:
            default_index = current_keys.index(st.session_state.current_page)
        except ValueError:
            default_index = 0

        selected_label = st.radio(
            "Navigation Menu",
            options=current_labels,
            index=default_index,
            label_visibility="collapsed",
            key="sidebar_radio",
        )

        # Sync back to page key
        for label, key in NAVIGATION_OPTIONS:
            if label == selected_label:
                st.session_state.current_page = key
                break

        # Sidebar Live Analytics Snapshot
        stats = get_stats()
        total_gen = stats.get("total_generated", 0)
        total_dl = stats.get("total_downloads", 0)

        # App Metrics Card matching reference image
        st.markdown(
            f"""
            <div style="background: #F3E8FF; border: 1px solid #E9DFFF; border-radius: 16px; padding: 14px 12px; margin-top: 16px; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-around; text-align: center;">
                    <div style="flex: 1;">
                        <div style="color: #6D28D9; margin-bottom: 2px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6D28D9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;">
                                <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
                                <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
                                <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
                                <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
                                <rect x="7" y="7" width="10" height="10"></rect>
                            </svg>
                        </div>
                        <div style="font-size: 1.55rem; font-weight: 800; color: #211B45; line-height: 1.1;">{total_gen}</div>
                        <div style="font-size: 0.74rem; font-weight: 700; color: #6D28D9; margin-top: 2px;">Generated</div>
                    </div>
                    <div style="width: 1px; height: 42px; background: #DDD6FE;"></div>
                    <div style="flex: 1;">
                        <div style="color: #6D28D9; margin-bottom: 2px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6D28D9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                        </div>
                        <div style="font-size: 1.55rem; font-weight: 800; color: #211B45; line-height: 1.1;">{total_dl}</div>
                        <div style="font-size: 0.74rem; font-weight: 700; color: #6D28D9; margin-top: 2px;">Downloads</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tip Card matching reference image
        st.markdown(
            """
            <div style="background: #F5F3FF; border: 1px solid #E9DFFF; border-radius: 14px; padding: 10px 12px; font-size: 0.78rem; color: #6D28D9; font-weight: 600; display: flex; align-items: center; gap: 8px; line-height: 1.35;">
                <span style="font-size: 1.1rem;">💡</span>
                <span><b>Tip:</b> Scan, share and stay connected with QR codes!</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.current_page
