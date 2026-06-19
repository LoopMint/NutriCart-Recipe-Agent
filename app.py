import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
#  CONFIGURATION
# ============================================================

load_dotenv()  # Load .env if present

DATA_FILE = os.getenv("SAAS_DATA_FILE", "saas_data.json")
LOG_LEVEL = os.getenv("SAAS_LOG_LEVEL", "INFO").upper()

# ============================================================
#  LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("SaaSApp")


# ============================================================
#  DEFAULT DATA MODEL
# ============================================================

@dataclass
class SaaSData:
    recipes: list
    categories: list
    favorites: list
    tasks: list
    social_posts: list
    properties: list
    appointments: list

    @staticmethod
    def default():
        return SaaSData(
            recipes=[],
            categories=[
                "Breakfast", "Lunch", "Dinner",
                "Dessert", "Snacks", "Meal Prep"
            ],
            favorites=[],
            tasks=[],
            social_posts=[],
            properties=[],
            appointments=[]
        )


# ============================================================
#  STORAGE SERVICE
# ============================================================

class StorageService:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        logger.info(f"Storage initialized at {self.file_path}")

    def load(self) -> SaaSData:
        """Load JSON data from disk with safe fallback."""
        if not self.file_path.exists():
            logger.warning("Data file not found. Using default dataset.")
            return SaaSData.default()

        try:
            with open(self.file_path, "r") as f:
                raw = json.load(f)
                logger.info("Data loaded successfully.")
                return SaaSData(**raw)
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return SaaSData.default()

    def save(self, data: SaaSData):
        """Persist data to disk safely."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(asdict(data), f, indent=2)
            logger.info("Data saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")


# ============================================================
#  APPLICATION CORE
# ============================================================

class SaaSApp:
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.state = storage.load()

    # -----------------------------
    # Example CRUD operations
    # -----------------------------

    def add_recipe(self, name: str):
        if not name:
            logger.error("Recipe name cannot be empty.")
            return False

        self.state.recipes.append(name)
        logger.info(f"Recipe added: {name}")
        self.storage.save(self.state)
        return True

    def add_task(self, task: str):
        if not task:
            logger.error("Task cannot be empty.")
            return False

        self.state.tasks.append(task)
        logger.info(f"Task added: {task}")
        self.storage.save(self.state)
        return True

    def list_all(self) -> Dict[str, Any]:
        """Return all data in a clean structure."""
        return asdict(self.state)


# ============================================================
#  MAIN ENTRYPOINT
# ============================================================

def main():
    logger.info("Starting SaaS Application...")

    storage = StorageService(DATA_FILE)
    app = SaaSApp(storage)

    # Example usage (replace with API, CLI, or UI layer)
    app.add_recipe("Sample Recipe")
    app.add_task("Sample Task")

    logger.info("Current State:")
    logger.info(json.dumps(app.list_all(), indent=2))


if __name__ == "__main__":
    main()
