"""
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

        # ---------- ① ファイル一覧 ----------
        res = requests.post(
            "https://dynalist.io/api/v1/file/list",
            json={"token": TOKEN}
        )
        data = res.json()
        files = data["files"]

        # ---------- ② 今日の存在チェック ----------
        if any(f["title"] == today_str for f in files):
            return "skip (already exists)"

        # ---------- ③ Bujoフォルダ ----------
        bujo = next((f for f in files if f["title"] == "Bujo" and f["type"] == "folder"), None)
        if not bujo:
            return "Bujo folder not found"

        # ---------- ④ 月フォルダ（Bujo配下限定） ----------
        month_folder = None
        for cid in bujo.get("children", []):
            f = next((x for x in files if x["id"] == cid), None)
            if f and f["title"] == month_str and f["type"] == "folder":
                month_folder = f
                break

        # ---------- ⑤ 月フォルダ作成 ----------
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
            res_json = create_res.json()

            if res_json.get("_code") != "Ok":
                return f"month folder create error: {res_json}"

            month_folder = {
                "id": res_json.get("file_id"),
                "title": month_str
            }

        # ---------- ⑥ 前日ドキュメント ----------
        source = next((f for f in files if f["title"] == yesterday_str), None)
        if not source:
            return "no source document"

        # ---------- ⑦ 中身取得 ----------
        doc_res = requests.post(
            "https://dynalist.io/api/v1/doc/read",
            json={
                "token": TOKEN,
                "file_id": source["id"]
            }
        )
        doc_json = doc_res.json()

        if doc_json.get("_code") != "Ok":
            return f"doc read error: {doc_json}"

        nodes = doc_json.get("nodes", [])

        # ---------- ⑧ 新規ドキュメント作成 ----------
        create_doc_res = requests.post(
            "https://dynalist.io/api/v1/file/create",
            json={
                "token": TOKEN,
                "title": today_str,
                "type": "document",
                "parent_id": month_folder["id"]
            }
        )

        res_json = create_doc_res.json()

        if res_json.get("_code") != "Ok":
            return f"document create error: {res_json}"

        new_file_id = res_json.get("file_id")

        if not new_file_id:
            return f"no file_id returned: {res_json}"

        # ---------- ⑨ ノードコピー ----------
        changes = []
        for n in nodes:
            content = n.get("content")
            if content:
                changes.append({
                    "action": "insert",
                    "parent_id": None,
                    "index": -1,
                    "content": content
                })

        if changes:
            edit_res = requests.post(
                "https://dynalist.io/api/v1/doc/edit",
                json={
                    "token": TOKEN,
                    "file_id": new_file_id,
                    "changes": changes
                }
            )

            edit_json = edit_res.json()
            if edit_json.get("_code") != "Ok":
                return f"edit error: {edit_json}"

        return "ok"

    except Exception as e:
        return str(e)
        """
from flask import Flask
import requests

app = Flask(__name__)

TOKEN = "ここにDynalistのトークン"

@app.route("/")
def test_create():
    try:
        res = requests.post(
            "https://dynalist.io/api/v1/file/create",
            json={
                "token": TOKEN,
                "title": "TEST_DOCUMENT",
                "type": "document"
            }
        )

        return res.text

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run()


if __name__ == "__main__":
    app.run()
