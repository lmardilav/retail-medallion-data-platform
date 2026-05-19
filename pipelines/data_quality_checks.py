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
rfm = read_gold("fact_rfm_clientes.parquet")

checks.append(("fact_ventas no vacía", len(fact_ventas) > 0))
checks.append(("dim_productos no vacía", len(dim_productos) > 0))
checks.append(("id_trans único", fact_ventas["id_trans"].is_unique))
checks.append(("vr_venta_neto no negativo", (fact_ventas["vr_venta_neto"] >= 0).all()))
checks.append(("alerta_quiebre existe", "alerta_quiebre" in fact_inventario.columns))
checks.append(("segmento_rfm existe", "segmento_rfm" in rfm.columns))

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