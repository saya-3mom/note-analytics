import os
from typing import Any

import requests
from dotenv import load_dotenv


class NoteClient:
    """noteの非公式APIから記事情報を取得するクライアント"""

    BASE_URL = "https://note.com"

    def __init__(self):
        load_dotenv()

        self.cookie = os.getenv("NOTE_COOKIE")
        self.client_code = os.getenv("NOTE_CLIENT_CODE")

        if not self.cookie:
            raise RuntimeError(
                "NOTE_COOKIE が .env に設定されていません。"
            )

        if not self.client_code:
            raise RuntimeError(
                "NOTE_CLIENT_CODE が .env に設定されていません。"
            )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Referer": "https://note.com/sitesettings/stats",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "X-Note-Client-Code": self.client_code,
                "Cookie": self.cookie,
            }
        )

    def get_articles(self) -> list[dict[str, Any]]:
        """
        noteの全記事情報を取得する。

        stats/pvからアクセス状況を取得し、
        v3/notes/{key} から記事の詳細情報を取得する。

        Returns:
            [
                {
                    "note_id": 記事ID,
                    "note_key": 記事key,
                    "title": 記事タイトル,
                    "published_at": 投稿日時,
                    "url": 記事URL,
                    "price": 価格,
                    "views": ビュー数,
                    "likes": スキ数,
                    "comments": コメント数,
                },
                ...
            ]
        """

        articles = []
        page = 1

        while True:

            url = (
                f"{self.BASE_URL}/api/v1/stats/pv"
                f"?filter=all&page={page}&sort=pv"
            )

            response = self.session.get(
                url,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            note_stats = (
                data
                .get("data", {})
                .get("note_stats", [])
            )

            if not note_stats:
                break

            for item in note_stats:

                title = item.get("name")
                note_key = item.get("key")

                if not title or not note_key:
                    continue

                # ----------------------------------
                # 記事詳細を取得
                # ----------------------------------

                try:
                    detail = self.get_article_detail(note_key)

                except requests.HTTPError as e:
                    print(
                        f"記事詳細取得失敗: "
                        f"{note_key} / {e}"
                    )

                    # 詳細取得できなくても
                    # stats側の情報は残す
                    detail = {
                        "note_id": item.get("id"),
                        "note_key": note_key,
                        "title": title,
                        "published_at": "",
                        "url": "",
                        "price": "",
                    }

                # ----------------------------------
                # 記事情報をまとめる
                # ----------------------------------

                article = {
                    "note_id": detail.get(
                        "note_id",
                        item.get("id"),
                    ),

                    "note_key": note_key,

                    "title": detail.get(
                        "title",
                        title,
                    ),

                    "published_at": detail.get(
                        "published_at",
                        "",
                    ),

                    "url": detail.get(
                        "url",
                        "",
                    ),

                    "price": detail.get(
                        "price",
                        "",
                    ),

                    "views": item.get(
                        "read_count",
                        0,
                    ),

                    "likes": item.get(
                        "like_count",
                        0,
                    ),

                    "comments": item.get(
                        "comment_count",
                        0,
                    ),
                }

                articles.append(article)

                print(
                    f"{article['title']} "
                    f"| {article['views']} views "
                    f"| {article['likes']} likes"
                )

            page += 1

        return articles

    def get_article_detail(self, article_key: str) -> dict:
        """note記事の詳細情報を取得する"""

        url = f"{self.BASE_URL}/api/v3/notes/{article_key}"

        response = self.session.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()["data"]

        return {
            "note_id": data.get("id"),
            "note_key": data.get("key"),
            "title": data.get("name"),
            "published_at": data.get("publish_at"),
            "url": data.get("note_url"),
            "like_count": data.get("like_count"),
            "comment_count": data.get("comment_count"),
            "price": data.get("price"),
        }