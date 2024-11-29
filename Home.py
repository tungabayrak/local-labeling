import requests
import streamlit as st
from tools import llm_generate
import json
from manager import manager
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Shark Label", page_icon="🦈", layout="wide")
big_title = st.empty()
big_title.markdown("# 🦈 Shark Label")

current_user_email = st.session_state.get("current_user_email")
logged_in = current_user_email != None

ADMIN_EMAILS = [
    "pyaesonemyo",
    "tungabayrak",
    "moazzam",
    "thomas",
    "alper",
    "tolga",
]

login_box = st.empty()
login_sidebar = st.sidebar.empty()
login_sidebar.header("Login to Continue")

with login_box.form(key="login_form"):
    st.markdown("Authenticate with Google")
    email = st.text_input("Email")
    submit_button = st.form_submit_button(label="Login")

    if submit_button and email and password:
        current_user = {"email": email, "": {}}
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

    if st.button("Go Back", icon="⬅️"):
        prev = manager.load_previous_image(st.session_state["current_user_email"])
        if not prev:
            st.warning("Unable to go back")
        else:
            st.session_state["loaded_image"] = prev["url"]

    if st.button("Label", icon="➡️"):
        st.session_state["loaded_image"] = manager.load_image(
            st.session_state["current_user_email"]
        )["url"]
        st.session_state["set_descriptors"] = False

    if st.session_state.get("set_descriptors") == None:
        st.session_state["set_descriptors"] = False

    if loaded_image := st.session_state.get("loaded_image"):
        if isinstance(loaded_image, bytes):
            image = loaded_image
            image_url = f"data:image/png;base64,{base64.b64encode(loaded_image).decode('utf-8')}"
        else:
            with st.spinner("Downloading image"):
                resp = requests.get(loaded_image)
            image = resp.content
            image_url = loaded_image

        def clean_descriptor(t: str):
            return t.replace('"', "")[2:].strip()

        if not st.session_state["set_descriptors"]:
            with st.spinner("Generaing a.i. descriptors"):
                _, response = llm_generate(
                    image=image,
                    prompt="I need to train an AI model to segment lines properly on geometry questions. Here is a question, give me 10 text prompts that refer to lines in an image so I can label them for my training data.",
                )
            st.session_state["descriptors"] = [
                clean_descriptor(d) for d in response.split("\n") if d
            ][
                1:
            ]  # skip the first preface
            st.session_state["set_descriptors"] = True

        st.markdown("**Please scroll down to see all the descriptors**")
        descriptors = st.session_state["descriptors"]
        for i in range(len(descriptors)):
            descriptors[i] = st.text_input(
                label=f"Label {i}/{(len(descriptors))}", value=descriptors[i]
            )
            components.html(
                manager.labeler_html.replace("{image_url}", image_url).replace(
                    "{label}", descriptors[i]
                ),
                height=500,
            )

elif DATA_MENU:
    st.table(
        [{"user": k, "n_labelled": len(v)} for k, v in manager.registeration.items()]
    )

    with open("viewer.html", "r") as fp:
        manager.viewer_html = fp.read()
    for w in manager.work:
        components.html(
            manager.viewer_html.replace("{json_data}", json.dumps(w)),
            height=300,
            scrolling=True,
        )
