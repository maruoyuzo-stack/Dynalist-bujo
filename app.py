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

        log = []

        # ---------- ファイル一覧 ----------
        res = requests.post(
            "https://dynalist.io/api/v1/file/list",
            json={"token": TOKEN}
        )
        data = res.json()
        files = data["files"]

        log.append(f"today={today_str}")
        log.append(f"yesterday={yesterday_str}")

        # ---------- 今日チェック ----------
        if any(f["title"] == today_str for f in files):
            return "skip (already exists)"

        # ---------- Bujo ----------
        bujo = next((f for f in files if f["title"] == "Bujo" and f["type"] == "folder"), None)
        log.append(f"bujo_id={bujo['id'] if bujo else 'None'}")

        # ---------- 月フォルダ ----------
        month_folder = None
        for cid in bujo.get("children", []):
            f = next((x for x in files if x["id"] == cid), None)
            if f:
                log.append(f"child={f['title']}")
            if f and f["title"] == month_str:
                month_folder = f

        if not month_folder:
            log.append("month folder NOT found → creating")
            create_res = requests.post(
                "https://dynalist.io/api/v1/file/create",
                json={
                    "token": TOKEN,
                    "title": month_str,
                    "type": "folder",
                    "parent_id": bujo["id"]
                }
            )
            log.append(f"create_res={create_res.text}")
            month_folder = create_res.json()["file"]

        log.append(f"month_id={month_folder['id']}")

        # ---------- コピー元 ----------
        source = next((f for f in files if f["title"] == yesterday_str), None)

        if not source:
            log.append("yesterday NOT found → fallback")
            source = files[-1]

        log.append(f"source={source['title']} id={source['id']}")

        # ---------- コピー ----------
        copy_res = requests.post(
            "https://dynalist.io/api/v1/doc/copy",
            json={
                "token": TOKEN,
                "file_id": source["id"],
                "parent_id": month_folder["id"]
            }
        )

        log.append(f"copy_status={copy_res.status_code}")
        log.append(f"copy_res={copy_res.text}")

        return "\n".join(log)

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run()
