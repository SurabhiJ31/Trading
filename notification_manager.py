import uuid
import streamlit as st
from global_logging import logger
import queue

notification_queue = queue.Queue()

def drain_notifications():
    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    while not notification_queue.empty():
        st.session_state.notifications.append(
            notification_queue.get()
        )

@st.fragment(run_every="2s")
def notification_fragment():
    try:
        drain_notifications()

        colors = {
            "info": "#1f77b4",
            "success": "#2e7d32",
            "warning": "#ed6c02",
            "error": "#d32f2f"
        }

        for notif in list(st.session_state.get("notifications", [])):

            col1, col2 = st.columns([20, 1])

            with col1:
                st.markdown(
                    f"""
                    <div style="
                        background-color:{colors.get(notif['type'], '#1f77b4')};
                        padding:12px;
                        margin-bottom:8px;
                        border-radius:6px;
                        color:white;
                        font-size:15px;">
                        {notif['message']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.button(
                    "✖",
                    key=f"dismiss_{notif['id']}",
                    on_click=lambda nid=notif["id"]: dismiss_notification(nid)
                )
    except Exception as e:
        logger.error(e)

def add_notification(message, ntype="info"):
    logger.info(f"in add notif {message}")
    notification_queue.put({
        "id": str(uuid.uuid4()),
        "message": message,
        "type": ntype
    })
    logger.info("notif added")

def dismiss_notification(nid):
    st.session_state.notifications = [
        n for n in st.session_state.notifications
        if n["id"] != nid
    ]