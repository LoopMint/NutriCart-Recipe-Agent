import json
import os
import streamlit as st

DATA_FILE = "saas_data.json"

DEFAULT_DATA = {
    "recipes": [],
    "categories": [
        "Breakfast",
        "Lunch",
        "Dinner",
        "Dessert",
        "Snacks",
        "Meal Prep"
    ],
    "favorites": [],
    "tasks": [],
    "social_posts": [],
    "properties": [],
    "appointments": []
}

# -----------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DATA.copy()

# -----------------------------------------------------------
# SAVE DATA
# -----------------------------------------------------------
def save_data():
    data = {
        "recipes": st.session_state.recipes,
        "categories": st.session_state.categories,
        "favorites": st.session_state.favorites,
        "tasks": st.session_state.tasks,
        "social_posts": st.session_state.social_posts,
        "properties": st.session_state.properties,
        "appointments": st.session_state.appointments
    }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------------------------------------
# INITIALIZE SESSION STATE
# -----------------------------------------------------------
data = load_data()

for key, value in data.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------------------------------------
# SIMPLE UI TO SHOW DATA IS LOADED
# -----------------------------------------------------------
st.title("Data Loader Test")

st.subheader("Recipes")
st.write(st.session_state.recipes)

st.subheader("Categories")
st.write(st.session_state.categories)

st.subheader("Tasks")
st.write(st.session_state.tasks)

st.subheader("Social Posts")
st.write(st.session_state.social_posts)

st.subheader("Properties")
st.write(st.session_state.properties)

st.subheader("Appointments")
st.write(st.session_state.appointments)

# Button to test saving
if st.button("Save Data"):
    save_data()
    st.success("Data saved!")
