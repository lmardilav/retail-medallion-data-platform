import subprocess
import sys
from datetime import datetime

steps = [
    ("Bronze Upload", "../pipelines/upload_to_bronze.py"),
    ("Silver Transform", "../pipelines/silver_transform.py"),
    ("Gold Transform", "../pipelines/gold_transform.py"),
    ("Data Quality Checks", "../pipelines/data_quality_checks.py"),
]

print("Iniciando pipeline:", datetime.now())

for name, script in steps:
    print(f"\nEjecutando: {name}")

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"Error en: {name}")
        print(result.stderr)
        sys.exit(1)

print("\nPipeline completado correctamente:", datetime.now())