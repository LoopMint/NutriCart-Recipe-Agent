import json, os

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

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_DATA.copy()

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

data = load_data()

for k, v in data.items():
    if k not in st.session_state:
        st.session_state[k] = v
