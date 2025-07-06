import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- بيانات من GitHub Secrets ---
ADO_ORG = os.environ["ADO_ORG"]
ADO_PAT = os.environ["ADO_PAT"]
ADO_CHANGED_BY = os.environ["ADO_CHANGED_BY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

AUTH = HTTPBasicAuth("", ADO_PAT)
HEADERS = {"Content-Type": "application/json"}
BASE_URL = f"https://dev.azure.com/{ADO_ORG}"
today = datetime.now().strftime("%Y-%m-%d")

raw_tasks = []

# --- Step 1: Get All Projects ---
projects_url = f"{BASE_URL}/_apis/projects?api-version=6.0"
projects_res = requests.get(projects_url, auth=AUTH).json()
projects = [p["name"] for p in projects_res.get("value", [])]

# --- Step 2: Loop through projects and fetch changed tasks ---
for project in projects:
    wiql_query = {
        "query": f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.ChangedDate] >= '{today}T00:00:00Z'
        AND [System.ChangedBy] = '{ADO_CHANGED_BY}'
        AND ([System.State] = 'Done' OR [System.State] = 'Rejected' OR [System.State] = 'Resolved')
        """
    }

    wiql_url = f"{BASE_URL}/{project}/_apis/wit/wiql?api-version=6.0"
    wiql_res = requests.post(wiql_url, json=wiql_query, auth=AUTH, headers=HEADERS).json()
    ids = [item["id"] for item in wiql_res.get("workItems", [])]

    for wid in ids:
        workitem_url = f"{BASE_URL}/_apis/wit/workitems/{wid}?api-version=6.0"
        wi = requests.get(workitem_url, auth=AUTH).json()
        title = wi["fields"].get("System.Title", "")
        actual_project = wi["fields"].get("System.TeamProject", "")
        raw_tasks.append((wid, title, actual_project))

# --- Step 3: Remove Duplicates (by task ID) ---
seen_ids = set()
unique_tasks = []
for tid, title, project in raw_tasks:
    if tid not in seen_ids:
        seen_ids.add(tid)
        unique_tasks.append(f"✅#{tid} | {title} | {project}")

# --- Step 4: Send Telegram Message ---
if unique_tasks:
    message = "\n".join(unique_tasks)
else:
    message = f"ℹ️ لا توجد تاسكات انت عدلت حالتها النهاردة ({today})."

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
requests.post(telegram_url, json={
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
})
