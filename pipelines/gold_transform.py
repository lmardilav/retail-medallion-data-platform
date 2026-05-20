import boto3
import pandas as pd
import numpy as np
from io import BytesIO
from logger_config import logger

s3 = boto3.client("s3")

silver_bucket = "retail-data-engineering-luis-810204248846-silver"
gold_bucket = "retail-data-engineering-luis-810204248846-gold"


def read_parquet(file):
    response = s3.get_object(
        Bucket=silver_bucket,
        Key=f"clean/{file}"
    )
    return pd.read_parquet(BytesIO(response["Body"].read()))


def save_gold(df, name):
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    s3.put_object(
        Bucket=gold_bucket,
        Key=f"analytics/{name}.parquet",
        Body=buffer.getvalue()
    )
    print(f"{name} creada: {len(df)} registros")


# Leer Silver
articulos = read_parquet("MSTR_ARTICULOS.parquet")
proveedores = read_parquet("MSTR_PROVEEDORES.parquet")
tiendas = read_parquet("MSTR_TIENDAS.parquet")
clientes = read_parquet("CRM_MIEMBROS.parquet")
ventas = read_parquet("TRANS_VENTAS.parquet")
inventario = read_parquet("INV_STOCK_DIARIO.parquet")
devoluciones = read_parquet("POST_DEVOLUCIONES.parquet")


# -------------------------
# dim_productos
# -------------------------
dim_productos = articulos.merge(
    proveedores,
    on="id_proveedor",
    how="left"
)

dim_productos["categoria_nivel_1"] = dim_productos["id_categ_n1"]
dim_productos["categoria_nivel_2"] = dim_productos["id_categ_n2"]
dim_productos["categoria_nivel_3"] = dim_productos["id_categ_n3"]
dim_productos["margen_estimado"] = dim_productos["precio_lista"] * 0.30

save_gold(dim_productos, "dim_productos")


# -------------------------
# dim_tiendas
# -------------------------
pais_map = {
    "CO": "Colombia",
    "MX": "Mexico",
    "CL": "Chile",
    "PE": "Peru",
    "EC": "Ecuador"
}

dim_tiendas = tiendas.copy()
dim_tiendas["pais"] = dim_tiendas["id_pais"].map(pais_map)
dim_tiendas["ciudad"] = "Ciudad_" + dim_tiendas["id_ciudad"].astype(str)

dim_tiendas["tipo_tienda"] = dim_tiendas["tipo_tienda"].replace({
    "Hipermercado": "HIPERMERCADO",
    "Supermercado": "SUPERMERCADO",
    "Conveniencia": "CONVENIENCIA",
    "Ecommerce": "ECOMMERCE"
})

dim_tiendas["zona_distribucion"] = np.where(
    dim_tiendas["id_pais"].isin(["CO", "EC", "PE"]),
    "ANDINA",
    np.where(dim_tiendas["id_pais"] == "MX", "NORTE", "SUR")
)

save_gold(dim_tiendas, "dim_tiendas")


# -------------------------
# dim_clientes
# -------------------------
dim_clientes = clientes.copy()
dim_clientes["fec_registro"] = pd.to_datetime(dim_clientes["fec_registro"], errors="coerce")
dim_clientes["fec_ultima_compra"] = pd.to_datetime(dim_clientes["fec_ultima_compra"], errors="coerce")

dim_clientes["antiguedad_dias"] = (
    pd.Timestamp.today().normalize() - dim_clientes["fec_registro"]
).dt.days

dim_clientes["genero"] = dim_clientes["genero"].replace({
    "SIN_DATO": "No informado",
    None: "No informado"
}).fillna("No informado")

save_gold(dim_clientes, "dim_clientes")


# -------------------------
# fact_ventas
# -------------------------
ventas["fec_trans"] = pd.to_datetime(ventas["fec_trans"], errors="coerce")
ventas["vr_venta_neto"] = (
    ventas["qty_vendida"] * ventas["precio_unitario_venta"]
) - ventas["descuento_aplicado"]
ventas["vr_venta_neto"] = ventas["vr_venta_neto"].clip(lower=0)

ventas["ind_descuento"] = ventas["descuento_aplicado"] > 0

fact_ventas = ventas[[
    "id_trans",
    "id_miembro",
    "id_tienda",
    "art_id",
    "fec_trans",
    "hra_trans",
    "qty_vendida",
    "precio_unitario_venta",
    "descuento_aplicado",
    "vr_venta_neto",
    "tipo_pago",
    "canal_venta",
    "ind_descuento"
]]

save_gold(fact_ventas, "fact_ventas")


# -------------------------
# fact_inventario
# -------------------------
fecha_max = ventas["fec_trans"].max()
fecha_14_dias = fecha_max - pd.Timedelta(days=14)

ventas_14 = ventas[ventas["fec_trans"] >= fecha_14_dias]

consumo_14 = ventas_14.groupby(
    ["art_id", "id_tienda"]
)["qty_vendida"].sum().reset_index()

consumo_14["promedio_consumo_14dias"] = consumo_14["qty_vendida"] / 14

fact_inventario = inventario.merge(
    consumo_14[["art_id", "id_tienda", "promedio_consumo_14dias"]],
    on=["art_id", "id_tienda"],
    how="left"
)

fact_inventario["promedio_consumo_14dias"] = fact_inventario["promedio_consumo_14dias"].fillna(0)

fact_inventario["cobertura_dias"] = np.where(
    fact_inventario["promedio_consumo_14dias"] > 0,
    fact_inventario["stock_fisico"] / fact_inventario["promedio_consumo_14dias"],
    999
)

fact_inventario["alerta_quiebre"] = (
    (fact_inventario["cobertura_dias"] < 7) &
    (fact_inventario["promedio_consumo_14dias"] > 0)
)

fact_inventario["diferencia_stock_minimo"] = (
    fact_inventario["stock_fisico"] - fact_inventario["stock_minimo_config"]
)

save_gold(fact_inventario, "fact_inventario")


# -------------------------
# fact_devoluciones
# -------------------------
devoluciones = devoluciones.merge(
    ventas[["id_trans", "precio_unitario_venta", "canal_venta"]],
    left_on="id_trans_origen",
    right_on="id_trans",
    how="left"
)

motivos = {
    "DEFECTO": "Producto defectuoso",
    "TALLA": "Problema de talla",
    "GARANTIA": "Garantia",
    "CLIENTE": "Decision del cliente",
    "OTRO": "Otro motivo"
}

devoluciones["motivo_desc"] = devoluciones["motivo_cod"].map(motivos).fillna("No informado")
devoluciones["vr_devolucion_estimado"] = (
    devoluciones["qty_devuelta"] * devoluciones["precio_unitario_venta"]
)

fact_devoluciones = devoluciones.drop(columns=["id_trans"], errors="ignore")

save_gold(fact_devoluciones, "fact_devoluciones")


# -------------------------
# fact_rfm_clientes
# -------------------------
ventas_90 = ventas[ventas["fec_trans"] >= (fecha_max - pd.Timedelta(days=90))]
clientes_activos = ventas[ventas["fec_trans"] >= (fecha_max - pd.Timedelta(days=180))]["id_miembro"].unique()

rfm = ventas_90[ventas_90["id_miembro"].isin(clientes_activos)].groupby(
    "id_miembro"
).agg(
    ultima_transaccion=("fec_trans", "max"),
    frecuencia=("id_trans", "count"),
    monto=("vr_venta_neto", "sum")
).reset_index()

rfm["recency"] = (fecha_max - rfm["ultima_transaccion"]).dt.days

rfm["score_r"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["score_f"] = pd.qcut(rfm["frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["score_m"] = pd.qcut(rfm["monto"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm["segmento_rfm"] = (
    "R" + rfm["score_r"].astype(str) +
    "-F" + rfm["score_f"].astype(str) +
    "-M" + rfm["score_m"].astype(str)
)

rfm["segmento_cliente"] = np.where(
    (rfm["score_r"] >= 4) & (rfm["score_f"] >= 4) & (rfm["score_m"] >= 4),
    "Champions",
    np.where(
        (rfm["score_r"] >= 4) & (rfm["score_f"] >= 3),
        "Leales",
        np.where(
            rfm["score_r"] <= 2,
            "En riesgo",
            "Regular"
        )
    )
)

save_gold(rfm, "fact_rfm_clientes")


# -------------------------
# KPI ejecutivo ventas diarias
# -------------------------
ventas_kpi = ventas.merge(
    articulos[["art_id", "id_categ_n1"]],
    on="art_id",
    how="left"
).merge(
    tiendas[["id_tienda", "id_pais"]],
    on="id_tienda",
    how="left"
)

kpi_ventas_diarias = ventas_kpi.groupby(
    ["fec_trans", "id_pais", "canal_venta", "id_categ_n1"]
).agg(
    ventas_netas=("vr_venta_neto", "sum"),
    unidades_vendidas=("qty_vendida", "sum"),
    transacciones=("id_trans", "count"),
    descuento_promedio=("descuento_aplicado", "mean")
).reset_index()

save_gold(kpi_ventas_diarias, "kpi_ventas_diarias")

logger.info("Gold completado correctamente")