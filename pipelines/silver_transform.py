import boto3
import pandas as pd
from io import BytesIO
import hashlib

s3 = boto3.client("s3")

bronze_bucket = "retail-data-engineering-luis-810204248846-bronze"
silver_bucket = "retail-data-engineering-luis-810204248846-silver"

files = [
    "MSTR_ARTICULOS.parquet",
    "MSTR_PROVEEDORES.parquet",
    "CRM_MIEMBROS.parquet",
    "TRANS_VENTAS.parquet",
    "MSTR_TIENDAS.parquet",
    "INV_STOCK_DIARIO.parquet",
    "POST_DEVOLUCIONES.parquet"
]

for file in files:

    response = s3.get_object(
        Bucket=bronze_bucket,
        Key=f"raw/{file}"
    )

    df = pd.read_parquet(
        BytesIO(response["Body"].read())
    )

    # Limpieza básica
    df = df.drop_duplicates()

    # Reemplazar nulos
    df = df.fillna("SIN_DATO")

    # Protección de datos sensibles para CRM_MIEMBROS
    if file == "CRM_MIEMBROS.parquet":
        sensitive_columns = ["genero", "rango_edad"]

        for column in sensitive_columns:
            if column in df.columns:
                df[f"{column}_hash"] = df[column].apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest()
                )

        print("Datos sensibles protegidos en CRM_MIEMBROS")

    buffer = BytesIO()

    df.to_parquet(
        buffer,
        index=False
    )

    s3.put_object(
        Bucket=silver_bucket,
        Key=f"clean/{file}",
        Body=buffer.getvalue()
    )

    print(file, "transformado")

print("Silver completado")