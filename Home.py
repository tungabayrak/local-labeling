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

USERS = [
    "tomas",
    "tunga",
    "ricky", 
    "Alper",
    "Moazzam",
    "tolga"
]

current_user_email = st.session_state.get("current_user_email")
logged_in = current_user_email != None

user_select_container = st.empty()
login_sidebar = st.sidebar.empty()
login_sidebar.header("Select User")

if not logged_in:
    with user_select_container.container():
        selected_user = st.selectbox("Select your name", USERS)
        if st.button("Continue"):
            st.session_state["current_user_email"] = selected_user
            logged_in = True
            st.rerun()

if logged_in:
    user_select_container.empty()
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

    category = st.selectbox("Categories", list(manager.data.keys()))
    
    default_prompt = """
    I am doing a labeling -  referring expression comprehension task for SAT Math Exam images. 
    I need you to give me 5-10 labeling tasks for spesific elements, points, objects and regions that are important information from the image. 
    Take the image description as the main source of information.
    The only tool I can use for labeling for are: Pencil, Line, Bounding box. So give me the task accordingly with my tools that I can mask things.
    """
    if "custom_prompt" not in st.session_state:
        st.session_state["custom_prompt"] = default_prompt
        
    st.markdown("### LLM Prompt Settings")
    st.session_state["custom_prompt"] = st.text_area(
        "Edit AI Prompt", 
        value=st.session_state["custom_prompt"],
        help="Customize the prompt that will be sent to the AI when analyzing images"
    )
    if st.button("Reset Prompt"):
        st.session_state["custom_prompt"] = default_prompt
        st.rerun()
    
    save = st.checkbox("Save", value=True)
    
    if "data/Tomas SAT pictures" in category:
        preview_container = st.empty()
        if st.button("Preview Next Image"):
            next_image = manager.data[category][-1]  # Get next image without popping it
            image_id = next_image["id"].split('.')[0]  # Remove file extension
            
            try:
                # Try to read the SAT description file
                with open("data/Tomas SAT picture labels.txt", "r") as f:
                    sat_descriptions = f.read()
                
                # Find matching description for this image
                import re
                description_match = re.search(f"^{image_id}: (.*?)$", sat_descriptions, re.MULTILINE)
                if description_match:
                    description = description_match.group(1).strip()
                else:
                    description = "No matching description found for this image ID"
                    st.warning(f"Could not find description for image {image_id}")
                
            except FileNotFoundError:
                st.error("SAT description file not found at: data/Tomas SAT picture labels.txt")
                description = "Description file not found"
            except Exception as e:
                st.error(f"Error reading description: {str(e)}")
                description = "Error reading description"
            
            # Display preview
            with preview_container.container():
                st.markdown("### Preview")
                if isinstance(next_image["url"], bytes):
                    st.image(next_image["url"])
                else:
                    st.image(next_image["url"])
                st.markdown("**Image ID:** " + image_id)
                st.markdown("**Description from SAT data:**")
                st.markdown(description)
                st.markdown("**Prompt to be sent:**")
                st.markdown(st.session_state["custom_prompt"])
    
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
            with st.spinner("Generating a.i. descriptors"):
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
                    prompt=st.session_state["custom_prompt"],
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
        [{"user": k, "n_labelled": len(v)} for k, v in manager.registration.items()]
    )

    with open("viewer.html", "r") as fp:
        manager.viewer_html = fp.read()
    for w in manager.work:
        components.html(
            manager.viewer_html.replace("{json_data}", json.dumps(w)),
            height=300,
            scrolling=True,
        )
