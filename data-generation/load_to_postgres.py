import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername="postgresql+pg8000",
    username="postgres",
    password="postgres",
    host="127.0.0.1",
    port=5433,
    database="retaildb"
)

engine = create_engine(url)

tables = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES"
]

for table in tables:
    file = f"output/csv/{table}.csv"

    print(f"Cargando {table}...")

    df = pd.read_csv(file)

    df.to_sql(
        table,
        engine,
        if_exists="replace",
        index=False,
        chunksize=10000
    )

    print(f"{table} cargada")

print("Carga terminada")