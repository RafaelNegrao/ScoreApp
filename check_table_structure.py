import sqlite3
import os

# Conectar ao banco de dados
db_path = os.path.join(os.getcwd(), "db.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar a estrutura da tabela supplier_score_records_table
    cursor.execute("PRAGMA table_info(supplier_score_records_table)")
    columns = cursor.fetchall()
    
    print("🔍 Estrutura da tabela supplier_score_records_table:")
    print("CID | Nome da Coluna | Tipo | Not NULL | Default | Primary Key")
    print("-" * 70)
    
    existing_columns = []
    for col in columns:
        cid, name, col_type, not_null, default_val, primary_key = col
        existing_columns.append(name)
        print(f"{cid:3} | {name:15} | {col_type:8} | {not_null:8} | {str(default_val):7} | {primary_key}")
    
    print("\n🔍 Colunas encontradas:", existing_columns)
    
    # Verificar quais colunas estão faltando
    required_columns = [
        'supplier_id', 'month', 'year', 'otif', 'quality_pickup', 
        'quality_package', 'nil', 'comment', 'total_score', 
        'registered_by', 'register_date', 'change_by', 'supplier_name'
    ]
    
    missing_columns = []
    for req_col in required_columns:
        if req_col not in existing_columns:
            missing_columns.append(req_col)
    
    if missing_columns:
        print(f"\n❌ Colunas que precisam ser adicionadas: {missing_columns}")
        
        # Tentar adicionar as colunas que estão faltando
        for col in missing_columns:
            try:
                if col in ['register_date']:
                    cursor.execute(f"ALTER TABLE supplier_score_records_table ADD COLUMN {col} TEXT")
                elif col in ['total_score']:
                    cursor.execute(f"ALTER TABLE supplier_score_records_table ADD COLUMN {col} REAL")
                elif col in ['supplier_name', 'registered_by', 'comment', 'change_by']:
                    cursor.execute(f"ALTER TABLE supplier_score_records_table ADD COLUMN {col} TEXT")
                else:
                    cursor.execute(f"ALTER TABLE supplier_score_records_table ADD COLUMN {col} REAL")
                
                print(f"✅ Coluna '{col}' adicionada com sucesso!")
                
            except sqlite3.Error as e:
                print(f"❌ Erro ao adicionar coluna '{col}': {e}")
        
        conn.commit()
        print("\n✅ Alterações salvas no banco de dados!")
    else:
        print("\n✅ Todas as colunas necessárias estão presentes!")
        
    # Testar uma consulta SELECT na tabela
    cursor.execute("SELECT COUNT(*) FROM supplier_score_records_table")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total de registros na tabela: {count}")
    
except sqlite3.Error as e:
    print(f"❌ Erro ao acessar o banco de dados: {e}")

finally:
    conn.close()
    print("\n🔒 Conexão com banco de dados fechada")