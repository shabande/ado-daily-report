
import os
import requests
from datetime import datetime

ADO_PAT = os.getenv("ADO_PAT")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([ADO_PAT, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    raise Exception("Missing required environment variables")

ORG = "sahl-solution"
AUTH = ("", ADO_PAT)
HEADERS = {"Content-Type": "application/json"}

today = datetime.now().date().isoformat()
url = f"https://dev.azure.com/{ORG}/_apis/wit/wiql?api-version=6.0"

query = {
    "query": f'''
    SELECT [System.Id], [System.Title], [System.State], [System.ChangedDate], [System.TeamProject]
    FROM WorkItems
    WHERE
        [System.ChangedDate] >= '{today}T00:00:00.0000000Z'
        AND [System.ChangedDate] <= '{today}T23:59:59.0000000Z'
        AND [System.ChangedBy] CONTAINS 'shaaban'
    ORDER BY [System.ChangedDate] DESC
    '''
}

res = requests.post(url, auth=AUTH, headers=HEADERS, json=query)
res.raise_for_status()
work_items = res.json().get("workItems", [])

result_lines = []

if not work_items:
    result_lines.append(f"ℹ️ لا توجد تاسكات انت عدلت حالتها النهاردة ({today}).")
else:
    ids = [str(item["id"]) for item in work_items]
    ids_url = f"https://dev.azure.com/{ORG}/_apis/wit/workitemsbatch?api-version=6.0"
    body = {
        "ids": ids,
        "fields": ["System.Id", "System.Title", "System.TeamProject"]
    }
    details = requests.post(ids_url, auth=AUTH, headers=HEADERS, json=body).json()
    for item in details["value"]:
        task_id = item["fields"]["System.Id"]
        title = item["fields"]["System.Title"]
        project = item["fields"]["System.TeamProject"]
        result_lines.append(f"✅#{task_id} | {title} | {project}")

message = "\n".join(result_lines)
send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
send_data = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message
}
requests.post(send_url, data=send_data)
