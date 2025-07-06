import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- GitHub Secrets ---
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

# Step 1: Get All Projects
projects_url = f"{BASE_URL}/_apis/projects?api-version=6.0"
projects_res = requests.get(projects_url, auth=AUTH)
projects_data = projects_res.json()
projects = [p["name"] for p in projects_data.get("value", [])]

# Step 2: Fetch changed work items per project
for project in projects:
    wiql_query = {
        "query": f"""
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.ChangedDate] >= '{today}T00:00:00Z'
AND [System.ChangedBy] = '{ADO_CHANGED_BY}'
"""
    }

    wiql_url = f"{BASE_URL}/{project}/_apis/wit/wiql?api-version=6.0"
    res = requests.post(wiql_url, json=wiql_query, auth=AUTH, headers=HEADERS)
    res.raise_for_status()
    data = res.json()
    ids = [item["id"] for item in data.get("workItems", [])]

    for wid in ids:
        workitem_url = f"{BASE_URL}/_apis/wit/workitems/{wid}?api-version=6.0"
        wi = requests.get(workitem_url, auth=AUTH).json()
        title = wi["fields"].get("System.Title", "")
        raw_tasks.append((wid, title, project))

# Step 3: Format unique tasks
seen = set()
unique_tasks = []
for task in raw_tasks:
    tid, title, project = task
    if tid not in seen:
        seen.add(tid)
        unique_tasks.append(f"✅#{tid} | {title} | {project}")

# Step 4: Send Telegram Message
if unique_tasks:
    message = "\n".join(unique_tasks)
else:
    message = f"ℹ️ لا توجد تاسكات انت عدلتها النهاردة ({today})."

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
requests.post(telegram_url, json={
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
})
