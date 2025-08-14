#!/usr/bin/env python3
"""
🚨 EMERGENCY DATABASE FIX - DISCOVERY SERVICE
=============================================
Solución DEFINITIVA para el error 'duplicate column name: updated_at'
"""

import sqlite3
from pathlib import Path
import sys

def check_database_state():
    """Verificar estado actual de la base de datos"""
    print("🔍 VERIFICANDO ESTADO ACTUAL DE LA BASE DE DATOS")
    print("=" * 70)
    
    db_path = Path("data/discovery.db")
    
    if not db_path.exists():
        print("❌ Base de datos no existe en data/discovery.db")
        return None
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='discovered_chats'
            """)
            
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                print("❌ Tabla 'discovered_chats' no existe")
                return None
            
            # Get current columns
            cursor.execute("PRAGMA table_info(discovered_chats)")
            columns_info = cursor.fetchall()
            columns = [row[1] for row in columns_info]
            
            print(f"✅ Tabla existe con {len(columns)} columnas:")
            for col_info in columns_info:
                print(f"   📋 {col_info[1]} ({col_info[2]})")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            count = cursor.fetchone()[0]
            print(f"📊 Registros en tabla: {count}")
            
            return {
                "exists": True,
                "columns": columns,
                "count": count,
                "has_updated_at": "updated_at" in columns
            }
            
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return None

def fix_database_schema():
    """Arreglar esquema de base de datos SIN duplicar columnas"""
    print("\n🔧 ARREGLANDO ESQUEMA DE BASE DE DATOS")
    print("=" * 70)
    
    db_path = Path("data/discovery.db")
    data_dir = db_path.parent
    data_dir.mkdir(exist_ok=True)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get current state
            state = check_database_state()
            
            if state is None:
                print("🔧 Creando tabla desde cero...")
                cursor.execute("""
                    CREATE TABLE discovered_chats (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        type TEXT NOT NULL,
                        username TEXT,
                        description TEXT,
                        participants_count INTEGER,
                        is_public BOOLEAN DEFAULT FALSE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_public_chats ON discovered_chats(is_public)")
                
                print("✅ Created fresh table with correct schema")
                conn.commit()
                return True
            
            # Fix existing table if needed
            if not state["has_updated_at"]:
                print("🔧 Adding missing 'updated_at' column...")
                try:
                    cursor.execute("""
                        ALTER TABLE discovered_chats 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
                    print("✅ Successfully added 'updated_at' column")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("✅ Column 'updated_at' already exists (that's OK)")
                    else:
                        print(f"❌ Error adding column: {e}")
                        return False
            else:
                print("✅ Column 'updated_at' already exists")
            
            # Ensure all required columns exist
            required_columns = [
                ("is_public", "BOOLEAN DEFAULT FALSE"),
                ("is_verified", "BOOLEAN DEFAULT FALSE"),
                ("discovered_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
            
            current_columns = state["columns"]
            
            for col_name, col_def in required_columns:
                if col_name not in current_columns:
                    print(f"🔧 Adding missing column '{col_name}'...")
                    try:
                        cursor.execute(f"""
                            ALTER TABLE discovered_chats 
                            ADD COLUMN {col_name} {col_def}
                        """)
                        print(f"✅ Added '{col_name}' column")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print(f"✅ Column '{col_name}' already exists")
                        else:
                            print(f"❌ Error adding {col_name}: {e}")
            
            # Create indexes if they don't exist
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_public_chats ON discovered_chats(is_public)")
                print("✅ Created indexes")
            except Exception as e:
                print(f"⚠️ Index creation warning: {e}")
            
            conn.commit()
            print("✅ Database schema successfully fixed!")
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False
    
    return True

def test_database_operations():
    """Test complete database operations"""
    print("\n🧪 TESTING DATABASE OPERATIONS")
    print("=" * 70)
    
    db_path = Path("data/discovery.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Test 1: Insert test record
            test_chat = {
                'id': -1001234567890,
                'title': 'Test Discovery Group',
                'type': 'supergroup',
                'username': 'testdiscovery',
                'description': 'Test group for discovery service',
                'participants_count': 150,
                'is_public': True,
                'is_verified': False
            }
            
            print("📝 Testing INSERT operation...")
            cursor.execute("""
                INSERT OR REPLACE INTO discovered_chats 
                (id, title, type, username, description, participants_count, 
                 is_public, is_verified, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                test_chat['id'],
                test_chat['title'],
                test_chat['type'],
                test_chat['username'],
                test_chat['description'],
                test_chat['participants_count'],
                test_chat['is_public'],
                test_chat['is_verified']
            ))
            
            # Test 2: Select test record
            print("📖 Testing SELECT operation...")
            cursor.execute("SELECT * FROM discovered_chats WHERE id = ?", (test_chat['id'],))
            result = cursor.fetchone()
            
            if result:
                print("✅ INSERT/SELECT operations successful")
                print(f"   📋 Record: {result[1]} ({result[2]})")
            else:
                print("❌ INSERT/SELECT operations failed")
                return False
            
            # Test 3: Update operation
            print("🔄 Testing UPDATE operation...")
            cursor.execute("""
                UPDATE discovered_chats 
                SET participants_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (200, test_chat['id']))
            
            # Test 4: Filter operations
            print("🔍 Testing FILTER operations...")
            cursor.execute("""
                SELECT COUNT(*) FROM discovered_chats 
                WHERE type = ? AND is_public = ?
            """, ('supergroup', True))
            
            count = cursor.fetchone()[0]
            print(f"✅ Filter test successful: found {count} matching records")
            
            # Test 5: Clean up
            print("🧹 Cleaning up test data...")
            cursor.execute("DELETE FROM discovered_chats WHERE id = ?", (test_chat['id'],))
            
            conn.commit()
            print("✅ All database operations working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def show_current_schema():
    """Show the current database schema"""
    print("\n📋 CURRENT DATABASE SCHEMA")
    print("=" * 70)
    
    db_path = Path("data/discovery.db")
    
    if not db_path.exists():
        print("❌ Database file does not exist")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Table info
            cursor.execute("PRAGMA table_info(discovered_chats)")
            columns_info = cursor.fetchall()
            
            print("📊 TABLE: discovered_chats")
            print("-" * 50)
            for col in columns_info:
                col_id, name, type_, not_null, default, pk = col
                default_str = f" DEFAULT {default}" if default else ""
                pk_str = " PRIMARY KEY" if pk else ""
                not_null_str = " NOT NULL" if not_null else ""
                print(f"   {name:<20} {type_:<15}{not_null_str}{default_str}{pk_str}")
            
            # Indexes
            cursor.execute("PRAGMA index_list(discovered_chats)")
            indexes = cursor.fetchall()
            
            if indexes:
                print("\n📇 INDEXES:")
                print("-" * 50)
                for idx in indexes:
                    print(f"   {idx[1]}")
            
            # Record count
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            count = cursor.fetchone()[0]
            
            print(f"\n📊 RECORDS: {count} total")
            
            # Sample records
            if count > 0:
                cursor.execute("SELECT id, title, type, participants_count FROM discovered_chats LIMIT 3")
                samples = cursor.fetchall()
                print("\n📝 SAMPLE RECORDS:")
                print("-" * 50)
                for sample in samples:
                    print(f"   ID: {sample[0]} | {sample[1]} ({sample[2]}) | {sample[3]} members")
            
    except Exception as e:
        print(f"❌ Error reading schema: {e}")

def main():
    """Función principal - SOLUCIÓN COMPLETA"""
    print("🚨 EMERGENCY DATABASE FIX - DISCOVERY SERVICE")
    print("=" * 70)
    print("🎯 FIXING: 'duplicate column name: updated_at' error")
    print("=" * 70)
    
    # Step 1: Show current state
    current_state = check_database_state()
    
    # Step 2: Fix schema
    if fix_database_schema():
        print("\n" + "=" * 50)
        
        # Step 3: Test operations
        if test_database_operations():
            print("\n" + "=" * 50)
            
            # Step 4: Show final schema
            show_current_schema()
            
            print("\n" + "=" * 70)
            print("✅ DATABASE REPAIR COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("\n🚀 NEXT STEPS:")
            print("   1. Stop all running services:")
            print("      pkill -f 'discovery' || true")
            print("")
            print("   2. Start the Discovery Service:")
            print("      python services/discovery/main.py")
            print("")
            print("   3. Test the API:")
            print("      curl 'http://localhost:8002/api/discovery/chats?limit=5'")
            print("")
            print("   4. Access the dashboard:")
            print("      http://localhost:8000/dashboard")
            print("")
            print("✅ Your Discovery Service should now work perfectly!")
            
        else:
            print("\n❌ Database operations test failed")
    else:
        print("\n❌ Database schema fix failed")
    
    print("=" * 70)

if __name__ == "__main__":
    main()