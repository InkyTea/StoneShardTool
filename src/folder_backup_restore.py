import os
import time
import zipfile
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置参数
USER_NAME = os.getlogin() # 用户名
TARGET_FOLDER = f"C:/Users/{USER_NAME}/AppData/Local/StoneShard/characters_v1/character_2" # 存档位置
UPLOAD_FOLDER = f"C:/Users/{USER_NAME}/AppData/Local/StoneShard" # 上传位置
BACKUP_FOLDER = f"{TARGET_FOLDER}/exitsave_1"  # 需要监控的文件夹路径
MONITORED_FILE = "save.map"     # 需要监控的文件名（位于目标文件夹内）
BACKUP_DIR = f"{TARGET_FOLDER}/tool_backups"  # 备份存储目录
BACKUP_NUM = 4 # 备份数量

def backup_folder():
    """备份目标文件夹到压缩文件"""
    print(f"\n检测到文件更新：{MONITORED_FILE}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        os.makedirs(BACKUP_DIR, exist_ok=True)
        parent_dir = os.path.dirname(BACKUP_FOLDER)
        #folder_name = os.path.basename(BACKUP_FOLDER)
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(BACKUP_FOLDER):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, parent_dir)
                    zipf.write(file_path, arcname)

        backups = [f for f in os.listdir(BACKUP_DIR) 
                  if f.startswith('backup_') and f.endswith('.zip')]
        
        # 检查备份数量
        if len(backups) > BACKUP_NUM:
            backups.sort()
            old_backup = os.path.join(BACKUP_DIR, backups[0])
            os.remove(old_backup)

        print(f"成功创建备份：{backup_path}")
        return True
    except Exception as e:
        print(f"备份失败：{e}")
        return False

def upload(local_file_path):
    remote_server_url = "https://www.inktea.eu.org/uploadarchive"
    try:
        # 发送HTTP POST请求，上传文件到远程服务器
        with open(local_file_path, "rb") as f:
            response = requests.post(
                remote_server_url, verify=False)
            response.close()

        # 检查响应状态码是否为200 (成功)
        if response.status_code == 200:
            print("文件上传成功！")
        else:
            print(f"文件上传失败，HTTP状态码：{response.status_code}")
    except Exception as e:
        print(f"文件上传失败，错误信息：{str(e)}")

def upload_folder():
    try:
        backup_filename = "StoneShard.zip"
        backup_path = os.path.join(os.path.dirname(UPLOAD_FOLDER), backup_filename)

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        parent_dir = os.path.dirname(UPLOAD_FOLDER)
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(UPLOAD_FOLDER):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, parent_dir)
                    zipf.write(file_path, arcname)
        print(f"成功创建备份：{backup_path}")
        upload(backup_path)
        return True
    except Exception as e:
        print(f"备份失败：{e}")
        return False

def restore_folder():
    """从最新备份恢复文件夹"""
    print(f"\n检测到文件夹不存在：{BACKUP_FOLDER}")
    try:
        if not os.path.isdir(BACKUP_DIR):
            print("备份目录不存在")
            return False

        backups = [f for f in os.listdir(BACKUP_DIR) 
                  if f.startswith('backup_') and f.endswith('.zip')]
        if not backups:
            print("没有找到备份文件")
            return False

        backups.sort(reverse=True)
        latest_backup = os.path.join(BACKUP_DIR, backups[0])
        parent_dir = os.path.dirname(BACKUP_FOLDER)
        
        os.makedirs(parent_dir, exist_ok=True)
        
        with zipfile.ZipFile(latest_backup, 'r') as zipf:
            zipf.extractall(parent_dir)
        
        print(f"从备份恢复成功：{latest_backup}")
        return True
    except Exception as e:
        print(f"恢复失败：{e}")
        return False

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_backup = 0
        self.cooldown = 5  # 防止重复备份的冷却时间（秒）

    def on_deleted(self, event):
        if event.is_directory:
            if event.src_path == BACKUP_FOLDER:
                restore_folder()

    def on_modified(self, event):
        if not event.is_directory:
            target_path = os.path.join(BACKUP_FOLDER, MONITORED_FILE)
            if event.src_path == target_path:
                if time.time() - self.last_backup > self.cooldown:
                    time.sleep(2)
                    if os.path.isdir(BACKUP_FOLDER):
                        backup_folder()
                    else:
                        restore_folder()
                    self.last_backup = time.time()
class AutoBackup:
    def __init__(self):
        event_handler = FileChangeHandler()
        self.observer = Observer()
        self.observer.schedule(event_handler, BACKUP_FOLDER, recursive=True)
        self.run = False
        pass
    def main(self):
        if self.run:
            self.run = False
        else:
            self.run = True
            self.start()
    def upload(self):
        upload_folder()

    def start(self):
        # 启动时检查并恢复
        if not os.path.exists(BACKUP_FOLDER):
            restore_folder()
        self.observer.start()
        print(f"开始监控文件夹：{BACKUP_FOLDER}")
        print(f"监控文件：{MONITORED_FILE}")
        print(f"备份存储位置：{BACKUP_DIR}")

        
        while self.run:
            time.sleep(1)
        self.observer.join()
        print(f"停止监控")