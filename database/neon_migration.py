
#!/usr/bin/env python3
"""
Neon DB Migration Script for F-AI Accountant
Handles database schema migration and data transfer to Neon PostgreSQL
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from datetime import datetime
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeonDBMigrator:
    """Handle migration to Neon PostgreSQL database"""
    
    def __init__(self):
        self.neon_url = os.environ.get("NEON_DATABASE_URL")
        self.sqlite_path = "instance/accufin360.db"
        
    def validate_connection(self):
        """Validate Neon DB connection"""
        if not self.neon_url:
            logger.error("NEON_DATABASE_URL environment variable not set")
            return False
            
        try:
            engine = create_engine(
                self.neon_url,
                connect_args={"sslmode": "require"}
            )
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to Neon DB: {e}")
            return False
    
    def create_schema(self):
        """Create database schema in Neon DB"""
        try:
            engine = create_engine(
                self.neon_url,
                connect_args={"sslmode": "require"}
            )
            
            # Import models to create tables
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from app import create_app
            
            app = create_app()
            with app.app_context():
                from app import db
                db.create_all()
                logger.info("Schema created successfully in Neon DB")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def migrate_data(self):
        """Migrate data from SQLite to Neon DB"""
        if not os.path.exists(self.sqlite_path):
            logger.warning("No SQLite database found to migrate")
            return True
            
        try:
            # Connect to both databases
            sqlite_engine = create_engine(f"sqlite:///{self.sqlite_path}")
            neon_engine = create_engine(
                self.neon_url,
                connect_args={"sslmode": "require"}
            )
            
            # Get tables from SQLite
            with sqlite_engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
            
            migrated_tables = 0
            for table_name in tables:
                if table_name.startswith('sqlite_'):
                    continue
                    
                try:
                    # Read data from SQLite
                    df = pd.read_sql_table(table_name, sqlite_engine)
                    
                    if not df.empty:
                        # Write to Neon DB
                        df.to_sql(
                            table_name,
                            neon_engine,
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                        logger.info(f"Migrated {len(df)} records from {table_name}")
                    else:
                        logger.info(f"Table {table_name} is empty")
                        
                    migrated_tables += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate table {table_name}: {e}")
            
            logger.info(f"Migration completed: {migrated_tables} tables processed")
            return True
            
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            return False
    
    def run_migration(self):
        """Run complete migration process"""
        logger.info("Starting Neon DB migration...")
        
        # Validate connection
        if not self.validate_connection():
            return False
        
        # Create schema
        if not self.create_schema():
            return False
        
        # Migrate data
        if not self.migrate_data():
            return False
        
        logger.info("✅ Neon DB migration completed successfully")
        return True

def main():
    """Main migration function"""
    migrator = NeonDBMigrator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        success = migrator.run_migration()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python neon_migration.py migrate")
        print("Ensure NEON_DATABASE_URL environment variable is set")
        sys.exit(1)

if __name__ == "__main__":
    main()
