from dotenv import load_dotenv
import os

load_dotenv()

ROUTER_URL = os.getenv("ROUTER_URL")
USERNAME = "root"
PASSWORD = os.getenv("PASSWORD")

COLLECTOR_ENABLED = os.getenv("COLLECTOR_ENABLED", "True") == "True"
COLLECTOR_INTERVAL_MINUTES = int(os.getenv("COLLECTOR_INTERVAL_MINUTES", 2))