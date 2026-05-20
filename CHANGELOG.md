# Changelog

## 2026-05-20

### Added

- Tabla fuente `MKT_VISITAS_CANAL` para calcular conversion por canal y categoria.
- KPI `referencias_riesgo_quiebre_7d` con consumo de 14 dias, stock disponible y tiempo de reabastecimiento.
- Segmentacion RFM semanal en cinco grupos de valor.
- KPI `kpi_conversion_canal_categoria` con visitantes, compradores, tasa de conversion y ticket promedio.
- KPI `kpi_devoluciones_patrones` por motivo, categoria, proveedor y canal.
- Vista `vista_dashboard_ejecutivo` por fecha, pais, tienda, canal y categoria.

## 2026-05-19

### Added

- Seleccion del escenario Retail.
- Generacion de datos sinteticos para tablas fuente.
- Carga de datos en PostgreSQL usando Docker.
- Creacion de infraestructura AWS con Terraform.
- Creacion de buckets S3 Bronze, Silver y Gold.
- Carga de archivos Parquet en Bronze.
- Transformacion de datos hacia Silver.
- Construccion de capa Gold con dimensiones, hechos y KPIs.
- Documentacion inicial del README.
- Creacion del catalogo de datos.
- Creacion del diagrama de arquitectura.
