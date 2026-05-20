# Prueba Técnica - Data Engineer Retail

## Sector seleccionado y justificación

### Sector elegido: Retail

Se seleccionó el sector Retail debido a que presenta múltiples escenarios de negocio y una alta complejidad en el manejo de datos, incluyendo ventas, inventario, clientes, proveedores y devoluciones. Este tipo de industria genera grandes volúmenes de información provenientes de diferentes fuentes y requiere procesos robustos para integración, transformación y análisis.

El escenario Retail permite modelar casos reales de negocio como:

- Análisis de ventas
- Gestión de inventarios
- Segmentación de clientes (RFM)
- Análisis de devoluciones
- KPIs comerciales
- Optimización de abastecimiento

Además, proporciona un caso práctico adecuado para implementar una arquitectura de datos moderna basada en capas.

---

### Plataforma Cloud seleccionada: AWS

Se seleccionó AWS como plataforma cloud debido a su amplio ecosistema de servicios orientados a ingeniería de datos y analítica.
AWS proporciona herramientas administradas que facilitan la construcción de pipelines escalables, seguros y con bajo costo operativo.

Servicios utilizados:

- Amazon S3 para Data Lake (Bronze, Silver y Gold)
- AWS Glue para catálogo y descubrimiento automático de datos
- CloudWatch para monitoreo y logs
- SNS para alertas y notificaciones
- Secrets Manager para gestión segura de credenciales
- IAM para administración de permisos

---

### Justificación de la arquitectura seleccionada

Se implementó una arquitectura Medallion (Bronze, Silver y Gold) porque permite separar los datos por niveles de procesamiento:

**Bronze**

- Almacena datos crudos sin transformaciones.

**Silver**

- Aplica procesos de limpieza, estandarización y validación.

**Gold**

- Contiene modelos analíticos y KPIs listos para consumo.

Esta arquitectura mejora la trazabilidad, facilita el mantenimiento y permite reutilizar los datos para diferentes casos de uso analítico.

---

## Gestión de roles y accesos

Se implementaron roles diferenciados siguiendo el principio de mínimo privilegio:

- RetailDataEngineerRole:
  Lectura/escritura sobre S3, Glue y monitoreo.

- RetailAnalystRole:
  Acceso de solo lectura a datos analíticos.

- RetailAdminRole:
  Control administrativo completo de la plataforma.

Los secretos y credenciales se gestionan mediante AWS Secrets Manager evitando exponer información sensible en el código fuente.

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

## Arquitectura

![Arquitectura](docs/evidencias/arquitectura.png)

Arquitectura implementada:

PostgreSQL → S3 Bronze → S3 Silver → S3 Gold → AWS Glue → CloudWatch + SNS

## Catálogo de datos

Ver catálogo en: [docs/catalogo_datos.md](docs/catalogo_datos.md)

## Evidencias

# Fase 1 — PostgreSQL

### PostgreSQL - tablas creadas

![PostgreSQL](docs/evidencias/fase1/conteos_tablas.png)

---

# Fase 2 — Infraestructura AWS + Terraform

### Buckets S3 creados

![Buckets](docs/evidencias/fase2/s3_buckets_aws.jpg)

### Terraform Apply

![Terraform Apply](docs/evidencias/fase2/terraform_apply_s3.png)

### Buckets creados mediante Terraform

![Terraform Buckets](docs/evidencias/fase2/terraform_buckets_creados.png)

---

# Fase 3 — Pipeline Medallion

### Datos cargados en Bronze

![Bronze](docs/evidencias/fase3/bronze_cargado.png)

### Flujo Bronze → Silver

![Bronze Silver](docs/evidencias/fase3/bronze_silver.png)

### Calidad inicial de datos

![Calidad Inicial](docs/evidencias/fase3/data_quality_checks.png)

### Gold completo

![Gold Completo](docs/evidencias/fase3/gold_completo.png)

### Dimensión Productos

![Gold Productos](docs/evidencias/fase3/gold_dim_productos.png)

### Dimensión Clientes

![Gold Clientes](docs/evidencias/fase3/gold_dim_clientes.png)

### Fact Ventas

![Fact Ventas](docs/evidencias/fase3/gold_fact_ventas.png)

### Segmentación RFM

![RFM](docs/evidencias/fase3/gold_rfm.png)

### Pipeline orquestado

![Pipeline](docs/evidencias/fase3/orquestacion_pipeline.png)

### Buckets Bronze AWS

![S3 Bronze](docs/evidencias/fase3/s3_buckets_bronze_aws.jpg)

---

# Fase 4 — Seguridad y Gobierno de Datos

### CloudWatch Logs

![CloudWatch](docs/evidencias/fase4/cloudwatch_logs.png)

### Data Quality Final

![Data Quality Final](docs/evidencias/fase4/data_quality_checks.png)

### AWS Glue Data Catalog

![Glue Catalog](docs/evidencias/fase4/glue_catalog_tables.png)

### AWS Secrets Manager

![Secrets Manager](docs/evidencias/fase4/secrets_manager.png)

### IAM Roles

![Secrets Manager](docs/evidencias/fase4/iam_roles.png)

### SNS Alertas

![SNS](docs/evidencias/fase4/sns_topic.png)

## Arquitectura

![Arquitectura](docs/evidencias/arquitectura.png)

---

## Servicios AWS implementados

| Servicio              | Propósito                             |
| --------------------- | ------------------------------------- |
| Amazon S3             | Almacenamiento Bronze, Silver y Gold  |
| AWS Glue Data Catalog | Catálogo automático de tablas         |
| AWS Glue Crawler      | Descubrimiento automático de esquemas |
| CloudWatch Logs       | Centralización de logs                |
| SNS                   | Alertas y notificaciones              |
| Secrets Manager       | Gestión segura de credenciales        |
| IAM                   | Gestión de permisos y roles           |
