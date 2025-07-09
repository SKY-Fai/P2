
#!/usr/bin/env python3
"""
Automated Backup Manager for F-AI Accountant
Handles database backups with cloud storage integration
"""

import os
import sys
import logging
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    """Automated backup management system"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.neon_url = os.environ.get("NEON_DATABASE_URL")
        self.sqlite_path = "instance/accufin360.db"
        
    def create_postgres_backup(self):
        """Create PostgreSQL backup using pg_dump"""
        if not self.neon_url:
            logger.error("NEON_DATABASE_URL not configured")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"fai_neon_backup_{timestamp}.sql.gz"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Extract connection details from URL
            from urllib.parse import urlparse
            parsed = urlparse(self.neon_url)
            
            # Create pg_dump command
            cmd = [
                "pg_dump",
                f"--host={parsed.hostname}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path[1:]}",  # Remove leading slash
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges"
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env["PGPASSWORD"] = parsed.password
            
            # Run pg_dump and compress
            with gzip.open(backup_path, 'wt') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
            
            if result.returncode == 0:
                logger.info(f"✅ PostgreSQL backup created: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                if backup_path.exists():
                    backup_path.unlink()
                return None
                
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            return None
    
    def create_sqlite_backup(self):
        """Create SQLite backup"""
        if not os.path.exists(self.sqlite_path):
            logger.warning("SQLite database not found")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"fai_sqlite_backup_{timestamp}.db.gz"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy and compress SQLite database
            with open(self.sqlite_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"✅ SQLite backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return None
    
    def cleanup_old_backups(self, retention_days=30):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            deleted_count = 0
            for backup_file in self.backup_dir.glob("*.gz"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"🗑️  Deleted old backup: {backup_file.name}")
                    deleted_count += 1
            
            logger.info(f"✅ Cleanup completed: {deleted_count} old backups removed")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def create_backup_metadata(self, backup_path):
        """Create metadata file for backup"""
        if not backup_path:
            return
            
        metadata = {
            "backup_date": datetime.now().isoformat(),
            "backup_file": os.path.basename(backup_path),
            "database_type": "postgresql" if "neon" in backup_path else "sqlite",
            "file_size": os.path.getsize(backup_path),
            "version": "2.0.0"
        }
        
        metadata_path = Path(backup_path).with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def run_backup(self):
        """Run complete backup process"""
        logger.info("🔄 Starting automated backup process...")
        
        backup_paths = []
        
        # Try PostgreSQL backup first
        postgres_backup = self.create_postgres_backup()
        if postgres_backup:
            backup_paths.append(postgres_backup)
            self.create_backup_metadata(postgres_backup)
        
        # Fallback to SQLite backup
        sqlite_backup = self.create_sqlite_backup()
        if sqlite_backup:
            backup_paths.append(sqlite_backup)
            self.create_backup_metadata(sqlite_backup)
        
        # Cleanup old backups
        self.cleanup_old_backups()
        
        if backup_paths:
            logger.info(f"✅ Backup process completed: {len(backup_paths)} backups created")
            return backup_paths
        else:
            logger.error("❌ No backups were created")
            return []

def main():
    """Main backup function"""
    backup_manager = BackupManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup_paths = backup_manager.run_backup()
            if backup_paths:
                for path in backup_paths:
                    print(f"Backup created: {path}")
            else:
                sys.exit(1)
                
        elif command == "cleanup":
            retention_days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            backup_manager.cleanup_old_backups(retention_days)
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Usage: python backup_manager.py <command>")
        print("Commands:")
        print("  backup  - Create database backup")
        print("  cleanup [days] - Clean up old backups (default: 30 days)")
        sys.exit(1)

if __name__ == "__main__":
    main()
