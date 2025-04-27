from dotenv import load_dotenv
import os

load_dotenv()

ROUTER_URL = os.getenv("ROUTER_URL")
USERNAME = "root"
PASSWORD = os.getenv("PASSWORD")