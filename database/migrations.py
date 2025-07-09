
#!/usr/bin/env python3
"""
Database Migration System for F-AI Accountant
Handles migrations between SQLite and PostgreSQL (Neon DB)
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handle database migrations"""
    
    def __init__(self, source_url, target_url):
        self.source_url = source_url
        self.target_url = target_url
        self.source_engine = None
        self.target_engine = None
    
    def connect_databases(self):
        """Connect to source and target databases"""
        try:
            self.source_engine = create_engine(self.source_url)
            self.target_engine = create_engine(
                self.target_url,
                pool_pre_ping=True,
                connect_args={"sslmode": "require"} if "postgresql" in self.target_url else {}
            )
            
            # Test connections
            with self.source_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            with self.target_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connections established")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_table_list(self, engine):
        """Get list of tables from database"""
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    def migrate_table_data(self, table_name):
        """Migrate data from one table to another"""
        try:
            # Read data from source
            with self.source_engine.connect() as source_conn:
                df = pd.read_sql_table(table_name, source_conn)
            
            if df.empty:
                logger.info(f"Table {table_name} is empty, skipping data migration")
                return True
            
            # Write data to target
            with self.target_engine.connect() as target_conn:
                df.to_sql(
                    table_name, 
                    target_conn, 
                    if_exists='append', 
                    index=False,
                    method='multi'
                )
            
            logger.info(f"Migrated {len(df)} records from table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            return False
    
    def run_migration(self):
        """Run complete migration process"""
        logger.info("Starting database migration...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Get tables from source database
            source_tables = self.get_table_list(self.source_engine)
            logger.info(f"Found {len(source_tables)} tables to migrate")
            
            success_count = 0
            total_tables = len(source_tables)
            
            for table_name in source_tables:
                if table_name.startswith('sqlite_'):
                    continue  # Skip SQLite system tables
                
                logger.info(f"Migrating table: {table_name}")
                if self.migrate_table_data(table_name):
                    success_count += 1
                else:
                    logger.warning(f"Failed to migrate table: {table_name}")
            
            logger.info(f"Migration completed: {success_count}/{total_tables} tables migrated successfully")
            return success_count == total_tables
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        finally:
            if self.source_engine:
                self.source_engine.dispose()
            if self.target_engine:
                self.target_engine.dispose()

def create_neon_db_schema(neon_url):
    """Create schema in Neon DB"""
    try:
        engine = create_engine(
            neon_url,
            connect_args={"sslmode": "require"}
        )
        
        # Import models to create tables
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app import db
            db.create_all()
        
        logger.info("Neon DB schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create Neon DB schema: {e}")
        return False

def run_sqlite_to_neon_migration():
    """Run migration from SQLite to Neon DB"""
    sqlite_url = "sqlite:///instance/accufin360.db"
    neon_url = os.environ.get("NEON_DATABASE_URL")
    
    if not neon_url:
        logger.error("NEON_DATABASE_URL environment variable not set")
        return False
    
    logger.info("Starting SQLite to Neon DB migration...")
    
    # First create schema in Neon DB
    if not create_neon_db_schema(neon_url):
        return False
    
    # Then migrate data
    migrator = DatabaseMigrator(sqlite_url, neon_url)
    return migrator.run_migration()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        success = run_sqlite_to_neon_migration()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python migrations.py migrate")
        sys.exit(1)
