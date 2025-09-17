import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect("db.db")
cursor = conn.cursor()

# Verificar a estrutura da tabela
print("=== ESTRUTURA DA TABELA ===")
cursor.execute("PRAGMA table_info(supplier_score_records_table)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n=== ÚLTIMOS 5 REGISTROS ===")
cursor.execute("SELECT * FROM supplier_score_records_table ORDER BY id DESC LIMIT 5")
records = cursor.fetchall()

if records:
    # Obter nomes das colunas
    column_names = [description[0] for description in cursor.description]
    
    for record in records:
        print(f"\nRegistro ID: {record[0]}")
        for i, value in enumerate(record):
            print(f"  {column_names[i]}: {value}")
else:
    print("Nenhum registro encontrado")

print(f"\n=== TOTAL DE REGISTROS ===")
cursor.execute("SELECT COUNT(*) FROM supplier_score_records_table")
total = cursor.fetchone()[0]
print(f"Total de registros: {total}")

# Verificar se há registros recentes (últimos 10 minutos)
print("\n=== REGISTROS RECENTES ===")
cursor.execute("""
    SELECT id, supplier_id, supplier_name, register_date, registered_by, changed_by, comment, total_score
    FROM supplier_score_records_table 
    WHERE register_date >= datetime('now', '-10 minutes')
    ORDER BY register_date DESC
""")
recent = cursor.fetchall()

if recent:
    print("Registros inseridos nos últimos 10 minutos:")
    for rec in recent:
        print(f"  ID: {rec[0]}, Supplier: {rec[1]}, Nome: {rec[2]}, Data: {rec[3]}")
        print(f"    Registrado por: {rec[4]}, Alterado por: {rec[5]}")
        print(f"    Comentário: {rec[6]}, Score: {rec[7]}")
else:
    print("Nenhum registro recente encontrado")

conn.close()