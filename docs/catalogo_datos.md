# Catálogo de Datos

## Capa Bronze

| Tabla             | Descripción                             | Sensible |
| ----------------- | --------------------------------------- | -------- |
| MSTR_ARTICULOS    | Maestro de productos/artículos          | No       |
| MSTR_PROVEEDORES  | Información de proveedores              | No       |
| MSTR_TIENDAS      | Maestro de tiendas                      | No       |
| CRM_MIEMBROS      | Clientes del programa de fidelización   | Sí       |
| TRANS_VENTAS      | Transacciones de ventas                 | No       |
| INV_STOCK_DIARIO  | Inventario diario por artículo y tienda | No       |
| POST_DEVOLUCIONES | Devoluciones de productos               | No       |

---

## Capa Silver

| Tabla             | Descripción          | Transformaciones                        |
| ----------------- | -------------------- | --------------------------------------- |
| MSTR_ARTICULOS    | Productos limpios    | Duplicados eliminados, nulos tratados   |
| MSTR_PROVEEDORES  | Proveedores limpios  | Duplicados eliminados, nulos tratados   |
| MSTR_TIENDAS      | Tiendas limpias      | Duplicados eliminados, nulos tratados   |
| CRM_MIEMBROS      | Clientes limpios     | Género estandarizado, nulos tratados    |
| TRANS_VENTAS      | Ventas limpias       | Duplicados eliminados, tipos preparados |
| INV_STOCK_DIARIO  | Inventario limpio    | Duplicados eliminados, nulos tratados   |
| POST_DEVOLUCIONES | Devoluciones limpias | Duplicados eliminados, nulos tratados   |

---

## Capa Gold

| Tabla              | Tipo      | Descripción                                                       |
| ------------------ | --------- | ----------------------------------------------------------------- |
| dim_productos      | Dimensión | Productos enriquecidos con proveedor, categoría y margen estimado |
| dim_tiendas        | Dimensión | Tiendas con país, ciudad y zona de distribución                   |
| dim_clientes       | Dimensión | Clientes con antigüedad y género estandarizado                    |
| fact_ventas        | Hecho     | Ventas netas, descuentos y canal de venta                         |
| fact_inventario    | Hecho     | Cobertura de inventario y alerta de quiebre                       |
| fact_devoluciones  | Hecho     | Devoluciones con motivo legible y valor estimado                  |
| fact_rfm_clientes  | Hecho     | Segmentación RFM de clientes                                      |
| kpi_ventas_diarias | KPI       | Ventas netas diarias por país, canal y categoría                  |

---

## Campos calculados principales

| Campo           | Tabla Gold        | Origen                          | Transformación                                            |
| --------------- | ----------------- | ------------------------------- | --------------------------------------------------------- |
| vr_venta_neto   | fact_ventas       | TRANS_VENTAS                    | qty_vendida \* precio_unitario_venta - descuento_aplicado |
| cobertura_dias  | fact_inventario   | INV_STOCK_DIARIO + TRANS_VENTAS | stock_fisico / promedio_consumo_14dias                    |
| alerta_quiebre  | fact_inventario   | fact_inventario                 | cobertura_dias < 7 y consumo mayor a 0                    |
| margen_estimado | dim_productos     | MSTR_ARTICULOS                  | precio_lista \* 0.30                                      |
| segmento_rfm    | fact_rfm_clientes | TRANS_VENTAS                    | Recency, Frequency y Monetary por cliente                 |
