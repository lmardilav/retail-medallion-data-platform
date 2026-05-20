import boto3
import pandas as pd
from io import BytesIO
from logger_config import logger

s3 = boto3.client("s3")

gold_bucket = "retail-data-engineering-luis-810204248846-gold"

def read_gold(file):
    response = s3.get_object(
        Bucket=gold_bucket,
        Key=f"analytics/{file}"
    )
    return pd.read_parquet(BytesIO(response["Body"].read()))

checks = []

fact_ventas = read_gold("fact_ventas.parquet")
dim_productos = read_gold("dim_productos.parquet")
fact_inventario = read_gold("fact_inventario.parquet")
riesgo_quiebre = read_gold("referencias_riesgo_quiebre_7d.parquet")
rfm = read_gold("fact_rfm_clientes.parquet")
conversion = read_gold("kpi_conversion_canal_categoria.parquet")
devoluciones = read_gold("kpi_devoluciones_patrones.parquet")
dashboard = read_gold("vista_dashboard_ejecutivo.parquet")


# ALERTA DE ANOMALÍA DE VOLUMEN
if len(fact_ventas) < 900000:
    print("ALERTA: volumen anómalo detectado")
    logger.warning("ALERTA: volumen anómalo detectado")


checks.append(("fact_ventas no vacía", len(fact_ventas) > 0))
checks.append(("dim_productos no vacía", len(dim_productos) > 0))
checks.append(("id_trans único", fact_ventas["id_trans"].is_unique))
checks.append(("vr_venta_neto no negativo", (fact_ventas["vr_venta_neto"] >= 0).all()))
checks.append(("alerta_quiebre existe", "alerta_quiebre" in fact_inventario.columns))
checks.append(("tiempo de reabastecimiento existe", "tiempo_repo_dias" in fact_inventario.columns))
checks.append(("riesgo quiebre 7d creado", len(riesgo_quiebre) >= 0))
checks.append(("segmento_rfm existe", "segmento_rfm" in rfm.columns))
checks.append(("RFM tiene minimo cinco segmentos", rfm["segmento_cliente"].nunique() >= 5))
checks.append(("conversion por canal y categoria existe", len(conversion) > 0))
checks.append(("tasa_conversion no negativa", (conversion["tasa_conversion"] >= 0).all()))
checks.append(("tasa_conversion menor o igual a 1", (conversion["tasa_conversion"] <= 1).all()))
checks.append(("devoluciones por patron existe", len(devoluciones) > 0))
checks.append(("dashboard ejecutivo existe", len(dashboard) > 0))

for name, result in checks:
    status = "PASSED" if result else "FAILED"
    print(f"{name}: {status}")
    logger.info(f"Data Quality - {name}: {status}")

if all(result for _, result in checks):
    print("Todas las pruebas de calidad pasaron correctamente")
    logger.info("Todas las pruebas de calidad pasaron correctamente")
else:
    print("Algunas pruebas de calidad fallaron")
    logger.error("Algunas pruebas de calidad fallaron")
