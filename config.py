from dotenv import load_dotenv
import os

load_dotenv()

ROUTER_URL = os.getenv("ROUTER_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")