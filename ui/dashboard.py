import streamlit as st
from services.history_service import (
    get_stats,
    get_history,
    delete_history_item,
    clear_all_history,
)


def render_dashboard() -> None:
    """Renders the comprehensive executive SaaS dashboard matching Section 3."""
    stats = get_stats()

    # Top Header: Welcome & Search
    top_c1, top_c2 = st.columns([3, 2], gap="medium")
    with top_c1:
        st.markdown(
            """
            <div>
                <h1 style="font-size: 1.6rem; font-weight: 800; color: #211B45; margin: 0; line-height: 1.2;">
                    👋 Welcome back!
                </h1>
                <p style="color: #6D28D9; font-size: 0.88rem; font-weight: 500; margin: 4px 0 0 0;">
                    Create, customize, and track your high-resolution QR codes with ease.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_c2:
        search_kw = st.text_input(
            "Quick Search",
            placeholder="🔍 Search generated codes...",
            label_visibility="collapsed",
            key="dash_quick_search",
        )

    st.write("")

    # Statistics Cards (4 Cards)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4, gap="small")

    with m_col1:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #6D28D9; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Total QR Generated</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size: 1.85rem; font-weight: 800; color: #211B45; margin: 4px 0;'>{stats['total_generated']}</div>",
                unsafe_allow_html=True,
            )
            st.caption("📈 All-time creations")

    with m_col2:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #6D28D9; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Total Downloads</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size: 1.85rem; font-weight: 800; color: #10B981; margin: 4px 0;'>{stats['total_downloads']}</div>",
                unsafe_allow_html=True,
            )
            st.caption("📥 High-res exports")

    with m_col3:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #6D28D9; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">QR Types Available</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size: 1.85rem; font-weight: 800; color: #8B5CF6; margin: 4px 0;'>8 Types</div>",
                unsafe_allow_html=True,
            )
            st.caption("🌐 Forms, UPI, Wi-Fi & more")

    with m_col4:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color: #6D28D9; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Recent Activities</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size: 1.85rem; font-weight: 800; color: #6D28D9; margin: 4px 0;'>{stats['history_count']}</div>",
                unsafe_allow_html=True,
            )
            st.caption("🔒 SQLite logs stored")

    st.write("")

    # Recent Activity Section
    with st.container(border=True):
        recent_items = get_history(search_query=search_kw)[:8]

        header_col, action_col = st.columns([3.5, 1.2])
        with header_col:
            st.markdown(
                "<div style='font-weight: 700; font-size: 1.05rem; margin-bottom: 8px; color: #211B45;'>🕒 Recent QR Activities</div>",
                unsafe_allow_html=True,
            )
        with action_col:
            if recent_items:
                if st.button("🗑️ Clear All", key="dash_clear_all_recent", use_container_width=True):
                    clear_all_history()
                    st.rerun()

        if recent_items:
            # Table Header
            h_c1, h_c2, h_c3, h_c4, h_c5 = st.columns([0.6, 2.4, 1.6, 2.2, 1.2])
            with h_c1:
                st.markdown("<span style='font-weight:700; color:#6D28D9; font-size:0.85rem;'>ID</span>", unsafe_allow_html=True)
            with h_c2:
                st.markdown("<span style='font-weight:700; color:#6D28D9; font-size:0.85rem;'>Name</span>", unsafe_allow_html=True)
            with h_c3:
                st.markdown("<span style='font-weight:700; color:#6D28D9; font-size:0.85rem;'>Type</span>", unsafe_allow_html=True)
            with h_c4:
                st.markdown("<span style='font-weight:700; color:#6D28D9; font-size:0.85rem;'>Created At</span>", unsafe_allow_html=True)
            with h_c5:
                st.markdown("<span style='font-weight:700; color:#6D28D9; font-size:0.85rem;'>Action</span>", unsafe_allow_html=True)

            st.markdown("<div style='border-bottom: 1px solid #ECEAFD; margin: 4px 0 10px 0;'></div>", unsafe_allow_html=True)

            for item in recent_items:
                c1, c2, c3, c4, c5 = st.columns([0.6, 2.4, 1.6, 2.2, 1.2])
                with c1:
                    st.write(str(item["id"]))
                with c2:
                    st.write(f"**{item['name']}**")
                with c3:
                    st.caption(f"`{item['qr_type']}`")
                with c4:
                    st.caption(item["created_at"])
                with c5:
                    if st.button("🗑️ Delete", key=f"dash_del_{item['id']}"):
                        delete_history_item(item["id"])
                        st.rerun()
        else:
            st.info("No QR codes generated yet. Use the sidebar navigation to create your first code!")
