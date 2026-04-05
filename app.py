from flask import Flask
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

TOKEN = "i6L0LFDkM7GojePgYmclsdM0T5WcwCr_8zaugOvfaEOZpf36pecJGpQeFN9e_CpXkIeqDZK4evfw7gE8JOEBOfsZKXNKhz3swE1t96vHb2d4SPC-cdjnrNw7lABVU5Nh"

WEEKDAY = ["月","火","水","木","金","土","日"]

@app.route("/")
def main():
    try:
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        today_str = today.strftime("%Y/%m/%d") + f"({WEEKDAY[today.weekday()]})"
        yesterday_str = yesterday.strftime("%Y/%m/%d") + f"({WEEKDAY[yesterday.weekday()]})"
        month_str = today.strftime("%Y/%m")

        # ---------- ファイル一覧 ----------
        res = requests.post(
            "https://dynalist.io/api/v1/file/list",
            json={"token": TOKEN}
        )
        files = res.json()["files"]

        # ---------- 今日チェック ----------
        if any(f["title"] == today_str for f in files):
            return "skip"

        # ---------- Bujo ----------
        bujo = next((f for f in files if f["title"] == "Bujo" and f["type"] == "folder"), None)

        # ---------- 月フォルダ ----------
        month_folder = None
        for cid in bujo.get("children", []):
            f = next((x for x in files if x["id"] == cid), None)
            if f and f["title"] == month_str:
                month_folder = f

        if not month_folder:
            create_res = requests.post(
                "https://dynalist.io/api/v1/file/create",
                json={
                    "token": TOKEN,
                    "title": month_str,
                    "type": "folder",
                    "parent_id": bujo["id"]
                }
            )
            month_folder = create_res.json()["file"]

        # ---------- 前日ドキュメント ----------
        source = next((f for f in files if f["title"] == yesterday_str), None)
        if not source:
            return "no source"

        # ---------- 中身取得 ----------
        doc_res = requests.post(
            "https://dynalist.io/api/v1/doc/read",
            json={
                "token": TOKEN,
                "file_id": source["id"]
            }
        )
        doc = doc_res.json()

        nodes = doc["nodes"]

        # ---------- 新規作成 ----------
        create_doc_res = requests.post(
            "https://dynalist.io/api/v1/file/create",
            json={
                "token": TOKEN,
                "title": today_str,
                "type": "document",
                "parent_id": month_folder["id"]
            }
        )
        new_file = create_doc_res.json()["file"]

        # ---------- ノードコピー ----------
        requests.post(
            "https://dynalist.io/api/v1/doc/edit",
            json={
                "token": TOKEN,
                "file_id": new_file["id"],
                "changes": [
                    {
                        "action": "insert",
                        "parent_id": None,
                        "index": 0,
                        "content": n["content"]
                    }
                    for n in nodes if n.get("content")
                ]
            }
        )

        return "ok"

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run()
