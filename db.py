"""import os
import mysql.connector
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def get_conn():
    return mysql.connector.connect(
        host    =os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user    =os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
"""

import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# 1. Configura os dados de acesso em um dicionário
db_config = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# 2. Cria o Pool de Conexões (será iniciado apenas UMA vez quando a API subir)
# pool_size=32 significa que ele pode abrir até 32 conexões simultâneas e reutilizá-las
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,
    **db_config
)

# 3. Altera a função para pegar uma conexão que já existe no pool
def get_conn():
    return connection_pool.get_connection()