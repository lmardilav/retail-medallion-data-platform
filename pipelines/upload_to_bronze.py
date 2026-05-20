import boto3
import os

s3 = boto3.client("s3")

bucket="retail-data-engineering-luis-810204248846-bronze"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder = os.path.join(BASE_DIR, "data-generation", "output", "parquet")

for file in os.listdir(folder):

    if file.endswith(".parquet"):

        path=os.path.join(folder,file)

        s3.upload_file(
            path,
            bucket,
            f"raw/{file}"
        )

        print(f"{file} subido")

print("Carga Bronze completada")
