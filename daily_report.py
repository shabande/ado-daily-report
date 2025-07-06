import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- بياناتك من GitHub Secrets ---
ADO_ORG = os.environ["ADO_ORG"]
PAT = os.environ["ADO_PAT"]
ADO_CHANGED_BY = os.environ["ADO_CHANGED_BY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

AUTH = HTTPBasicAuth("", PAT)
HEADERS = {"Content-Type": "application/json"}
BASE_URL = f"https://dev.azure.com/{ADO_ORG}"

today = datetime.now().strftime("%Y-%m-%d")
final_tasks = []

# باقي السكربت كما هو (نفس الكود السابق)
...
