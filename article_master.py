import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ARTICLE_MASTER_FILE = BASE_DIR / "articles.csv"


class ArticleMaster:
    """記事マスタ（articles.csv）を管理する。"""

    FIELDNAMES = [
        "management_id",
        "genre",
        "note_key",
        "title",
        "published_at",
        "url",
        "price",
        "views",
        "likes",
        "comments",
    ]

    def __init__(self):
        if not ARTICLE_MASTER_FILE.exists():
            raise FileNotFoundError(
                f"{ARTICLE_MASTER_FILE} がありません。"
            )

        self.articles = self._load()

    # ==========================================
    # 読み込み
    # ==========================================

    def _load(self) -> list[dict]:
        """記事マスタを読み込む。"""

        with ARTICLE_MASTER_FILE.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            return list(csv.DictReader(f))

    # ==========================================
    # 保存
    # ==========================================

    def save(self):
        """記事マスタを保存する。"""

        with ARTICLE_MASTER_FILE.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=self.FIELDNAMES,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(self.articles)

    # ==========================================
    # 検索
    # ==========================================

    def get_by_note_key(
        self,
        note_key: str,
    ) -> dict | None:
        """note_keyから記事を取得する。"""

        for article in self.articles:

            if article.get("note_key") == note_key:
                return article

        return None

    def get_by_management_id(
        self,
        management_id: str,
    ) -> dict | None:
        """管理IDから記事を取得する。"""

        for article in self.articles:

            if article.get("management_id") == management_id:
                return article

        return None

    # ==========================================
    # noteから取得した情報を反映
    # ==========================================

    def update_from_note(
        self,
        note_articles: list[dict],
    ) -> list[dict]:
        """
        noteから取得した記事情報を記事マスタへ反映する。

        既存記事:
            management_id・genreは保持し、
            note側の情報だけ更新する。

        新規記事:
            management_id・genreを空欄で追加する。

        Returns:
            新しく追加された記事一覧
        """

        existing_by_key = {
            article["note_key"]: article
            for article in self.articles
            if article.get("note_key")
        }

        new_articles = []

        for note_article in note_articles:

            note_key = note_article.get("note_key")

            if not note_key:
                continue

            # ----------------------------------
            # 既存記事
            # ----------------------------------

            if note_key in existing_by_key:

                article = existing_by_key[note_key]

                article["title"] = note_article.get(
                    "title",
                    article.get("title", ""),
                )

                article["published_at"] = note_article.get(
                    "published_at",
                    article.get("published_at", ""),
                )

                article["url"] = note_article.get(
                    "url",
                    article.get("url", ""),
                )

                article["price"] = note_article.get(
                    "price",
                    article.get("price", ""),
                )

                article["views"] = note_article.get(
                    "views",
                    article.get("views", 0),
                )

                article["likes"] = note_article.get(
                    "likes",
                    article.get("likes", 0),
                )

                article["comments"] = note_article.get(
                    "comments",
                    article.get("comments", 0),
                )

            # ----------------------------------
            # 新規記事
            # ----------------------------------

            else:

                article = {
                    "management_id": "",
                    "genre": "",
                    "note_key": note_key,
                    "title": note_article.get(
                        "title",
                        "",
                    ),
                    "published_at": note_article.get(
                        "published_at",
                        "",
                    ),
                    "url": note_article.get(
                        "url",
                        "",
                    ),
                    "price": note_article.get(
                        "price",
                        "",
                    ),
                    "views": note_article.get(
                        "views",
                        0,
                    ),
                    "likes": note_article.get(
                        "likes",
                        0,
                    ),
                    "comments": note_article.get(
                        "comments",
                        0,
                    ),
                }

                self.articles.append(article)
                new_articles.append(article)

                print(
                    f"[NEW] 新しい記事を検出: "
                    f"{article['title']}"
                )

        return new_articles