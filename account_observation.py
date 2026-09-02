import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class AccountObservationManager:
    """noteアカウントの観測データを管理する"""

    FIELDNAMES = [
        "observed_at",
        "follower_count",
    ]

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def record(self, follower_count: int):
        """フォロワー数を記録する"""

        today = datetime.now(
            ZoneInfo("Asia/Tokyo")
        ).date().isoformat()

        rows = []

        if self.csv_path.exists():
            with self.csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        # 同日の重複記録を防ぐ
        for row in rows:
            if row["observed_at"] == today:
                print(
                    f"アカウント観測データは既に存在します: "
                    f"{today}"
                )
                return

        rows.append({
            "observed_at": today,
            "follower_count": follower_count,
        })

        with self.csv_path.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.FIELDNAMES
            )
            writer.writeheader()
            writer.writerows(rows)

        print(
            f"アカウント観測データ保存完了: "
            f"{today} / フォロワー {follower_count}"
        )
