import psycopg2

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname="discord_db",
    user="postgres",
    password="password",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Exécuter la requête
cur.execute("SELECT * FROM aging_table;")
rows = cur.fetchall()

# Afficher les résultats
print("📊 Contenu de la table 'aging_table' :")
for row in rows:
    print(row)

# Fermer la connexion
cur.close()
conn.close()

