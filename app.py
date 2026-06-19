import json
import os
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
import streamlit as st

# ============================================================
#  CONFIG & DATA
# ============================================================

DATA_FILE = "saas_data.json"

DEFAULT_DATA = {
    "recipes": [],          # list of {title, url, source}
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


def load_data() -> Dict:
    """Load data from JSON file or return defaults."""
    path = Path(DATA_FILE)
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DATA.copy()


def save_data():
    """Persist current session_state to JSON file."""
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


# ============================================================
#  SCRAPING LOGIC
# ============================================================

def scrape_recipes_from_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Scrape recipe links from a search engine results page (DuckDuckGo HTML).
    This is a lightweight, best-effort scraper.
    """
    if not query:
        return []

    search_query = query + " recipe"
    url = "https://duckduckgo.com/html/"
    params = {"q": search_query}

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NutriCartBot/1.0; +https://example.com/bot)"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    # DuckDuckGo HTML results links often have class "result__a"
    for a in soup.find_all("a", class_="result__a"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue

        results.append(
            {
                "title": title,
                "url": href,
                "source": "DuckDuckGo"
            }
        )
        if len(results) >= max_results:
            break

    return results


# ============================================================
#  INITIALIZE SESSION STATE
# ============================================================

data = load_data()
for key, value in data.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "scraped_recipes" not in st.session_state:
    st.session_state.scraped_recipes = []


# ============================================================
#  UI SECTIONS
# ============================================================

def page_recipes():
    st.header("🍽 NutriCart Recipes")

    st.subheader("Saved Recipes")
    if st.session_state.recipes:
        for i, r in enumerate(st.session_state.recipes, start=1):
            st.markdown(f"**{i}. {r.get('title', 'Untitled')}**")
            st.write(r.get("url", ""))
            st.caption(f"Source: {r.get('source', 'Unknown')}")
            st.markdown("---")
    else:
        st.info("No recipes saved yet.")

    st.subheader("Add Recipe Manually")
    with st.form("add_recipe_form"):
        title = st.text_input("Recipe title")
        url = st.text_input("Recipe URL")
        submitted = st.form_submit_button("Add Recipe")
        if submitted:
            if title:
                st.session_state.recipes.append(
                    {"title": title, "url": url, "source": "Manual"}
                )
                save_data()
                st.success("Recipe added.")
            else:
                st.error("Title is required.")

    st.subheader("Search & Scrape Recipes from Web")
    query = st.text_input("Search term (e.g. 'chicken salad', 'vegan pasta')")
    max_results = st.slider("Max results", 1, 10, 5)

    if st.button("Search & Scrape"):
        with st.spinner("Searching and scraping recipes..."):
            scraped = scrape_recipes_from_search(query, max_results=max_results)
        st.session_state.scraped_recipes = scraped

        if not scraped:
            st.warning("No recipes found or scraping failed.")
        else:
            st.success(f"Found {len(scraped)} recipes.")

    if st.session_state.scraped_recipes:
        st.subheader("Scraped Recipes")
        selected_indices = []
        for idx, r in enumerate(st.session_state.scraped_recipes):
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                selected = st.checkbox("", key=f"scraped_{idx}")
            with col2:
                st.markdown(f"**{r['title']}**")
                st.write(r["url"])
                st.caption(f"Source: {r['source']}")
            if selected:
                selected_indices.append(idx)

        if st.button("Save Selected to Bucket"):
            if not selected_indices:
                st.warning("No recipes selected.")
            else:
                for idx in selected_indices:
                    st.session_state.recipes.append(st.session_state.scraped_recipes[idx])
                save_data()
                st.success(f"Saved {len(selected_indices)} recipes to bucket.")


def page_tasks():
    st.header("✅ Tasks")
    st.subheader("Current Tasks")
    if st.session_state.tasks:
        for i, t in enumerate(st.session_state.tasks, start=1):
            st.write(f"{i}. {t}")
    else:
        st.info("No tasks yet.")

    new_task = st.text_input("New task")
    if st.button("Add Task"):
        if new_task:
            st.session_state.tasks.append(new_task)
            save_data()
            st.success("Task added.")
        else:
            st.error("Task cannot be empty.")


def page_social():
    st.header("📣 Social Posts Planner")
    st.subheader("Planned Posts")
    if st.session_state.social_posts:
        for i, p in enumerate(st.session_state.social_posts, start=1):
            st.write(f"{i}. {p}")
    else:
        st.info("No social posts yet.")

    new_post = st.text_area("New social post idea")
    if st.button("Add Social Post"):
        if new_post:
            st.session_state.social_posts.append(new_post)
            save_data()
            st.success("Social post added.")
        else:
            st.error("Post cannot be empty.")


def page_properties():
    st.header("🏠 Properties")
    st.subheader("Tracked Properties")
    if st.session_state.properties:
        for i, p in enumerate(st.session_state.properties, start=1):
            st.write(f"{i}. {p}")
    else:
        st.info("No properties yet.")

    new_prop = st.text_input("New property")
    if st.button("Add Property"):
        if new_prop:
            st.session_state.properties.append(new_prop)
            save_data()
            st.success("Property added.")
        else:
            st.error("Property cannot be empty.")


def page_appointments():
    st.header("📅 Appointments")
    st.subheader("Upcoming Appointments")
    if st.session_state.appointments:
        for i, a in enumerate(st.session_state.appointments, start=1):
            st.write(f"{i}. {a}")
    else:
        st.info("No appointments yet.")

    new_appt = st.text_input("New appointment")
    if st.button("Add Appointment"):
        if new_appt:
            st.session_state.appointments.append(new_appt)
            save_data()
            st.success("Appointment added.")
        else:
            st.error("Appointment cannot be empty.")


def page_debug():
    st.header("🛠 Data Debug")
    st.write("Raw session_state data:")
    st.json(
        {
            "recipes": st.session_state.recipes,
            "categories": st.session_state.categories,
            "favorites": st.session_state.favorites,
            "tasks": st.session_state.tasks,
            "social_posts": st.session_state.social_posts,
            "properties": st.session_state.properties,
            "appointments": st.session_state.appointments,
        }
    )
    if st.button("Force Save to Disk"):
        save_data()
        st.success("Data saved to JSON file.")


# ============================================================
#  MAIN APP
# ============================================================

def main():
    st.set_page_config(page_title="NutriCart", page_icon="🥗", layout="wide")

    st.sidebar.title("NutriCart Navigation")
    page = st.sidebar.radio(
        "Go to",
        [
            "Recipes",
            "Tasks",
            "Social Planner",
            "Properties",
            "Appointments",
            "Data Debug",
        ],
    )

    if page == "Recipes":
        page_recipes()
    elif page == "Tasks":
        page_tasks()
    elif page == "Social Planner":
        page_social()
    elif page == "Properties":
        page_properties()
    elif page == "Appointments":
        page_appointments()
    elif page == "Data Debug":
        page_debug()


if __name__ == "__main__":
    main()
