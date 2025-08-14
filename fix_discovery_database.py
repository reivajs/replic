#!/usr/bin/env python3
"""
🔧 FIX DISCOVERY DATABASE SCHEMA
================================
Arregla el esquema de la base de datos del Discovery Service
"""

import sqlite3
from pathlib import Path

def fix_discovery_database():
    """Arreglar esquema de la base de datos"""
    print("🔧 FIXING DISCOVERY DATABASE SCHEMA")
    print("=" * 50)
    
    # Asegurar que existe el directorio data
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "discovery.db"
    
    try:
        # Conectar a la base de datos
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar si existe la tabla
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='discovered_chats'
            """)
            
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                print("✅ Table 'discovered_chats' exists")
                
                # Verificar columnas existentes
                cursor.execute("PRAGMA table_info(discovered_chats)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"📋 Existing columns: {', '.join(columns)}")
                
                # Verificar si falta la columna updated_at
                if 'updated_at' not in columns:
                    print("🔧 Adding missing 'updated_at' column...")
                    cursor.execute("""
                        ALTER TABLE discovered_chats 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
                    print("✅ Added 'updated_at' column")
                else:
                    print("✅ Column 'updated_at' already exists")
                
                # Verificar si necesitamos otras columnas faltantes
                required_columns = {
                    'id': 'INTEGER PRIMARY KEY',
                    'title': 'TEXT NOT NULL',
                    'type': 'TEXT NOT NULL',
                    'username': 'TEXT',
                    'description': 'TEXT',
                    'participants_count': 'INTEGER',
                    'is_public': 'BOOLEAN DEFAULT FALSE',
                    'is_verified': 'BOOLEAN DEFAULT FALSE',
                    'discovered_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                }
                
                for col_name, col_def in required_columns.items():
                    if col_name not in columns:
                        print(f"🔧 Adding missing column '{col_name}'...")
                        cursor.execute(f"""
                            ALTER TABLE discovered_chats 
                            ADD COLUMN {col_name} {col_def}
                        """)
                        print(f"✅ Added '{col_name}' column")
                
            else:
                print("🔧 Creating 'discovered_chats' table...")
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
                print("✅ Created 'discovered_chats' table")
            
            # Crear índices si no existen
            indexes = [
                ("idx_chat_type", "CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type)"),
                ("idx_public_chats", "CREATE INDEX IF NOT EXISTS idx_public_chats ON discovered_chats(is_public)"),
                ("idx_updated_at", "CREATE INDEX IF NOT EXISTS idx_updated_at ON discovered_chats(updated_at)")
            ]
            
            for index_name, index_sql in indexes:
                cursor.execute(index_sql)
                print(f"✅ Created index: {index_name}")
            
            # Verificar esquema final
            cursor.execute("PRAGMA table_info(discovered_chats)")
            final_columns = [row[1] for row in cursor.fetchall()]
            print(f"\n📋 Final schema columns: {', '.join(final_columns)}")
            
            # Contar registros existentes
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            count = cursor.fetchone()[0]
            print(f"📊 Records in database: {count}")
            
            conn.commit()
            print("\n✅ Database schema fixed successfully!")
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False
    
    return True

def test_database():
    """Test que la base de datos funciona correctamente"""
    print("\n🧪 TESTING DATABASE")
    print("-" * 30)
    
    db_path = Path("data/discovery.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Test insert
            test_chat = {
                'id': -1001234567890,
                'title': 'Test Group',
                'type': 'supergroup',
                'username': 'testgroup',
                'description': 'Test description',
                'participants_count': 100,
                'is_public': True,
                'is_verified': False
            }
            
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
            
            # Test select
            cursor.execute("SELECT * FROM discovered_chats WHERE id = ?", (test_chat['id'],))
            result = cursor.fetchone()
            
            if result:
                print("✅ Test insert/select successful")
                
                # Clean up test data
                cursor.execute("DELETE FROM discovered_chats WHERE id = ?", (test_chat['id'],))
                print("✅ Test data cleaned up")
                
                conn.commit()
                return True
            else:
                print("❌ Test insert/select failed")
                return False
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def clean_old_data():
    """Limpiar datos corruptos si existen"""
    print("\n🧹 CLEANING OLD DATA")
    print("-" * 30)
    
    db_path = Path("data/discovery.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Contar registros antes
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            before_count = cursor.fetchone()[0]
            
            # Eliminar registros con campos NULL críticos
            cursor.execute("""
                DELETE FROM discovered_chats 
                WHERE title IS NULL OR type IS NULL
            """)
            
            # Contar registros después
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            after_count = cursor.fetchone()[0]
            
            deleted_count = before_count - after_count
            
            if deleted_count > 0:
                print(f"🗑️ Cleaned {deleted_count} corrupted records")
            else:
                print("✅ No corrupted records found")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error cleaning data: {e}")

def main():
    """Función principal"""
    print("🔧 DISCOVERY DATABASE REPAIR TOOL")
    print("=" * 70)
    
    # Step 1: Fix database schema
    if fix_discovery_database():
        print("\n" + "=" * 50)
        
        # Step 2: Clean old data
        clean_old_data()
        
        # Step 3: Test database
        if test_database():
            print("\n✅ DATABASE REPAIR COMPLETED SUCCESSFULLY!")
            print("\n🚀 Next steps:")
            print("   1. Restart Discovery Service: python services/discovery/main.py")
            print("   2. Check for errors in the log")
            print("   3. Test endpoint: curl 'http://localhost:8002/api/discovery/chats?limit=5'")
            print("   4. Access Groups Hub: http://localhost:8000/groups")
        else:
            print("\n❌ Database test failed - manual intervention needed")
    else:
        print("\n❌ Database repair failed")
    
    print("=" * 70)

if __name__ == "__main__":
    main()