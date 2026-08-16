import csv
from pathlib import Path


class CsvStorage:
    """CSVファイルへの保存を担当するクラス"""

    HEADER = [
        "計測日",
        "ID",
        "記事タイトル",
        "ビュー",
        "スキ",
        "コメント",
    ]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def append_articles(self, measurement_date: str, articles: list[list]) -> None:
        """記事データをCSVに追記する"""

        file_exists = self.file_path.exists()

        with self.file_path.open(
            "a",
            newline="",
            encoding="utf-8-sig",
        ) as file:

            writer = csv.writer(file)

            # ファイルが存在しない場合だけヘッダーを書く
            if not file_exists:
                writer.writerow(self.HEADER)

            for article in articles:
                writer.writerow(
                    [
                        measurement_date,
                        *article,
                    ]
                )

    def create_if_not_exists(self) -> None:
        """CSVが存在しなければ空のCSVを作成する"""

        if self.file_path.exists():
            return

        with self.file_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(self.HEADER)