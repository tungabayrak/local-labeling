import json
import requests
import streamlit as st
from tools import llm_generate
from manager import manager
import streamlit.components.v1 as components

st.set_page_config(page_title="Shark Label", page_icon="🦈", layout="wide")
big_title = st.empty()
big_title.markdown("# 🦈 Shark Label")

current_user_email = st.session_state.get("current_user_email")
logged_in = current_user_email != None

ADMIN_EMAILS = [
    "nightfever170@gmail.com",
    "tungabayrak@gmail.com",
    "torii.kyuu@gmail.com",
]

login_box = st.empty()
login_sidebar = st.sidebar.empty()
login_sidebar.header("Login to Continue")

with login_box.form(key="login_form"):
    st.markdown("Authenticate with Google")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submit_button = st.form_submit_button(label="Login")

    if submit_button and email and password:
        with st.spinner("Logging in"):
            # current_user = Auth.sign_in_with_email_and_password(email, password)
            if password != "@8sdJs!XcsfEG":
                current_user = {"error": {"message": "INVALID LOGIN CREDENTIALS"}}
            else:
                current_user = {"email": email, "": {}}

        if "error" in current_user:
            st.text(current_user["error"]["message"])
        else:
            if current_user["email"] in ADMIN_EMAILS:
                logged_in = True
                st.session_state["current_user_email"] = current_user["email"]

if logged_in:
    login_box.empty()
    login_sidebar.empty()
else:
    st.stop()

st.sidebar.header(f"🔑 {st.session_state['current_user_email']}")
INFO = "Information"
APP_MENU = "🚩 App"
DATA_MENU = "📅 Data"
selected_menu = st.sidebar.radio("Menus", [INFO, APP_MENU, DATA_MENU])

if st.sidebar.button("Logout"):
    st.session_state["current_user_email"] = None
    st.rerun()


if selected_menu == INFO:
    st.markdown("""### Information""")

elif selected_menu == APP_MENU:
    st.markdown(f"{len(manager.data)} images waiting to be labelled.")

    if st.button("Label", icon="➡️"):
        image_url = manager.load_image(st.session_state["current_user_email"])[
            "options"
        ]["backgroundImage"]["url"]

        with st.spinner("Downloading image"):
            resp = requests.get(image_url)

        with st.spinner("Generaing a.i. descriptors"):
            _, response = llm_generate(
                image=resp.content,
                prompt="I need to train an AI model to segment lines properly on geometry questions. Here is a question, give me 10 text prompts that refer to lines in an image so I can label them for my training data.",
            )

        descriptors = response.split("-")
        st.text_input(label="Label", value=descriptors)
        placeholder = st.text(f"Data {image_url}")
        components.html(manager.labeler.replace("{image_url}", image_url), height=1000)

elif DATA_MENU:
    st.table(
        [{"user": k, "n_labelled": len(v)} for k, v in manager.registeration.items()]
    )
