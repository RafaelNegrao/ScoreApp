import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect("db.db")
cursor = conn.cursor()

print("=== REMOVENDO COLUNA DUPLICADA change_by ===")

try:
    # SQLite não suporta DROP COLUMN diretamente, então vamos recriar a tabela
    print("1. Criando backup da tabela...")
    cursor.execute("""
        CREATE TABLE supplier_score_records_table_backup AS 
        SELECT id, supplier_id, supplier_name, month, year, quality_package, quality_pickup, 
               nil, otif, total_score, comment, register_date, registered_by, change_date, changed_by
        FROM supplier_score_records_table
    """)
    
    print("2. Removendo tabela original...")
    cursor.execute("DROP TABLE supplier_score_records_table")
    
    print("3. Recriando tabela sem coluna duplicada...")
    cursor.execute("""
        CREATE TABLE supplier_score_records_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id TEXT,
            supplier_name TEXT,
            month TEXT,
            year TEXT,
            quality_package TEXT,
            quality_pickup TEXT,
            nil REAL,
            otif REAL,
            total_score TEXT,
            comment TEXT,
            register_date TEXT,
            registered_by TEXT,
            change_date TEXT,
            changed_by TEXT
        )
    """)
    
    print("4. Restaurando dados...")
    cursor.execute("""
        INSERT INTO supplier_score_records_table 
        SELECT * FROM supplier_score_records_table_backup
    """)
    
    print("5. Removendo backup...")
    cursor.execute("DROP TABLE supplier_score_records_table_backup")
    
    conn.commit()
    print("✅ Coluna change_by removida com sucesso!")
    
    # Verificar estrutura final
    print("\n=== ESTRUTURA FINAL DA TABELA ===")
    cursor.execute("PRAGMA table_info(supplier_score_records_table)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()

conn.close()