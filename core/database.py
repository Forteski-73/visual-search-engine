# core/database.py
from mysql.connector import pooling

from config import settings

# Configura os dados de acesso em um dicionário
db_config = {
    "host": settings.DB_HOST,
    "database": settings.DB_NAME,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
}

# Cria o Pool de Conexões (será iniciado apenas UMA vez quando a API subir)
# pool_size=32 significa que ele pode abrir até 32 conexões simultâneas e reutilizá-las
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,
    **db_config,
)


def get_conn():
    return connection_pool.get_connection()
