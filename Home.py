import requests
import streamlit as st
import base64
import json
import os

from tools import llm_generate
from manager import manager
import streamlit.components.v1 as components

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
    st.markdown("Authenticate with trusted name")
    email = st.text_input("Username")
    submit_button = st.form_submit_button(label="Login")

    if submit_button and email:
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
APP_MENU = "🚩 App"
DATA_MENU = "📅 Data"
selected_menu = st.sidebar.radio("Menus", [APP_MENU, DATA_MENU])

if st.sidebar.button("Logout"):
    st.session_state["current_user_email"] = None
    st.rerun()

if selected_menu == APP_MENU:
    st.markdown("Images waiting to be labelled.")
    st.table([{"category": k, "size": len(v)} for k, v in manager.data.items()])

    # if st.button("Go Back", icon="⬅️"):
    #     prev = manager.load_previous_image(st.session_state["current_user_email"])
    #     if not prev:
    #         st.warning("Unable to go back")
    #     else:
    #         st.session_state["loaded_image"] = prev["url"]

    category = st.selectbox("Categories", list(manager.data.keys()))
    save = st.checkbox("Save", value=True)
    if st.button("Label", icon="➡️"):
        st.session_state["loaded_image"] = manager.load_image(
            category, st.session_state["current_user_email"], save=save
        )
        st.session_state["set_descriptors"] = False

    if st.session_state.get("set_descriptors") == None:
        st.session_state["set_descriptors"] = False

    if loaded_image := st.session_state.get("loaded_image"):
        if isinstance(loaded_image["url"], bytes):
            image = loaded_image["url"]
            image_url = f"data:image/png;base64,{base64.b64encode(loaded_image['url']).decode('utf-8')}"
        else:
            with st.spinner("Downloading image"):
                resp = requests.get(loaded_image["url"])
            image = resp.content
            image_url = loaded_image["url"]

        def clean_descriptor(t: str):
            return t.replace('"', "")[2:].strip()

        if not st.session_state["set_descriptors"]:
            with st.spinner("Generaing a.i. descriptors"):
                print(loaded_image["id"], list(manager.descriptions.keys()))
                extra_desc = manager.descriptions.get(
                    loaded_image["id"].replace(".png", ""), ""
                )
                if extra_desc:
                    extra_desc = (
                        f"\nHere is a helpful annotation of the image: {extra_desc}"
                    )
                _, response = llm_generate(
                    image=image,
                    prompt="I need to train an AI model to segment lines properly on geometry questions. Here is a question, give me 10 text prompts that refer to lines in an image so I can label them for my training data. {}",
                )

            st.session_state["descriptors"] = {
                "lines": [clean_descriptor(d) for d in response.split("\n") if d][1:],
                "extra": extra_desc,
            }
            st.session_state["set_descriptors"] = True

        st.markdown(
            f"**Image Description**: {st.session_state['descriptors']['extra']}"
        )
        st.markdown("**Please scroll down to see all the descriptors**")
        descriptors = st.session_state["descriptors"]["lines"]
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
