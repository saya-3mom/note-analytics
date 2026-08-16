from datetime import datetime
from pathlib import Path

from note_client import NoteClient
from article_master import ArticleMaster
from observation import ObservationManager


# ==========================================
# ファイル設定
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

OBSERVATIONS_CSV = BASE_DIR / "observations.csv"


# ==========================================
# メイン処理
# ==========================================

def main():

    start = datetime.now()

    print("")
    print("========================================")
    print("note観測処理 開始")
    print(f"開始時刻: {start}")
    print("========================================")

    try:

        # ==================================
        # 1. noteから最新情報を取得
        # ==================================

        print("")
        print("[1] noteから記事情報を取得")

        client = NoteClient()

        note_articles = client.get_articles()

        print(
            f"取得記事数: {len(note_articles)}"
        )

        # ==================================
        # 2. 記事マスタを更新
        # ==================================

        print("")
        print("[2] 記事マスタを更新")

        article_master = ArticleMaster()

        print(
            f"既存記事数: "
            f"{len(article_master.articles)}"
        )

        new_articles = article_master.update_from_note(
            note_articles
        )

        article_master.save()

        print(
            f"記事マスタ保存完了: "
            f"{len(article_master.articles)}記事"
        )

        # ==================================
        # 3. 新規記事を通知
        # ==================================

        if new_articles:

            print("")
            print("⚠ 新しい記事があります")

            for article in new_articles:

                print(
                    f"  - {article['title']}"
                )

                print(
                    "    管理ID・ジャンルを設定してください"
                )

        # ==================================
        # 4. 観測データを記録
        # ==================================

        print("")
        print("[3] 観測データを記録")

        observation_manager = ObservationManager(
            OBSERVATIONS_CSV
        )

        observation_manager.append(
            article_master.articles
        )

        # ==================================
        # 完了
        # ==================================

        print("")
        print("更新完了")

    except Exception as e:

        print("")
        print("========================================")
        print("ERROR")
        print("========================================")

        print(
            f"{type(e).__name__}: {e}"
        )

        raise

    finally:

        finish = datetime.now()

        print("")
        print("========================================")
        print("終了")
        print(f"終了時刻: {finish}")
        print(
            "処理時間: "
            f"{finish - start}"
        )
        print("========================================")
        print("")


# ==========================================
# エントリーポイント
# ==========================================

if __name__ == "__main__":
    main()