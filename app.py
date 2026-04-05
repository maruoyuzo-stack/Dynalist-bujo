from flask import Flask
import requests
import datetime
import os

app = Flask(__name__)

API_TOKEN = os.environ.get("DYNALIST_TOKEN")
BUJO_FOLDER_NAME = "Bujo"

def log(msg):
    print(msg)

def make_date_str(dt):
    weekdays = ["月","火","水","木","金","土","日"]
    return dt.strftime("%Y/%m/%d") + f"({weekdays[dt.weekday()]})"

def make_month_str(dt):
    return dt.strftime("%Y/%m")

@app.route("/")
def run():
    try:
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)

        today_str = make_date_str(today)
        yesterday_str = make_date_str(yesterday)
        month_str = make_month_str(today)

        log(f"START {today_str}")

        res = requests.post(
            "https://dynalist.io/api/v1/file/list",
            json={"token": API_TOKEN}
        )

        return str(res.json())
        
        files = res.json()["files"]

        bujo = next(f for f in files if f["title"] == BUJO_FOLDER_NAME)

        month_folder = next(
            (f for f in files if f["title"] == month_str and f.get("parent_id") == bujo["id"]),
            None
        )

        if not month_folder:
            res = requests.post(
                "https://dynalist.io/api/v1/file/create",
                json={
                    "token": API_TOKEN,
                    "title": month_str,
                    "parent_id": bujo["id"]
                }
            )
            month_folder = {"id": res.json()["file_id"]}

        for f in files:
            if f["title"] == today_str and f.get("parent_id") == month_folder["id"]:
                return "skip"

        source = next((f for f in files if f["title"] == yesterday_str), None)

        if not source:
            files.sort(key=lambda x: x.get("updated", 0), reverse=True)
            source = files[0]

        res = requests.post(
            "https://dynalist.io/api/v1/doc/read",
            json={"token": API_TOKEN, "file_id": source["id"]}
        )
        nodes = res.json()["nodes"]

        nodes = [n for n in nodes if not n.get("checked", False)]
        for n in nodes:
            n.pop("id", None)

        res = requests.post(
            "https://dynalist.io/api/v1/doc/create",
            json={
                "token": API_TOKEN,
                "title": today_str,
                "parent_id": month_folder["id"]
            }
        )
        new_id = res.json()["file_id"]

        requests.post(
            "https://dynalist.io/api/v1/doc/edit",
            json={
                "token": API_TOKEN,
                "file_id": new_id,
                "changes": [{
                    "action": "insert",
                    "parent_id": "root",
                    "index": 0,
                    "nodes": nodes
                }]
            }
        )

        return "ok"

    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run()
