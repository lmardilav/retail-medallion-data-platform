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
visitas = read_parquet("MKT_VISITAS_CANAL.parquet")
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

inventario["fec_snapshot"] = pd.to_datetime(inventario["fec_snapshot"], errors="coerce")
fecha_snapshot_max = inventario["fec_snapshot"].max()
inventario_actual = inventario[inventario["fec_snapshot"] == fecha_snapshot_max].copy()

fact_inventario = inventario_actual.merge(
    consumo_14[["art_id", "id_tienda", "promedio_consumo_14dias"]],
    on=["art_id", "id_tienda"],
    how="left"
).merge(
    articulos[["art_id", "id_proveedor", "id_categ_n1"]],
    on="art_id",
    how="left"
).merge(
    proveedores[["id_proveedor", "tiempo_repo_dias", "razon_social"]],
    on="id_proveedor",
    how="left"
)

fact_inventario["promedio_consumo_14dias"] = fact_inventario["promedio_consumo_14dias"].fillna(0)
fact_inventario["tiempo_repo_dias"] = pd.to_numeric(
    fact_inventario["tiempo_repo_dias"],
    errors="coerce"
).fillna(0)
fact_inventario["stock_disponible"] = (
    fact_inventario["stock_fisico"] +
    fact_inventario["stock_transito"] -
    fact_inventario["stock_reservado"]
).clip(lower=0)

fact_inventario["cobertura_dias"] = np.where(
    fact_inventario["promedio_consumo_14dias"] > 0,
    fact_inventario["stock_disponible"] / fact_inventario["promedio_consumo_14dias"],
    999
)

fact_inventario["demanda_estimada_7dias"] = fact_inventario["promedio_consumo_14dias"] * 7
fact_inventario["demanda_durante_reabastecimiento"] = (
    fact_inventario["promedio_consumo_14dias"] *
    fact_inventario["tiempo_repo_dias"]
)
fact_inventario["stock_proyectado_7dias"] = (
    fact_inventario["stock_disponible"] -
    fact_inventario["demanda_estimada_7dias"]
)
fact_inventario["dias_umbral_riesgo"] = fact_inventario["tiempo_repo_dias"].clip(lower=7)

fact_inventario["alerta_quiebre_7dias"] = (
    (fact_inventario["cobertura_dias"] <= fact_inventario["dias_umbral_riesgo"]) &
    (fact_inventario["promedio_consumo_14dias"] > 0)
)
fact_inventario["alerta_quiebre"] = fact_inventario["alerta_quiebre_7dias"]

fact_inventario["diferencia_stock_minimo"] = (
    fact_inventario["stock_disponible"] - fact_inventario["stock_minimo_config"]
)

save_gold(fact_inventario, "fact_inventario")

referencias_riesgo_quiebre_7d = fact_inventario[
    fact_inventario["alerta_quiebre_7dias"]
].sort_values(
    ["cobertura_dias", "stock_proyectado_7dias"]
)

save_gold(referencias_riesgo_quiebre_7d, "referencias_riesgo_quiebre_7d")


# -------------------------
# fact_devoluciones
# -------------------------
devoluciones = devoluciones.merge(
    ventas[["id_trans", "precio_unitario_venta", "canal_venta"]],
    left_on="id_trans_origen",
    right_on="id_trans",
    how="left"
).merge(
    articulos[["art_id", "id_categ_n1", "id_proveedor"]],
    on="art_id",
    how="left"
).merge(
    proveedores[["id_proveedor", "razon_social"]],
    on="id_proveedor",
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

ventas_devoluciones_base = ventas.merge(
    articulos[["art_id", "id_categ_n1", "id_proveedor"]],
    on="art_id",
    how="left"
)

ventas_por_segmento = ventas_devoluciones_base.groupby(
    ["id_categ_n1", "id_proveedor", "canal_venta"]
).agg(
    transacciones_venta=("id_trans", "count"),
    unidades_vendidas=("qty_vendida", "sum"),
    ventas_netas=("vr_venta_neto", "sum")
).reset_index()

kpi_devoluciones_patrones = fact_devoluciones.groupby(
    ["motivo_desc", "id_categ_n1", "id_proveedor", "razon_social", "canal_devolucion"]
).agg(
    devoluciones=("id_devolucion", "count"),
    unidades_devueltas=("qty_devuelta", "sum"),
    valor_devolucion=("vr_devolucion_estimado", "sum")
).reset_index().merge(
    ventas_por_segmento,
    left_on=["id_categ_n1", "id_proveedor", "canal_devolucion"],
    right_on=["id_categ_n1", "id_proveedor", "canal_venta"],
    how="left"
)

kpi_devoluciones_patrones["tasa_devolucion_unidades"] = np.where(
    kpi_devoluciones_patrones["unidades_vendidas"] > 0,
    kpi_devoluciones_patrones["unidades_devueltas"] /
    kpi_devoluciones_patrones["unidades_vendidas"],
    0
)

kpi_devoluciones_patrones = kpi_devoluciones_patrones.drop(
    columns=["canal_venta"],
    errors="ignore"
)

save_gold(kpi_devoluciones_patrones, "kpi_devoluciones_patrones")


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

rfm["puntaje_rfm"] = rfm["score_r"] + rfm["score_f"] + rfm["score_m"]
rfm["segmento_cliente"] = pd.qcut(
    rfm["puntaje_rfm"].rank(method="first"),
    5,
    labels=[
        "Bajo valor",
        "En riesgo",
        "Potencial",
        "Alto valor",
        "Champions"
    ]
).astype(str)

rfm["fecha_actualizacion"] = fecha_max.normalize()
rfm["semana_actualizacion"] = rfm["fecha_actualizacion"].dt.strftime("%G-W%V")

save_gold(rfm, "fact_rfm_clientes")

kpi_segmentos_rfm = rfm.groupby(
    ["semana_actualizacion", "segmento_cliente"]
).agg(
    clientes=("id_miembro", "count"),
    recency_promedio=("recency", "mean"),
    frecuencia_promedio=("frecuencia", "mean"),
    monto_total=("monto", "sum")
).reset_index()

save_gold(kpi_segmentos_rfm, "kpi_segmentos_rfm")


# -------------------------
# Conversion por canal y categoria
# -------------------------
visitas["fec_visita"] = pd.to_datetime(visitas["fec_visita"], errors="coerce")

visitas_categoria = visitas.merge(
    articulos[["art_id", "id_categ_n1"]],
    on="art_id",
    how="left"
)

ventas_categoria = ventas.merge(
    articulos[["art_id", "id_categ_n1"]],
    on="art_id",
    how="left"
)

visitas_agg = visitas_categoria.groupby(
    ["canal_visita", "id_categ_n1"]
).agg(
    visitas=("id_visita", "count"),
    clientes_visitantes=("id_miembro", "nunique")
).reset_index()

compras_agg = ventas_categoria.groupby(
    ["canal_venta", "id_categ_n1"]
).agg(
    compras=("id_trans", "count"),
    ventas_netas=("vr_venta_neto", "sum")
).reset_index()

visitantes_unicos = visitas_categoria[[
    "canal_visita",
    "id_categ_n1",
    "id_miembro"
]].drop_duplicates()

compradores_unicos = ventas_categoria[[
    "canal_venta",
    "id_categ_n1",
    "id_miembro"
]].drop_duplicates()

compradores_convertidos = visitantes_unicos.merge(
    compradores_unicos,
    left_on=["canal_visita", "id_categ_n1", "id_miembro"],
    right_on=["canal_venta", "id_categ_n1", "id_miembro"],
    how="inner"
).groupby(
    ["canal_visita", "id_categ_n1"]
).agg(
    clientes_compradores=("id_miembro", "nunique")
).reset_index()

kpi_conversion_canal_categoria = visitas_agg.merge(
    compras_agg,
    left_on=["canal_visita", "id_categ_n1"],
    right_on=["canal_venta", "id_categ_n1"],
    how="left"
).merge(
    compradores_convertidos,
    on=["canal_visita", "id_categ_n1"],
    how="left"
)

kpi_conversion_canal_categoria["compras"] = (
    kpi_conversion_canal_categoria["compras"].fillna(0)
)
kpi_conversion_canal_categoria["clientes_compradores"] = (
    kpi_conversion_canal_categoria["clientes_compradores"].fillna(0)
)
kpi_conversion_canal_categoria["ventas_netas"] = (
    kpi_conversion_canal_categoria["ventas_netas"].fillna(0)
)
kpi_conversion_canal_categoria["tasa_conversion"] = np.where(
    kpi_conversion_canal_categoria["clientes_visitantes"] > 0,
    kpi_conversion_canal_categoria["clientes_compradores"] /
    kpi_conversion_canal_categoria["clientes_visitantes"],
    0
)
kpi_conversion_canal_categoria["ticket_promedio"] = np.where(
    kpi_conversion_canal_categoria["compras"] > 0,
    kpi_conversion_canal_categoria["ventas_netas"] /
    kpi_conversion_canal_categoria["compras"],
    0
)
kpi_conversion_canal_categoria = kpi_conversion_canal_categoria.rename(
    columns={
        "canal_visita": "canal",
        "id_categ_n1": "categoria"
    }
).drop(columns=["canal_venta"], errors="ignore")

save_gold(kpi_conversion_canal_categoria, "kpi_conversion_canal_categoria")


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

# ===================================================
# DASHBOARD EJECUTIVO
# ===================================================

ventas_dashboard_base = ventas.merge(
    articulos[["art_id", "id_categ_n1"]],
    on="art_id",
    how="left"
).merge(
    tiendas[["id_tienda", "id_pais", "nom_tienda"]],
    on="id_tienda",
    how="left"
)

ventas_dashboard_base["pais"] = ventas_dashboard_base["id_pais"].map(pais_map)
ventas_dashboard_base["categoria"] = ventas_dashboard_base["id_categ_n1"]

vista_dashboard_ejecutivo = ventas_dashboard_base.groupby(
    [
        "fec_trans",
        "pais",
        "id_tienda",
        "nom_tienda",
        "canal_venta",
        "categoria"
    ]
).agg(
    ventas_totales=("vr_venta_neto", "sum"),
    cantidad_ventas=("id_trans", "count"),
    unidades_vendidas=("qty_vendida", "sum")
).reset_index()

vista_dashboard_ejecutivo["ticket_promedio"] = (
    vista_dashboard_ejecutivo["ventas_totales"] /
    vista_dashboard_ejecutivo["cantidad_ventas"]
)

save_gold(
    vista_dashboard_ejecutivo,
    "vista_dashboard_ejecutivo"
)

print(
    "vista_dashboard_ejecutivo creada:",
    len(vista_dashboard_ejecutivo),
    "registros"
)

logger.info("Gold completado correctamente")
print("Gold completado")
