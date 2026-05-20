# Catalogo de Datos

## Capa Bronze

| Tabla | Descripcion | Sensible |
| --- | --- | --- |
| MSTR_ARTICULOS | Maestro de productos/articulos | No |
| MSTR_PROVEEDORES | Informacion de proveedores | No |
| MSTR_TIENDAS | Maestro de tiendas | No |
| CRM_MIEMBROS | Clientes del programa de fidelizacion | Si |
| TRANS_VENTAS | Transacciones de ventas | No |
| MKT_VISITAS_CANAL | Visitas e interacciones por canal | No |
| INV_STOCK_DIARIO | Inventario diario por articulo y tienda | No |
| POST_DEVOLUCIONES | Devoluciones de productos | No |

---

## Capa Silver

| Tabla | Descripcion | Transformaciones |
| --- | --- | --- |
| MSTR_ARTICULOS | Productos limpios | Duplicados eliminados, nulos tratados |
| MSTR_PROVEEDORES | Proveedores limpios | Duplicados eliminados, nulos tratados |
| MSTR_TIENDAS | Tiendas limpias | Duplicados eliminados, nulos tratados |
| CRM_MIEMBROS | Clientes limpios | Genero estandarizado, nulos tratados |
| TRANS_VENTAS | Ventas limpias | Duplicados eliminados, tipos preparados |
| MKT_VISITAS_CANAL | Visitas limpias | Duplicados eliminados, nulos tratados |
| INV_STOCK_DIARIO | Inventario limpio | Duplicados eliminados, nulos tratados |
| POST_DEVOLUCIONES | Devoluciones limpias | Duplicados eliminados, nulos tratados |

---

## Capa Gold

| Tabla | Tipo | Descripcion |
| --- | --- | --- |
| dim_productos | Dimension | Productos enriquecidos con proveedor, categoria y margen estimado |
| dim_tiendas | Dimension | Tiendas con pais, ciudad y zona de distribucion |
| dim_clientes | Dimension | Clientes con antiguedad y genero estandarizado |
| fact_ventas | Hecho | Ventas netas, descuentos y canal de venta |
| fact_inventario | Hecho | Cobertura de inventario y alerta de quiebre |
| fact_devoluciones | Hecho | Devoluciones con motivo, categoria, proveedor, canal y valor estimado |
| fact_rfm_clientes | Hecho | Segmentacion RFM de clientes |
| kpi_ventas_diarias | KPI | Ventas netas diarias por pais, canal y categoria |
| referencias_riesgo_quiebre_7d | KPI | Referencias con riesgo de quiebre considerando consumo, stock y reabastecimiento |
| kpi_conversion_canal_categoria | KPI | Tasa de conversion, compradores, visitantes y ticket promedio por canal y categoria |
| kpi_devoluciones_patrones | KPI | Devoluciones por motivo, categoria, proveedor y canal con tasa de devolucion |
| kpi_segmentos_rfm | KPI | Resumen semanal de clientes por segmento RFM |
| vista_dashboard_ejecutivo | Vista | Ventas diarias por pais, tienda, canal y categoria para direccion comercial |

---

## Campos calculados principales

| Campo | Tabla Gold | Origen | Transformacion |
| --- | --- | --- | --- |
| vr_venta_neto | fact_ventas | TRANS_VENTAS | qty_vendida * precio_unitario_venta - descuento_aplicado |
| cobertura_dias | fact_inventario | INV_STOCK_DIARIO + TRANS_VENTAS | stock_disponible / promedio_consumo_14dias |
| alerta_quiebre_7dias | fact_inventario | fact_inventario + MSTR_PROVEEDORES | cobertura_dias <= max(7, tiempo_repo_dias) y consumo mayor a 0 |
| margen_estimado | dim_productos | MSTR_ARTICULOS | precio_lista * 0.30 |
| segmento_rfm | fact_rfm_clientes | TRANS_VENTAS | Recency, Frequency y Monetary por cliente |
| tasa_conversion | kpi_conversion_canal_categoria | MKT_VISITAS_CANAL + TRANS_VENTAS | clientes_compradores / clientes_visitantes |
| tasa_devolucion_unidades | kpi_devoluciones_patrones | POST_DEVOLUCIONES + TRANS_VENTAS | unidades_devueltas / unidades_vendidas |
