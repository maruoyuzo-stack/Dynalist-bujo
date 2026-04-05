from flask import Flask
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

TOKEN = i6L0LFDkM7GojePgYmclsdM0T5WcwCr_8zaugOvfaEOZpf36pecJGpQeFN9e_CpXkIeqDZK4evfw7gE8JOEBOfsZKXNKhz3swE1t96vHb2d4SPC-cdjnrNw7lABVU5Nh

@app.route("/")
def main():
    try:
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        today_str = today.strftime("%Y/%m/%d(%a)")
        yesterday_str = yesterday.strftime("%Y/%m/%d(%a)")
        month_str = today.strftime("%Y/%m")

        # ---------- ① ファイル一覧取得 ----------
        res = requests.post(
            "https://dynalist.io/api/v1/file/list",
            json={"token": TOKEN}
        )
        data = res.json()
        files = data["files"]

        # ---------- ② 今日の存在チェック ----------
        if any(f["title"] == today_str for f in files):
            return "skip"

        # ---------- ③ Bujoフォルダ取得 ----------
        bujo = next((f for f in files if f["title"] == "Bujo" and f["type"] == "folder"), None)
        if not bujo:
            return "Bujo folder not found"

        # ---------- ④ 月フォルダ取得 or 作成 ----------
        month_folder = next((f for f in files if f["title"] == month_str and f["type"] == "folder"), None)

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

        # ---------- ⑤ 前日のドキュメント取得 ----------
        source = next((f for f in files if f["title"] == yesterday_str), None)

        # ---------- ⑥ 見つからない場合（保険） ----------
        if not source:
            # Bujo配下から全部集める
            candidates = []
            for m_id in bujo.get("children", []):
                m = next((f for f in files if f["id"] == m_id), None)
                if m and "children" in m:
                    for cid in m["children"]:
                        child = next((f for f in files if f["id"] == cid), None)
                        if child and child["type"] == "document":
                            candidates.append(child)

            if not candidates:
                return "no source found"

            # 適当に一番新しそうなの
            source = candidates[-1]

        # ---------- ⑦ コピー ----------
        requests.post(
            "https://dynalist.io/api/v1/doc/copy",
            json={
                "token": TOKEN,
                "file_id": source["id"],
                "parent_id": month_folder["id"]
            }
        )

        return "ok"

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run()
