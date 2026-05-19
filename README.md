# Prueba Técnica - Data Engineer Retail

## Objetivo

Construir un pipeline de datos end-to-end usando arquitectura Medallion (Bronze, Silver y Gold) sobre un escenario Retail.

---

## Arquitectura utilizada

PostgreSQL → S3 Bronze → S3 Silver → S3 Gold

### Bronze

Contiene datos crudos sin transformación.

Tablas:

- MSTR_ARTICULOS
- MSTR_PROVEEDORES
- MSTR_TIENDAS
- CRM_MIEMBROS
- TRANS_VENTAS
- INV_STOCK_DIARIO
- POST_DEVOLUCIONES

### Silver

Transformaciones aplicadas:

- Eliminación de duplicados
- Manejo de nulos
- Estandarización de formatos

### Gold

Modelo dimensional generado:

Dimensiones:

- dim_productos
- dim_tiendas
- dim_clientes

Hechos:

- fact_ventas
- fact_inventario
- fact_devoluciones
- fact_rfm_clientes
- kpi_ventas_diarias

---

## Infraestructura

Creada mediante Terraform:

Recursos:

- Bucket Bronze
- Bucket Silver
- Bucket Gold

---

## Tecnologías utilizadas

- Python
- PostgreSQL
- Docker
- Terraform
- AWS S3
- Pandas
- Boto3

---

## Ejecución

### Generar datos

```bash
python generate_data.py
```

### Cargar PostgreSQL

```bash
python load_to_postgres.py
```

### Cargar Bronze

```bash
python upload_to_bronze.py
```

### Procesar Silver

```bash
python silver_transform.py
```

### Procesar Gold

```bash
python gold_transform.py
```

```md
## Arquitectura

Ver diagrama en: [docs/arquitectura.md](docs/arquitectura.md)
```

## Catálogo de datos

Ver catálogo en: [docs/catalogo_datos.md](docs/catalogo_datos.md)

## Evidencias

### PostgreSQL - tablas creadas

![PostgreSQL](docs/evidencias/fase1/conteos_tablas.png)

### Buckets S3 creados

![Buckets](docs/evidencias/fase2/s3_buckets_aws.jpg)

### Terraform buckets

![Terraform](docs/evidencias/fase2/terraform_apply_s3.png)

### Datos cargados en Bronze

![Bronze](docs/evidencias/fase3/bronze_cargado.png)

### Calidad de datos

![Calidad](docs/evidencias/fase3/data_quality_checks.png)

### Capa Gold - Productos

![Gold Productos](docs/evidencias/fase3/gold_dim_productos.png)

### Capa Gold - Clientes

![Gold Clientes](docs/evidencias/fase3/gold_dim_clientes.png)

### Capa Gold - Ventas

![Gold Ventas](docs/evidencias/fase3/gold_fact_ventas.png)

### Capa Gold - RFM

![Gold RFM](docs/evidencias/fase3/gold_rfm.png)

### Orquestación

![Pipeline](docs/evidencias/fase3/orquestacion_pipeline.png)
