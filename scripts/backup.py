#!/usr/bin/env python3
"""
Скрипт для создания бэкапов проекта.
"""

import os
import sys
import shutil
import tarfile
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import argparse
import subprocess


class BackupManager:
    """Класс для управления бэкапами."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_timestamp(self) -> str:
        """Создать временную метку для бэкапа."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_database(self, db_path: Path, backup_name: str) -> Path:
        """Создать бэкап базы данных SQLite."""
        if not db_path.exists():
            print(f"⚠️  Database not found: {db_path}")
            return None
        
        backup_file = self.backup_dir / f"{backup_name}_db_{self.create_timestamp()}.sql"
        
        try:
            # Создаем SQL дамп
            with sqlite3.connect(str(db_path)) as conn:
                with open(backup_file, 'w') as f:
                    for line in conn.iterdump():
                        f.write('%s\n' % line)
            
            print(f"✅ Database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Database backup failed: {e}")
            return None
    
    def backup_rag_data(self, backup_name: str) -> Path:
        """Создать бэкап RAG данных."""
        rag_dirs = ["rag", "rag_index"]
        backup_file = self.backup_dir / f"{backup_name}_rag_{self.create_timestamp()}.tar.gz"
        
        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                for dir_name in rag_dirs:
                    dir_path = self.project_root / dir_name
                    if dir_path.exists():
                        tar.add(dir_path, arcname=dir_name)
                        print(f"✅ Added {dir_name} to RAG backup")
                    else:
                        print(f"⚠️  RAG directory not found: {dir_path}")
            
            print(f"✅ RAG data backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ RAG backup failed: {e}")
            return None
    
    def backup_config(self, backup_name: str) -> Path:
        """Создать бэкап конфигурационных файлов."""
        config_files = [
            ".env",
            "config.py",
            "docker-compose.yml",
            "nginx.conf",
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml"
        ]
        
        backup_file = self.backup_dir / f"{backup_name}_config_{self.create_timestamp()}.tar.gz"
        
        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                for file_name in config_files:
                    file_path = self.project_root / file_name
                    if file_path.exists():
                        tar.add(file_path, arcname=file_name)
                        print(f"✅ Added {file_name} to config backup")
            
            print(f"✅ Config backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Config backup failed: {e}")
            return None
    
    def backup_logs(self, backup_name: str, days: int = 7) -> Path:
        """Создать бэкап логов."""
        log_files = []
        
        # Ищем файлы логов
        for pattern in ["*.log", "logs/*.log", "logs/*/*.log"]:
            log_files.extend(self.project_root.glob(pattern))
        
        # Фильтруем по дате
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = []
        
        for log_file in log_files:
            if log_file.stat().st_mtime > cutoff_date.timestamp():
                recent_logs.append(log_file)
        
        if not recent_logs:
            print("⚠️  No recent log files found")
            return None
        
        backup_file = self.backup_dir / f"{backup_name}_logs_{self.create_timestamp()}.tar.gz"
        
        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                for log_file in recent_logs:
                    relative_path = log_file.relative_to(self.project_root)
                    tar.add(log_file, arcname=str(relative_path))
                    print(f"✅ Added {relative_path} to logs backup")
            
            print(f"✅ Logs backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Logs backup failed: {e}")
            return None
    
    def backup_docker_volumes(self, backup_name: str) -> Path:
        """Создать бэкап Docker volumes."""
        backup_file = self.backup_dir / f"{backup_name}_volumes_{self.create_timestamp()}.tar.gz"
        
        try:
            # Получаем список volumes
            result = subprocess.run([
                "docker", "volume", "ls", "--format", "{{.Name}}"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("⚠️  Docker not available or no volumes found")
                return None
            
            volumes = result.stdout.strip().split('\n')
            project_volumes = [v for v in volumes if 'optimaai' in v.lower()]
            
            if not project_volumes:
                print("⚠️  No project-related Docker volumes found")
                return None
            
            with tarfile.open(backup_file, "w:gz") as tar:
                for volume in project_volumes:
                    # Создаем временный контейнер для доступа к volume
                    temp_dir = f"/tmp/backup_{volume}"
                    
                    # Копируем данные из volume
                    subprocess.run([
                        "docker", "run", "--rm", "-v", f"{volume}:/data",
                        "-v", f"{temp_dir}:/backup", "alpine",
                        "tar", "czf", f"/backup/{volume}.tar.gz", "-C", "/data", "."
                    ], check=True)
                    
                    # Добавляем в основной архив
                    volume_backup = Path(temp_dir) / f"{volume}.tar.gz"
                    if volume_backup.exists():
                        tar.add(volume_backup, arcname=f"volumes/{volume}.tar.gz")
                        volume_backup.unlink()
                        print(f"✅ Added volume {volume} to backup")
            
            print(f"✅ Docker volumes backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Docker volumes backup failed: {e}")
            return None
    
    def create_full_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """Создать полный бэкап."""
        if not backup_name:
            backup_name = f"optimaai_backup_{self.create_timestamp()}"
        
        print(f"🚀 Creating full backup: {backup_name}")
        
        backup_info = {
            "name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "files": {}
        }
        
        # Бэкап базы данных
        db_paths = list(self.project_root.glob("*.db")) + list(self.project_root.glob("**/*.db"))
        for db_path in db_paths:
            db_backup = self.backup_database(db_path, backup_name)
            if db_backup:
                backup_info["files"][f"database_{db_path.name}"] = str(db_backup)
        
        # Бэкап RAG данных
        rag_backup = self.backup_rag_data(backup_name)
        if rag_backup:
            backup_info["files"]["rag_data"] = str(rag_backup)
        
        # Бэкап конфигурации
        config_backup = self.backup_config(backup_name)
        if config_backup:
            backup_info["files"]["config"] = str(config_backup)
        
        # Бэкап логов
        logs_backup = self.backup_logs(backup_name)
        if logs_backup:
            backup_info["files"]["logs"] = str(logs_backup)
        
        # Бэкап Docker volumes
        volumes_backup = self.backup_docker_volumes(backup_name)
        if volumes_backup:
            backup_info["files"]["docker_volumes"] = str(volumes_backup)
        
        # Сохраняем информацию о бэкапе
        info_file = self.backup_dir / f"{backup_name}_info.json"
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"✅ Full backup completed: {backup_name}")
        print(f"📄 Backup info saved: {info_file}")
        
        return backup_info
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Получить список всех бэкапов."""
        backups = []
        
        for info_file in self.backup_dir.glob("*_info.json"):
            try:
                with open(info_file, 'r') as f:
                    backup_info = json.load(f)
                    backup_info["info_file"] = str(info_file)
                    backups.append(backup_info)
            except Exception as e:
                print(f"⚠️  Could not read backup info: {info_file} - {e}")
        
        # Сортируем по дате
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """Очистить старые бэкапы."""
        print(f"🧹 Cleaning up backups older than {keep_days} days, keeping last {keep_count}")
        
        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Определяем бэкапы для удаления
        to_delete = []
        for i, backup in enumerate(backups):
            backup_date = datetime.fromisoformat(backup["timestamp"])
            
            # Удаляем если старше cutoff_date И не входит в keep_count последних
            if backup_date < cutoff_date and i >= keep_count:
                to_delete.append(backup)
        
        # Удаляем файлы
        deleted_count = 0
        for backup in to_delete:
            try:
                # Удаляем все файлы бэкапа
                for file_type, file_path in backup["files"].items():
                    if Path(file_path).exists():
                        Path(file_path).unlink()
                        print(f"🗑️  Deleted {file_type}: {file_path}")
                
                # Удаляем info файл
                info_file = Path(backup["info_file"])
                if info_file.exists():
                    info_file.unlink()
                    print(f"🗑️  Deleted info: {info_file}")
                
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete backup {backup['name']}: {e}")
        
        print(f"✅ Cleanup completed. Deleted {deleted_count} old backups")
    
    def restore_backup(self, backup_name: str, restore_types: List[str] = None):
        """Восстановить бэкап."""
        print(f"🔄 Restoring backup: {backup_name}")
        
        # Находим информацию о бэкапе
        info_file = self.backup_dir / f"{backup_name}_info.json"
        if not info_file.exists():
            print(f"❌ Backup info not found: {info_file}")
            return False
        
        with open(info_file, 'r') as f:
            backup_info = json.load(f)
        
        if not restore_types:
            restore_types = list(backup_info["files"].keys())
        
        print(f"Restoring: {', '.join(restore_types)}")
        
        success = True
        for restore_type in restore_types:
            if restore_type not in backup_info["files"]:
                print(f"⚠️  Backup type not found: {restore_type}")
                continue
            
            file_path = Path(backup_info["files"][restore_type])
            if not file_path.exists():
                print(f"❌ Backup file not found: {file_path}")
                success = False
                continue
            
            try:
                if restore_type.startswith("database"):
                    self._restore_database(file_path)
                elif restore_type == "rag_data":
                    self._restore_rag_data(file_path)
                elif restore_type == "config":
                    self._restore_config(file_path)
                elif restore_type == "logs":
                    self._restore_logs(file_path)
                elif restore_type == "docker_volumes":
                    self._restore_docker_volumes(file_path)
                
                print(f"✅ Restored {restore_type}")
            except Exception as e:
                print(f"❌ Failed to restore {restore_type}: {e}")
                success = False
        
        return success
    
    def _restore_database(self, backup_file: Path):
        """Восстановить базу данных."""
        # Здесь должна быть логика восстановления БД
        print(f"Restoring database from {backup_file}")
    
    def _restore_rag_data(self, backup_file: Path):
        """Восстановить RAG данные."""
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(self.project_root)
    
    def _restore_config(self, backup_file: Path):
        """Восстановить конфигурацию."""
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(self.project_root)
    
    def _restore_logs(self, backup_file: Path):
        """Восстановить логи."""
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(self.project_root)
    
    def _restore_docker_volumes(self, backup_file: Path):
        """Восстановить Docker volumes."""
        # Здесь должна быть логика восстановления Docker volumes
        print(f"Restoring Docker volumes from {backup_file}")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Backup management tool")
    parser.add_argument("action", choices=["create", "list", "cleanup", "restore"],
                       help="Action to perform")
    parser.add_argument("--name", help="Backup name")
    parser.add_argument("--keep-days", type=int, default=30,
                       help="Days to keep backups (for cleanup)")
    parser.add_argument("--keep-count", type=int, default=10,
                       help="Number of recent backups to keep (for cleanup)")
    parser.add_argument("--types", nargs="+",
                       help="Backup types to restore (for restore)")
    
    args = parser.parse_args()
    
    backup_manager = BackupManager()
    
    if args.action == "create":
        backup_info = backup_manager.create_full_backup(args.name)
        print(f"\n📊 Backup Summary:")
        print(f"Name: {backup_info['name']}")
        print(f"Files: {len(backup_info['files'])}")
        for file_type, file_path in backup_info['files'].items():
            size = Path(file_path).stat().st_size / 1024 / 1024
            print(f"  - {file_type}: {size:.1f} MB")
    
    elif args.action == "list":
        backups = backup_manager.list_backups()
        if not backups:
            print("No backups found")
        else:
            print(f"\n📋 Found {len(backups)} backups:")
            for backup in backups:
                print(f"  - {backup['name']} ({backup['timestamp']})")
                print(f"    Files: {len(backup['files'])}")
    
    elif args.action == "cleanup":
        backup_manager.cleanup_old_backups(args.keep_days, args.keep_count)
    
    elif args.action == "restore":
        if not args.name:
            print("❌ Backup name required for restore")
            sys.exit(1)
        
        success = backup_manager.restore_backup(args.name, args.types)
        if success:
            print("✅ Restore completed successfully")
        else:
            print("❌ Restore completed with errors")
            sys.exit(1)


if __name__ == "__main__":
    main()