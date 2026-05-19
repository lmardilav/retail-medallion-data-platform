import boto3
import pandas as pd
from io import BytesIO

s3 = boto3.client("s3")

bronze_bucket="retail-data-engineering-luis-810204248846-bronze"
silver_bucket="retail-data-engineering-luis-810204248846-silver"

files=[
"MSTR_ARTICULOS.parquet",
"MSTR_PROVEEDORES.parquet",
"CRM_MIEMBROS.parquet",
"TRANS_VENTAS.parquet",
"MSTR_TIENDAS.parquet",
"INV_STOCK_DIARIO.parquet",
"POST_DEVOLUCIONES.parquet"
]

for file in files:

    response=s3.get_object(
        Bucket=bronze_bucket,
        Key=f"raw/{file}"
    )

    df=pd.read_parquet(
        BytesIO(response["Body"].read())
    )

    # limpieza básica
    df=df.drop_duplicates()

    # reemplazar nulos
    df=df.fillna("SIN_DATO")

    buffer=BytesIO()

    df.to_parquet(
        buffer,
        index=False
    )

    s3.put_object(
        Bucket=silver_bucket,
        Key=f"clean/{file}",
        Body=buffer.getvalue()
    )

    print(file,"transformado")

print("Silver completado")