import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Verificar tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tablas en la BD:")
for table in tables:
    print(f"  - {table[0]}")

# Si existe tabla de clientes, listar clientes
if any('client' in str(t) for t in tables):
    print("\nClientes registrados:")
    cursor.execute("SELECT id_key, name, email FROM client")
    clients = cursor.fetchall()
    if clients:
        for client in clients:
            print(f"  ID: {client[0]}, Nombre: {client[1]}, Email: {client[2]}")
    else:
        print("  (ninguno)")

conn.close()
