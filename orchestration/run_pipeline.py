import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

steps = [
    ("Bronze Upload", BASE_DIR / "pipelines" / "upload_to_bronze.py"),
    ("Silver Transform", BASE_DIR / "pipelines" / "silver_transform.py"),
    ("Gold Transform", BASE_DIR / "pipelines" / "gold_transform.py"),
    ("Data Quality Checks", BASE_DIR / "pipelines" / "data_quality_checks.py"),
]

print("Iniciando pipeline:", datetime.now())

for name, script in steps:
    print(f"\nEjecutando: {name}")

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"Error en: {name}")
        print(result.stderr)
        sys.exit(1)

print("\nPipeline completado correctamente:", datetime.now())


print("========== REPORTE DIARIO ==========")
print("Bronze: OK")
print("Silver: OK")
print("Gold: OK")
print("Calidad: PASSED")
print("Tablas Gold principales: fact_ventas, fact_inventario, fact_rfm_clientes")
print("KPIs nuevos: referencias_riesgo_quiebre_7d, kpi_conversion_canal_categoria, kpi_devoluciones_patrones, vista_dashboard_ejecutivo")
print("====================================")
