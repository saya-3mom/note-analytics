import csv
from datetime import datetime
from pathlib import Path


class AnalysisManager:
    """記事と観測データを分析する"""

    def __init__(self, articles_csv_path, observations_csv_path):
        self.articles_csv_path = Path(articles_csv_path)
        self.observations_csv_path = Path(observations_csv_path)

    def load_csv(self, csv_path):
        """CSVを読み込む"""
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def load_articles(self):
        """記事マスタを読み込む"""
        return self.load_csv(self.articles_csv_path)

    def load_observations(self):
        """観測データを読み込む"""
        return self.load_csv(self.observations_csv_path)

    def get_article_map(self):
        """note_keyをキーにした記事マスタを作る"""
        articles = self.load_articles()

        return {
            article["note_key"]: article
            for article in articles
        }

    def get_latest_changes(self):
        """記事ごとの最新観測と前回観測との差分を取得する"""
        observations = self.load_observations()

        articles = {}

        for row in observations:
            note_key = row["note_key"]
            articles.setdefault(note_key, []).append(row)

        results = []

        for note_key, rows in articles.items():
            rows.sort(key=lambda row: row["observed_at"])

            latest = rows[-1]

            if len(rows) >= 2:
                previous = rows[-2]

                views_diff = int(latest["views"]) - int(previous["views"])
                likes_diff = int(latest["likes"]) - int(previous["likes"])
                comments_diff = (
                    int(latest["comments"]) - int(previous["comments"])
                )
            else:
                views_diff = None
                likes_diff = None
                comments_diff = None

            views = int(latest["views"])
            likes = int(latest["likes"])

            if views > 0:
                like_rate = likes / views * 100
            else:
                like_rate = 0

            results.append(
                {
                    "note_key": note_key,
                    "management_id": latest["management_id"],
                    "observed_at": latest["observed_at"],
                    "views": views,
                    "likes": likes,
                    "comments": int(latest["comments"]),
                    "like_rate": like_rate,
                    "views_diff": views_diff,
                    "likes_diff": likes_diff,
                    "comments_diff": comments_diff,
                }
            )

        return results

    def add_elapsed_days(self, results):
        """公開日からの経過日数を追加する"""
        article_map = self.get_article_map()

        for result in results:
            article = article_map.get(result["note_key"])

            if article is None:
                result["elapsed_days"] = None
                continue

            published_at = datetime.fromisoformat(
                article["published_at"]
            )

            observed_at = datetime.fromisoformat(
                result["observed_at"]
            )

            elapsed_days = (observed_at.date() - published_at.date()).days

            result["elapsed_days"] = elapsed_days

        return results

    def get_article_history(self, management_id):
        """指定した記事の観測履歴を取得する"""
        articles = self.load_articles()
        observations = self.load_observations()

        article = next(
            (
                article
                for article in articles
                if article["management_id"] == management_id
            ),
            None,
        )

        if article is None:
            return None, []

        article_observations = [
            observation
            for observation in observations
            if observation["management_id"] == management_id
        ]

        published_at = datetime.fromisoformat(
            article["published_at"]
        )

        history = []

        for observation in article_observations:
            observed_at = datetime.fromisoformat(
                observation["observed_at"]
            )

            elapsed_days = (
                observed_at.date() - published_at.date()
            ).days

            history.append(
                {
                    "observed_at": observation["observed_at"],
                    "elapsed_days": elapsed_days,
                    "views": int(observation["views"]),
                    "likes": int(observation["likes"]),
                    "comments": int(observation["comments"]),
                }
            )

        history.sort(key=lambda row: row["observed_at"])

        return article, history
    
    def get_growth_comparison(self):
        """全記事の公開後日数別のビュー数を取得する"""
        articles = self.load_articles()
        observations = self.load_observations()

        article_map = {
            article["management_id"]: article
            for article in articles
        }

        comparison = {}

        for observation in observations:
            management_id = observation["management_id"]

            article = article_map.get(management_id)

            if article is None:
                continue

            published_at = datetime.fromisoformat(
                article["published_at"]
            )

            observed_at = datetime.fromisoformat(
                observation["observed_at"]
            )

            elapsed_days = (
                observed_at.date() - published_at.date()
            ).days

            comparison.setdefault(management_id, {})
            comparison[management_id][elapsed_days] = int(
                observation["views"]
            )

        return comparison


def print_like_rate_ranking(results):
    """スキ率ランキングを表示する"""
    print()
    print("=== スキ率ランキング ===")

    ranked = sorted(
        results,
        key=lambda result: result["like_rate"],
        reverse=True,
    )

    for i, result in enumerate(ranked, start=1):
        print(
            f"{i:2}. "
            f"{result['management_id']:12} "
            f"{result['like_rate']:5.1f}% "
            f"({result['likes']}/{result['views']})"
        )


def print_views_growth_ranking(results):
    """前回からのビュー増加ランキングを表示する"""
    print()
    print("=== 前回からのビュー増加ランキング ===")

    ranked = sorted(
        results,
        key=lambda result: (
            result["views_diff"] is not None,
            result["views_diff"] or 0,
        ),
        reverse=True,
    )

    for i, result in enumerate(ranked, start=1):
        if result["views_diff"] is None:
            diff_text = "データなし"
        else:
            diff_text = f"+{result['views_diff']}"

        print(
            f"{i:2}. "
            f"{result['management_id']:12} "
            f"{diff_text}"
        )


def print_elapsed_days(results):
    """公開後の経過日数を表示する"""
    print()
    print("=== 公開後経過日数 ===")

    ranked = sorted(
        results,
        key=lambda result: result["elapsed_days"]
        if result["elapsed_days"] is not None
        else -1,
    )

    for result in ranked:
        if result["elapsed_days"] is None:
            elapsed_text = "不明"
        else:
            elapsed_text = f"{result['elapsed_days']}日後"

        print(
            f"{result['management_id']:12} "
            f"{elapsed_text:8} "
            f"ビュー:{result['views']:4} "
            f"スキ:{result['likes']:3}"
        )

def print_article_history(article, history):
    """指定した記事の成長履歴を表示する"""
    print()
    print(f"=== {article['management_id']} の成長履歴 ===")
    print()
    print(f"公開日: {article['published_at']}")
    print(f"タイトル: {article['title']}")

    if not history:
        print()
        print("観測データがありません。")
        return

    print()

    for row in history:
        print(
            f"公開{row['elapsed_days']:3}日後 "
            f"観測日:{row['observed_at']} "
            f"ビュー:{row['views']:4} "
            f"スキ:{row['likes']:3} "
            f"コメント:{row['comments']:2}"
        )

def print_growth_comparison(comparison):
    """公開後1・3・7・14・30日後のビューを比較する"""
    print()
    print("=== 公開後日数別比較（ビュー） ===")

    if not comparison:
        print("観測データがありません。")
        return

    target_days = [1, 3, 7, 14, 30]

    header = f"{'管理ID':12}"

    for day in target_days:
        header += f"{day:>8}日後"

    print(header)

    for management_id in sorted(comparison):
        row = f"{management_id:12}"

        for day in target_days:
            views = comparison[management_id].get(day)

            if views is None:
                row += f"{'-':>10}"
            else:
                row += f"{views:>10}"

        print(row)

def show_initial_growth(observations, article_master, days=3):
    """公開後指定日数以内の初速ランキングを表示する"""

    results = []

    # 記事ごとに観測データをまとめる
    grouped = {}

    for row in observations:
        management_id = row["management_id"]

        if management_id not in grouped:
            grouped[management_id] = []

        grouped[management_id].append(row)

    for article in article_master:
        management_id = article["management_id"]

        if management_id not in grouped:
            continue

        published_at = datetime.fromisoformat(article["published_at"])

        valid_observations = []

        for row in grouped[management_id]:
            observed_at = datetime.fromisoformat(row["observed_at"])

            elapsed_days = (observed_at.date() - published_at.date()).days

            if 1 <= elapsed_days <= days:
                valid_observations.append(
                    (elapsed_days, int(row["views"]))
                )

        if not valid_observations:
            continue

        # 指定期間内で一番後の観測値を採用
        valid_observations.sort(key=lambda x: x[0])
        elapsed_days, views = valid_observations[-1]

        results.append(
            (management_id, elapsed_days, views)
        )

    results.sort(key=lambda x: x[2], reverse=True)

    print()
    print(f"=== 公開後{days}日以内の初速ランキング ===")

    if not results:
        print("初速データがありません。")
        return

    for rank, (management_id, elapsed_days, views) in enumerate(results, 1):
        print(
            f"{rank:2}. {management_id:<12} "
            f"{views:3}ビュー "
            f"（公開{elapsed_days}日後）"
        )

def main():
    import sys

    base_dir = Path(__file__).parent

    articles_csv_path = base_dir / "articles.csv"
    observations_csv_path = base_dir / "observations.csv"

    analyzer = AnalysisManager(
        articles_csv_path,
        observations_csv_path,
    )

    # 記事IDが指定された場合は、その記事の成長履歴を表示
    if len(sys.argv) >= 2:
        management_id = sys.argv[1]

        article, history = analyzer.get_article_history(
            management_id
        )

        if article is None:
            print(f"{management_id} の記事が見つかりません。")
            return

        print_article_history(article, history)
        return

    # 記事IDが指定されていない場合は、通常の分析を表示
    results = analyzer.get_latest_changes()
    results = analyzer.add_elapsed_days(results)

    print("=== 最新の記事分析 ===")

    for result in results:
        print(
            f"{result['management_id']:12} "
            f"ビュー:{result['views']:4} "
            f"スキ:{result['likes']:3} "
            f"スキ率:{result['like_rate']:5.1f}% "
            f"コメント:{result['comments']:2}"
        )

    print_like_rate_ranking(results)
    print_views_growth_ranking(results)
    print_elapsed_days(results)

    comparison = analyzer.get_growth_comparison()
    print_growth_comparison(comparison)

    observations = analyzer.load_observations()
    article_master = analyzer.load_articles()

    show_initial_growth(observations, article_master, days=3)


if __name__ == "__main__":
    main()