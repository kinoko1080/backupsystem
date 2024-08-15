import os
import zipfile
from datetime import datetime, timedelta
from git import Repo
import schedule
import time

# 設定
MINECRAFT_WORLD_PATH = "Minecraftサーバーのワールドデータが保存されているディレクトリのパス"
GITHUB_REPO_PATH = "ローカルのGitHubリポジトリのパス"
GITHUB_REMOTE_URL = "GitHubリモートリポジトリのURL"
BACKUP_RETENTION_DAYS = 3

def backup_world():
    # 現在の日時を取得
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # バックアップファイル名を作成
    backup_filename = f"minecraft_world_backup_{timestamp}.zip"
    backup_path = os.path.join(GITHUB_REPO_PATH, backup_filename)
    
    # ワールドデータをZIPファイルに圧縮
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(MINECRAFT_WORLD_PATH):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, MINECRAFT_WORLD_PATH)
                zipf.write(file_path, arcname)
    
    # GitHubリポジトリを開く
    repo = Repo(GITHUB_REPO_PATH)
    
    # 変更をステージングに追加
    repo.index.add([backup_filename])
    
    # コミットを作成
    repo.index.commit(f"Backup Minecraft world - {timestamp}")
    
    # リモートリポジトリにプッシュ
    origin = repo.remote(name='origin')
    origin.push()
    
    print(f"Backup completed: {backup_filename}")

    # 古いバックアップを削除
    delete_old_backups(now)

def delete_old_backups(current_time):
    repo = Repo(GITHUB_REPO_PATH)
    
    backups = []
    for file in os.listdir(GITHUB_REPO_PATH):
        if file.startswith("minecraft_world_backup_") and file.endswith(".zip"):
            file_path = os.path.join(GITHUB_REPO_PATH, file)
            file_time = datetime.strptime(file.split("_")[3].split(".")[0], "%Y%m%d%H%M%S")
            backups.append((file, file_path, file_time))
    
    # バックアップを日時順にソート
    backups.sort(key=lambda x: x[2], reverse=True)
    
    # 最新のバックアップの日時を取得
    if backups:
        latest_backup_time = backups[0][2]
        
        for file, file_path, file_time in backups[1:]:  # 最新のバックアップ以外をチェック
            if (latest_backup_time - file_time).days > BACKUP_RETENTION_DAYS:
                os.remove(file_path)
                print(f"Deleted old backup: {file}")
                
                # GitHubから削除
                repo.index.remove([file])
    
    if repo.index.diff(None):
        repo.index.commit(f"Remove old backups - {current_time.strftime('%Y%m%d_%H%M%S')}")
        # 変更をプッシュ
        origin = repo.remote(name='origin')
        origin.push()

# 毎日午前3時にバックアップを実行するようにスケジュール
schedule.every().day.at("03:00").do(backup_world)

if __name__ == "__main__":
    print("Minecraft world backup script is running...")
    while True:
        schedule.run_pending()
        time.sleep(60)
        
#最新のバックアップからBACKUP_RETENTION_DAYSで指定された日数でバックアップは消えます
#実行するには　pip install GitPython schedule　し、GitPythonとscheduleを入れやがれください