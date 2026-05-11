import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

ADO_ORG = os.environ["ADO_ORG"]
ADO_PAT = os.environ["ADO_PAT"]
ADO_CHANGED_BY = os.environ["ADO_CHANGED_BY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

AUTH = HTTPBasicAuth("", ADO_PAT)
HEADERS = {"Content-Type": "application/json"}
BASE_URL = f"https://dev.azure.com/{ADO_ORG}"
today = datetime.now().strftime("%Y-%m-%d")
TOTAL_HOURS = 7

# Step 1: Get All Projects
projects_res = requests.get(f"{BASE_URL}/_apis/projects?api-version=6.0", auth=AUTH)
projects = [p["name"] for p in projects_res.json().get("value", [])]

# Step 2: Fetch changed work items per project
raw_tasks = {}

for project in projects:
    wiql_query = {
        "query": f"""
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItems
WHERE [System.ChangedDate] >= '{today}T00:00:00Z'
AND [System.ChangedBy] = '{ADO_CHANGED_BY}'
ORDER BY [System.ChangedDate] DESC
"""
    }
    res = requests.post(
        f"{BASE_URL}/{project}/_apis/wit/wiql?api-version=6.0",
        json=wiql_query, auth=AUTH, headers=HEADERS
    )
    if not res.ok:
        continue

    ids = [item["id"] for item in res.json().get("workItems", [])]
    if not ids:
        continue

    ids_str = ",".join(str(i) for i in ids)
    fields = "System.Id,System.Title,System.TeamProject,System.WorkItemType"
    batch_res = requests.get(
        f"{BASE_URL}/_apis/wit/workitems?ids={ids_str}&fields={fields}&api-version=6.0",
        auth=AUTH
    )
    if not batch_res.ok:
        continue

    for wi in batch_res.json().get("value", []):
        wid = wi["id"]
        if wid not in raw_tasks:
            raw_tasks[wid] = {
                "title": wi["fields"].get("System.Title", ""),
                "project": wi["fields"].get("System.TeamProject", project),
                "type": wi["fields"].get("System.WorkItemType", "Task"),
            }

# Step 3: Group by project
grouped = {}
for wid, info in raw_tasks.items():
    proj = info["project"]
    if proj not in grouped:
        grouped[proj] = []
    grouped[proj].append((wid, info["title"], info["type"]))

# Step 4: Calculate time per task
total_tasks = sum(len(t) for t in grouped.values())
if total_tasks > 0:
    time_each = round(TOTAL_HOURS / total_tasks, 1)
    # Fix rounding so total = exactly 7h
    times = [time_each] * total_tasks
    diff = round(TOTAL_HOURS - sum(times), 1)
    if diff != 0:
        times[0] = round(times[0] + diff, 1)
else:
    times = []

# Step 5: Build message
if grouped:
    lines = [f"📋 Daily Report — {today}\n"]
    task_index = 0
    for proj, tasks in grouped.items():
        lines.append(f"Project: {proj}")
        for wid, title, wtype in tasks:
            hours = times[task_index]
            task_index += 1
            lines.append(f"Azure Task ID: {wid}")
            lines.append(f"Task: {title}")
            lines.append(f"Time: {hours}h")
            lines.append("")
    lines.append(f"⏱ Total: {TOTAL_HOURS}h")
    message = "\n".join(lines)
else:
    message = f"ℹ️ لا توجد تاسكات النهارده ({today})."

# Step 6: Send to Telegram
requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
    json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
)
