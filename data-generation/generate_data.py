import os
import yaml
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("es_CO")

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

SEED = config["seed"]
random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)

CSV_PATH = "output/csv"
PARQUET_PATH = "output/parquet"

os.makedirs(CSV_PATH, exist_ok=True)
os.makedirs(PARQUET_PATH, exist_ok=True)

start_date = datetime.fromisoformat(config["date_range"]["start"])
end_date = datetime.fromisoformat(config["date_range"]["end"])


def random_date():
    days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, days))


def save_table(df, name):
    df.to_csv(f"{CSV_PATH}/{name}.csv", index=False, encoding="utf-8")
    df.to_parquet(f"{PARQUET_PATH}/{name}.parquet", index=False)
    print(f"{name}: {len(df)} registros generados")


# 1. PROVEEDORES
proveedores = pd.DataFrame({
    "id_proveedor": range(1, 801),
    "razon_social": [fake.company() for _ in range(800)],
    "pais_origen": np.random.choice(["Colombia", "Mexico", "Chile", "Peru", "Ecuador"], 800),
    "tiempo_repo_dias": np.random.randint(1, 15, 800),
    "calificacion_calidad": np.round(np.random.uniform(3.0, 5.0, 800), 2),
    "activo": np.random.choice([True, False], 800, p=[0.95, 0.05])
})
save_table(proveedores, "MSTR_PROVEEDORES")


# 2. ARTICULOS
categorias = [
    "Alimentos y bebidas",
    "Cuidado personal e higiene",
    "Hogar y limpieza",
    "Electronica y tecnologia",
    "Ropa y calzado basico",
    "Bebes y maternidad"
]

articulos = pd.DataFrame({
    "art_id": range(1, 5001),
    "cod_barra": [fake.ean(length=13) for _ in range(5000)],
    "desc_art": [fake.word().capitalize() + " " + fake.word() for _ in range(5000)],
    "id_categ_n1": np.random.choice(categorias, 5000),
    "id_categ_n2": np.random.randint(1, 20, 5000),
    "id_categ_n3": np.random.randint(1, 100, 5000),
    "id_proveedor": np.random.choice(proveedores["id_proveedor"], 5000),
    "precio_lista": np.round(np.random.uniform(3000, 900000, 5000), 2),
    "peso_kg": np.round(np.random.uniform(0.1, 25, 5000), 2),
    "unid_medida": np.random.choice(["UND", "KG", "LT", "PAQ"], 5000),
    "activo": np.random.choice([True, False], 5000, p=[0.96, 0.04]),
    "fec_alta": [random_date().date() for _ in range(5000)]
})
save_table(articulos, "MSTR_ARTICULOS")


# 3. TIENDAS
tiendas = pd.DataFrame({
    "id_tienda": range(1, 151),
    "nom_tienda": [f"Tienda {i}" for i in range(1, 151)],
    "tipo_tienda": np.random.choice(["Hipermercado", "Supermercado", "Conveniencia", "Ecommerce"], 150),
    "id_ciudad": np.random.randint(1, 30, 150),
    "id_pais": np.random.choice(["CO", "MX", "CL", "PE", "EC"], 150),
    "metros_cuadrados": np.random.randint(80, 8000, 150),
    "activo": np.random.choice([True, False], 150, p=[0.94, 0.06]),
    "fec_apertura": [random_date().date() for _ in range(150)]
})
save_table(tiendas, "MSTR_TIENDAS")


# 4. MIEMBROS
miembros = pd.DataFrame({
    "id_miembro": range(1, 50001),
    "fec_registro": [random_date().date() for _ in range(50000)],
    "id_ciudad": np.random.randint(1, 30, 50000),
    "genero": np.random.choice(["M", "F", None], 50000, p=[0.48, 0.47, 0.05]),
    "rango_edad": np.random.choice(["18-25", "26-35", "36-45", "46-60", "60+"], 50000),
    "canal_pref": np.random.choice(["Tienda", "Web", "App", "Marketplace"], 50000),
    "activo": np.random.choice([True, False], 50000, p=[0.92, 0.08]),
    "fec_ultima_compra": [random_date().date() for _ in range(50000)]
})
save_table(miembros, "CRM_MIEMBROS")


# 5. VENTAS
n_ventas = 1_000_000
ventas_fechas = [random_date() for _ in range(n_ventas)]

ventas = pd.DataFrame({
    "id_trans": range(1, n_ventas + 1),
    "id_miembro": np.random.choice(miembros["id_miembro"], n_ventas),
    "id_tienda": np.random.choice(tiendas["id_tienda"], n_ventas),
    "art_id": np.random.choice(articulos["art_id"], n_ventas),
    "fec_trans": [f.date() for f in ventas_fechas],
    "hra_trans": [f"{random.randint(8, 22):02d}:{random.randint(0, 59):02d}:00" for _ in range(n_ventas)],
    "qty_vendida": np.random.randint(1, 8, n_ventas),
    "precio_unitario_venta": np.round(np.random.uniform(3000, 900000, n_ventas), 2),
    "descuento_aplicado": np.round(np.random.uniform(0, 50000, n_ventas), 2),
    "tipo_pago": np.random.choice(["Efectivo", "Tarjeta", "PSE", "Nequi", "Transferencia"], n_ventas),
    "canal_venta": np.random.choice(["Tienda", "Web", "App", "Marketplace"], n_ventas)
})
save_table(ventas, "TRANS_VENTAS")


# 6. INVENTARIO
n_stock = 750_000
stock = pd.DataFrame({
    "id_snapshot": range(1, n_stock + 1),
    "art_id": np.random.choice(articulos["art_id"], n_stock),
    "id_tienda": np.random.choice(tiendas["id_tienda"], n_stock),
    "fec_snapshot": [random_date().date() for _ in range(n_stock)],
    "stock_fisico": np.random.randint(0, 500, n_stock),
    "stock_transito": np.random.randint(0, 200, n_stock),
    "stock_reservado": np.random.randint(0, 80, n_stock),
    "stock_minimo_config": np.random.randint(5, 60, n_stock),
    "stock_maximo_config": np.random.randint(100, 800, n_stock)
})
save_table(stock, "INV_STOCK_DIARIO")


# 7. DEVOLUCIONES
n_dev = 50_000
devoluciones = pd.DataFrame({
    "id_devolucion": range(1, n_dev + 1),
    "id_trans_origen": np.random.choice(ventas["id_trans"], n_dev),
    "art_id": np.random.choice(articulos["art_id"], n_dev),
    "id_tienda": np.random.choice(tiendas["id_tienda"], n_dev),
    "fec_devolucion": [random_date().date() for _ in range(n_dev)],
    "qty_devuelta": np.random.randint(1, 4, n_dev),
    "motivo_cod": np.random.choice(["DEFECTO", "TALLA", "GARANTIA", "CLIENTE", "OTRO"], n_dev),
    "canal_devolucion": np.random.choice(["Tienda", "Web", "App", "Marketplace"], n_dev),
    "estado_devolucion": np.random.choice(["Aprobada", "Rechazada", "Pendiente"], n_dev),
    "vr_reembolso": np.round(np.random.uniform(3000, 500000, n_dev), 2)
})
save_table(devoluciones, "POST_DEVOLUCIONES")

print("Proceso finalizado correctamente.")