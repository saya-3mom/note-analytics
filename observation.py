import csv
from datetime import datetime
from pathlib import Path


class ObservationManager:
    """記事の観測データを管理する"""

    FIELDNAMES = [
        "observed_at",
        "management_id",
        "note_key",
        "views",
        "likes",
        "comments",
    ]

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path

    def append(
        self,
        articles: list[dict],
    ):
        """
        現在の記事情報を観測データとして追加する。

        management_id が DEL で始まる記事は対象外。
        同一日に同じ管理IDが存在する場合は追加しない。
        """

        today = datetime.now().strftime("%Y-%m-%d")

        existing_rows = self._load()

        # 今日すでに観測済みの管理ID
        observed_today = {
            row["management_id"]
            for row in existing_rows
            if row.get("observed_at") == today
        }

        new_rows = []

        for article in articles:

            management_id = article.get("management_id", "").strip()

            # 管理ID未設定は対象外
            if not management_id:
                continue

            # DELで始まる記事は対象外
            if management_id.startswith("DEL"):
                continue

            # 同じ日にすでに観測済みなら追加しない
            if management_id in observed_today:
                continue

            row = {
                "observed_at": today,
                "management_id": management_id,
                "note_key": article.get("note_key", ""),
                "views": article.get("views", 0),
                "likes": article.get("likes", 0),
                "comments": article.get("comments", 0),
            }

            new_rows.append(row)

        if not new_rows:
            print("観測対象の新規データはありません。")
            return

        self._save(existing_rows + new_rows)

        print(
            f"観測データ追加: {len(new_rows)}記事"
        )

    def _load(self) -> list[dict]:
        """既存の観測データを読み込む"""

        if not self.csv_path.exists():
            return []

        with open(
            self.csv_path,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _save(self, rows: list[dict]):
        """観測データを保存する"""

        with open(
            self.csv_path,
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=self.FIELDNAMES,
            )

            writer.writeheader()
            writer.writerows(rows)