import json
import os
from pathlib import Path
from typing import List, Dict, Any
import uuid

import requests
from bs4 import BeautifulSoup
import streamlit as st

# ============================================================
# CONFIG & DATA
# ============================================================

DATA_FILE = "health_wellness_recipes.json"

DEFAULT_DATA = {
    "recipes": []  # list of {id, title, url, calories_total, servings, calories_per_serving, ingredients, steps}
}


def load_data() -> Dict[str, Any]:
    path = Path(DATA_FILE)
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DATA.copy()


def save_data():
    data = {
        "recipes": st.session_state.recipes
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================
# SCRAPING LOGIC
# ============================================================

def scrape_recipe_from_url(url: str) -> Dict[str, Any]:
    """
    Best-effort recipe scraper from a URL.
    Tries to extract title, ingredients, and steps using common patterns.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HealthWellnessApp/1.0)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title
    title = soup.find("h1")
    if title:
        title = title.get_text(strip=True)
    else:
        title = soup.title.get_text(strip=True) if soup.title else "Untitled Recipe"

    # Ingredients
    ingredients = []

    # Common pattern: itemprop="recipeIngredient"
    for tag in soup.find_all(attrs={"itemprop": "recipeIngredient"}):
        text = tag.get_text(" ", strip=True)
        if text:
            ingredients.append(text)

    # Fallback: look for elements with "ingredient" in class name
    if not ingredients:
        for tag in soup.find_all(True, class_=lambda c: c and "ingredient" in " ".join(c).lower()):
            text = tag.get_text(" ", strip=True)
            if text and len(text) < 200:
                ingredients.append(text)

    # Deduplicate
    ingredients = list(dict.fromkeys(ingredients))

    # Steps / Instructions
    steps = []

    # Common pattern: itemprop="recipeInstructions"
    for tag in soup.find_all(attrs={"itemprop": "recipeInstructions"}):
        # Some sites wrap each step in <li>, others in <p>
        sub_steps = tag.find_all(["li", "p"])
        if sub_steps:
            for s in sub_steps:
                text = s.get_text(" ", strip=True)
                if text:
                    steps.append(text)
        else:
            text = tag.get_text(" ", strip=True)
            if text:
                steps.append(text)

    # Fallback: look for elements with "instruction" or "direction" in class name
    if not steps:
        for tag in soup.find_all(True, class_=lambda c: c and any(
                kw in " ".join(c).lower() for kw in ["instruction", "direction", "method"])):
            sub_steps = tag.find_all(["li", "p"])
            if sub_steps:
                for s in sub_steps:
                    text = s.get_text(" ", strip=True)
                    if text:
                        steps.append(text)
            else:
                text = tag.get_text(" ", strip=True)
                if text:
                    steps.append(text)

    # Deduplicate
    steps = list(dict.fromkeys(steps))

    return {
        "title": title,
        "ingredients": ingredients,
        "steps": steps
    }


# ============================================================
# SESSION STATE INIT
# ============================================================

data = load_data()
if "recipes" not in st.session_state:
    st.session_state.recipes = data.get("recipes", [])


# ============================================================
# HELPERS
# ============================================================

def add_recipe(recipe: Dict[str, Any]):
    st.session_state.recipes.append(recipe)
    save_data()


def delete_recipe(recipe_id: str):
    st.session_state.recipes = [r for r in st.session_state.recipes if r["id"] != recipe_id]
    save_data()


def calculate_calories_per_serving(calories_total: float, servings: float) -> float:
    if servings <= 0:
        return 0.0
    return round(calories_total / servings, 2)


# ============================================================
# PAGES
# ============================================================

def page_dashboard():
    st.title("🏥 Health & Wellness Dashboard")

    total_recipes = len(st.session_state.recipes)
    total_calories = sum(r.get("calories_total", 0) for r in st.session_state.recipes if r.get("calories_total"))
    total_servings = sum(r.get("servings", 0) for r in st.session_state.recipes if r.get("servings"))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saved Recipes", total_recipes)
    with col2:
        st.metric("Total Calories (all recipes)", int(total_calories))
    with col3:
        st.metric("Total Servings (all recipes)", int(total_servings))

    st.markdown("---")
    st.subheader("Recent Recipes")
    if st.session_state.recipes:
        for r in st.session_state.recipes[-5:][::-1]:
            st.markdown(f"**{r['title']}**")
            st.caption(r.get("url", ""))
            cals = r.get("calories_per_serving")
            if cals:
                st.write(f"Calories per serving: {cals}")
            st.markdown("---")
    else:
        st.info("No recipes saved yet. Go to 'Recipes' to add some.")


def page_calorie_calculator():
    st.title("🔥 Calorie Calculator")

    st.write("Use this to quickly calculate calories per serving for any meal or recipe.")

    with st.form("calorie_calc_form"):
        calories_total = st.number_input("Total calories for the dish", min_value=0.0, step=10.0)
        servings = st.number_input("Number of servings", min_value=1.0, step=1.0)
        submitted = st.form_submit_button("Calculate")

    if submitted:
        cps = calculate_calories_per_serving(calories_total, servings)
        st.success(f"Calories per serving: **{cps} kcal**")


def page_recipes():
    st.title("🍽 Recipes Manager")

    st.subheader("1. Import Recipe from URL (Web Scrape)")
    url = st.text_input("Recipe URL")
    if st.button("Scrape Recipe"):
        if not url:
            st.error("Please enter a URL.")
        else:
            with st.spinner("Scraping recipe..."):
                scraped = scrape_recipe_from_url(url)
            if not scraped:
                st.error("Could not extract recipe from this URL.")
            else:
                st.success("Recipe scraped. You can review and edit below.")
                st.session_state["scraped_recipe"] = {
                    "id": str(uuid.uuid4()),
                    "url": url,
                    "title": scraped.get("title", "Untitled Recipe"),
                    "ingredients": scraped.get("ingredients", []),
                    "steps": scraped.get("steps", []),
                    "calories_total": 0.0,
                    "servings": 1.0,
                    "calories_per_serving": 0.0
                }

    if "scraped_recipe" in st.session_state:
        st.markdown("### Scraped Recipe (Review & Edit)")
        r = st.session_state["scraped_recipe"]

        r["title"] = st.text_input("Title", value=r["title"])
        r["url"] = st.text_input("URL", value=r["url"])

        st.markdown("**Ingredients (one per line)**")
        ingredients_text = st.text_area(
            "Ingredients",
            value="\n".join(r.get("ingredients", [])),
            height=150
        )
        r["ingredients"] = [line.strip() for line in ingredients_text.splitlines() if line.strip()]

        st.markdown("**Preparation Steps (one per line)**")
        steps_text = st.text_area(
            "Steps",
            value="\n".join(r.get("steps", [])),
            height=200
        )
        r["steps"] = [line.strip() for line in steps_text.splitlines() if line.strip()]

        col1, col2, col3 = st.columns(3)
        with col1:
            r["calories_total"] = st.number_input(
                "Total Calories",
                min_value=0.0,
                value=float(r.get("calories_total", 0.0)),
                step=10.0
            )
        with col2:
            r["servings"] = st.number_input(
                "Servings",
                min_value=1.0,
                value=float(r.get("servings", 1.0)),
                step=1.0
            )
        with col3:
            r["calories_per_serving"] = calculate_calories_per_serving(
                r["calories_total"], r["servings"]
            )
            st.metric("Calories / Serving", r["calories_per_serving"])

        if st.button("Save Recipe to Library"):
            add_recipe(r)
            del st.session_state["scraped_recipe"]
            st.success("Recipe saved to your library.")

    st.markdown("---")
    st.subheader("2. Saved Recipes Library")

    if not st.session_state.recipes:
        st.info("No recipes saved yet.")
        return

    for recipe in st.session_state.recipes:
        with st.expander(recipe["title"], expanded=False):
            st.write(f"**URL:** {recipe.get('url', '')}")
            if recipe.get("calories_per_serving"):
                st.write(f"**Calories per serving:** {recipe['calories_per_serving']} kcal")
            st.write(f"**Total calories:** {recipe.get('calories_total', 0)}")
            st.write(f"**Servings:** {recipe.get('servings', 1)}")

            st.markdown("**Ingredients:**")
            if recipe.get("ingredients"):
                for ing in recipe["ingredients"]:
                    st.write(f"- {ing}")
            else:
                st.write("_No ingredients stored._")

            st.markdown("**Steps:**")
            if recipe.get("steps"):
                for i, step in enumerate(recipe["steps"], start=1):
                    st.write(f"{i}. {step}")
            else:
                st.write("_No steps stored._")

            if st.button("Delete Recipe", key=f"del_{recipe['id']}"):
                delete_recipe(recipe["id"])
                st.warning("Recipe deleted.")
                st.experimental_rerun()


def page_data_debug():
    st.title("🛠 Data Debug")
    st.json({"recipes": st.session_state.recipes})
    if st.button("Force Save to Disk"):
        save_data()
        st.success("Data saved.")


# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title="Health & Wellness Recipes", page_icon="🥗", layout="wide")

    st.sidebar.title("Health & Wellness App")
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Calorie Calculator", "Recipes", "Data Debug"]
    )

    if page == "Dashboard":
        page_dashboard()
    elif page == "Calorie Calculator":
        page_calorie_calculator()
    elif page == "Recipes":
        page_recipes()
    elif page == "Data Debug":
        page_data_debug()


if __name__ == "__main__":
    main()
