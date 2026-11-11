import sqlite3
import time
import requests
from bs4 import BeautifulSoup


def setup_database():
    """データベースとテーブルの作成"""
    conn = sqlite3.connect("github_repositories.db")
    cursor = conn.cursor()

    # テーブルが存在しない場合は作成
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT,
            stars TEXT
        )
    """
    )
    conn.commit()
    return conn


def scrape_google_repos():
    """GitHubのGoogle組織ページからスクレイピング"""
    url = "https://github.com/orgs/google/repositories"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 指定されたインターバル（ルール通り time.sleep(1) を挿入）
    time.sleep(1)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repo_list = []

    # リポジトリカードの抽出
    repos = soup.select("li.Box-row")
    for repo in repos:
        # リポジトリ名
        name_elem = repo.select_one('a[aria-describedby], a[data-hovercard-type="repository"]')
        repo_name = name_elem.text.strip() if name_elem else "N/A"

        # 主要言語
        lang_elem = repo.select_one('span[itemprop="programmingLanguage"]')
        language = lang_elem.text.strip() if lang_elem else "None"

        # スター数
        star_elem = repo.select_one('a[href$="/stargazers"]')
        stars = star_elem.text.strip() if star_elem else "0"

        repo_list.append((repo_name, language, stars))

    return repo_list


def save_to_db(conn, repo_data):
    """取得したデータをDBへ保存"""
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
    """,
        repo_data,
    )
    conn.commit()


def display_db_data(conn):
    """SELECT文で保存データを取得し表示"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, language, stars FROM repositories")
    rows = cursor.fetchall()

    print("\n--- 保存されたデータ一覧 (SELECT結果) ---")
    print(f"{'ID':<4} | {'Repository Name':<35} | {'Language':<12} | {'Stars'}")
    print("-" * 65)
    for row in rows:
        print(f"{row[0]:<4} | {row[1]:<35} | {row[2]:<12} | {row[3]}")


if __name__ == "__main__":
    # DB初期化
    conn = setup_database()

    # スクレイピング実行
    print("スクレイピングを開始します...")
    data = scrape_google_repos()

    if data:
        # DBへ保存
        save_to_db(conn, data)
        print(f"{len(data)}件のデータを保存しました。")

        # SELECT文で表示（課題要件）
        display_db_data(conn)
    else:
        print("データの取得に失敗したか、データが存在しませんでした。")

    conn.close()