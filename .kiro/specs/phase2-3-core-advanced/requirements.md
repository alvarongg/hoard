# Requirements Document

_Fase 2 (Core) y Fase 3 (Advanced) — H.O.A.R.D._

## Introduction

La Fase 1 (MVP) de H.O.A.R.D. está terminada: el backend FastAPI expone services y routes para categorías, catálogos (con catalog items e import CSV), colecciones (con collection items) e imágenes; el frontend React 18 tiene 6 páginas (Home, Collections, CollectionDetail, Catalogs, CatalogDetail, CatalogManagement) con componentes UI base y traducciones en español e inglés.

La migración `001_initial_schema.py` ya crea las 17 tablas, los triggers y las 4 vistas (`v_collection_items_full`, `v_collection_items_by_category`, `v_wishlist_with_avg_price`, `v_collection_stats`), por lo que este spec **no requiere crear tablas nuevas**. Sin embargo:

- Faltan modelos SQLAlchemy para `category_field_schemas`, `catalog_price_history`, `item_transactions` e `item_accessories`.
- `WishlistItem`, `WishlistSighting`, `Supplier`, `AccessoryStock` e `ItemComponent` tienen modelo pero no tienen schemas Pydantic, ni service, ni endpoints, ni UI.
- No existe dark mode, búsqueda avanzada, estadísticas, gráficos, import/export JSON, backups, scheduler ni PWA.

Este spec cubre el cierre de la Fase 2 (Core) y de la Fase 3 (Advanced) del roadmap.

Nombres usados en los criterios de aceptación: **Backend** (API FastAPI y sus services), **Frontend** (aplicación React), **Sistema** (Backend y Frontend en conjunto). Los criterios que dependen de funcionalidad exclusiva de PostgreSQL (`tsvector`, `pg_trgm`, columnas `GENERATED`, triggers y vistas) declaran explícitamente el comportamiento esperado en producción (PostgreSQL 14+) y en el entorno de test (SQLite in-memory).

## Glossary

- **Backend**: La API FastAPI de H.O.A.R.D. junto con sus services, models y schemas.
- **Frontend**: La aplicación React 18 de H.O.A.R.D., incluidas sus páginas, componentes y hooks.
- **Sistema**: El Backend y el Frontend considerados en conjunto, incluidos sus tests y archivos de configuración y traducción.
- **colección single_category**: Colección restringida a una única sub-categoría, identificada por `restricted_to_sub_category_id`, que es obligatorio para este tipo.
- **colección multi_category**: Colección que admite items de varias sub-categorías dentro de un mismo criterio temático, sin restricción a una sub-categoría única.
- **colección mixed**: Colección que admite items de cualquier categoría principal y sub-categoría, sin restricción de categoría.
- **catalog item**: Entrada del catálogo que describe una pieza a nivel de referencia (título, fabricante, región, rareza), independiente de si el usuario la posee.
- **collection item**: Ejemplar concreto que el usuario posee, asociado a una colección y normalmente a un catalog item, con datos de compra, condición y valor.
- **wishlist item**: Pieza deseada y no poseída, asociada a un catalog item, con prioridad, urgencia, presupuesto máximo y estado de adquisición.
- **avistamiento (sighting)**: Registro de una ocasión en que un wishlist item fue visto en venta, con precio, proveedor, condición, disponibilidad y decisión tomada.
- **componente estándar (standard component)**: Elemento definido a nivel de sub-categoría que una pieza completa debería incluir (por ejemplo caja, manual, inserto). Su carácter se expresa en `standard_components.component_type`, cuyos valores son `required`, `common`, `optional` y `variant_specific`.
- **historial de precios**: Serie de precios de mercado registrados para un catalog item, cualificados por condición, completitud, fecha, región y fuente.
- **transacción de item**: Movimiento económico asociado a un collection item (compra, venta, envío, grading, tasación, entre otros), con importe, costos adicionales y total.
- **accesorio**: Insumo de protección o almacenamiento (funda, caja protectora) gestionado como stock y asignable a collection items.
- **stock disponible**: Cantidad de un accesorio que no está asignada a ningún collection item, es decir el total menos la cantidad en uso.
- **backup**: Archivo que contiene el dump de la base de datos, las imágenes y la configuración de la aplicación en un momento dado.
- **retención**: Número máximo de backups que el Sistema conserva; al superarse, se eliminan los backups más antiguos.
- **cola de sincronización**: Almacenamiento persistente en el Frontend de las operaciones creadas sin conexión, pendientes de enviarse al Backend cuando la conexión se restablece.
- **entorno de test**: Entorno de ejecución de la suite de tests, que usa SQLite in-memory en lugar de PostgreSQL.
- **modo degradado de búsqueda**: Modo de búsqueda usado cuando no está disponible la funcionalidad de texto completo de PostgreSQL, basado en coincidencia por `LIKE`/`ILIKE` e indicado explícitamente en la respuesta.

---

## Requirements

### Requirement 1: Colecciones multi-category

**User Story:** Como coleccionista con aficiones diversas, quiero crear colecciones que mezclen varias categorías, para organizar todo mi acervo bajo un mismo criterio temático sin fragmentarlo.

#### Acceptance Criteria

1. WHEN el usuario crea una colección con `collection_type` igual a `single_category`, `multi_category` o `mixed` THEN el Backend SHALL persistir el valor recibido y rechazar con error de validación cualquier otro valor
2. WHEN el usuario crea o edita una colección con `collection_type` igual a `single_category` y sin `restricted_to_sub_category_id` THEN el Backend SHALL rechazar la operación con un error descriptivo que identifique el campo faltante
3. WHEN el usuario crea o edita una colección con `collection_type` distinto de `single_category` THEN el Backend SHALL aceptar `restricted_to_sub_category_id` nulo
4. WHEN el usuario agrega un collection item cuya sub-categoría no coincide con `restricted_to_sub_category_id` en una colección `single_category` THEN el Backend SHALL rechazar la operación con un error descriptivo
5. WHEN el usuario crea o edita una colección THEN el Frontend SHALL permitir capturar `theme`, `theme_description`, `goal_description`, `goal_items_count`, `display_order`, `is_public` e `is_active`
6. WHEN el usuario abre el detalle de una colección `multi_category` o `mixed` THEN el Frontend SHALL mostrar los items agrupados por categoría, con el conteo de items por grupo
7. WHEN el usuario consulta las estadísticas de una colección multi-categoría THEN el Backend SHALL retornar totales consolidados cross-category (`total_items`, `different_categories_count`, `total_invested`, `current_value`, `value_gain`, `roi_percentage`, `complete_items`, `graded_items`)
8. WHILE la colección no tiene items THE Frontend SHALL mostrar un estado vacío con acción para agregar el primer item
9. WHEN el Backend calcula estadísticas de colección sobre PostgreSQL THEN el Backend SHALL usar la vista `v_collection_stats`, y WHEN se ejecuta sobre SQLite en el entorno de test THEN el Backend SHALL calcular los mismos campos mediante consultas equivalentes en el service

### Requirement 2: Proveedores

**User Story:** Como coleccionista, quiero registrar los proveedores donde compro, para saber a quién le compré cada pieza y evaluar con quién conviene volver a operar.

#### Acceptance Criteria

1. WHEN el usuario crea un proveedor con `name` no vacío y `type` dentro de `online`, `physical_store`, `marketplace`, `private_seller` o `auction` THEN el Backend SHALL persistir el proveedor y retornar código 201
2. IF el usuario crea un proveedor con `name` vacío o solo espacios THEN el Backend SHALL rechazar la operación con código 422 y un mensaje de validación
3. IF el usuario crea un proveedor con un `type` no permitido THEN el Backend SHALL rechazar la operación con código 422
4. WHEN el usuario asigna un `rating` al proveedor THEN el Backend SHALL aceptar valores entre 0.00 y 5.00 inclusive y rechazar valores fuera de ese rango
5. WHEN el usuario edita un proveedor THEN el Backend SHALL actualizar `country`, `city`, `address`, `website`, `email`, `phone`, `marketplace_url`, `social_media`, `notes`, `is_favorite` e `is_active`
6. WHEN el usuario marca o desmarca un proveedor como favorito THEN el Backend SHALL persistir `is_favorite` y el Frontend SHALL reflejar el cambio sin recargar la página
7. WHEN el usuario solicita el listado de proveedores con filtros de `type`, `country`, `is_favorite` o `is_active` THEN el Backend SHALL retornar únicamente los proveedores que cumplen todos los filtros aplicados
8. WHEN el usuario solicita el listado de proveedores THEN el Backend SHALL soportar paginación mediante `skip` y `limit`
9. WHEN el usuario consulta el historial de compras de un proveedor THEN el Backend SHALL retornar los collection items cuyo `supplier_id` coincide, con `purchase_date`, `purchase_price` y `purchase_currency`
10. WHEN el usuario elimina un proveedor referenciado por collection items, wishlist sightings o accesorios THEN el Backend SHALL preservar la integridad referencial y retornar un resultado determinista documentado (rechazo con error o desvinculación), sin dejar referencias inválidas

### Requirement 3: Wishlist

**User Story:** Como coleccionista, quiero mantener una lista de deseos con prioridades y presupuesto, para enfocar mis compras en lo que más quiero y no exceder lo que puedo gastar.

#### Acceptance Criteria

1. WHEN el usuario crea un wishlist item con `catalog_item_id` existente THEN el Backend SHALL persistirlo y retornar código 201
2. IF el usuario crea un wishlist item con un `catalog_item_id` o `collection_id` inexistente THEN el Backend SHALL rechazar la operación con código 404 y un mensaje descriptivo
3. WHEN el usuario crea o edita un wishlist item THEN el Backend SHALL aceptar `desired_condition`, `desired_condition_min`, `must_be_complete`, `desired_completeness_description`, `max_price`, `currency`, `specific_variant_required`, `variant_description`, `notes`, `search_notes`, `tags` e `is_active`
4. WHEN el usuario asigna `priority` THEN el Backend SHALL aceptar valores enteros de 1 a 5 inclusive y rechazar valores fuera de ese rango con código 422
5. WHEN el usuario asigna `urgency` THEN el Backend SHALL aceptar únicamente `low`, `medium`, `high` o `critical` y rechazar otros valores con código 422
6. WHEN el usuario solicita el listado de wishlist items con filtros de `collection_id`, `priority`, `urgency`, `is_active` o `is_acquired` THEN el Backend SHALL retornar únicamente los items que cumplen todos los filtros aplicados
7. WHEN el usuario marca un wishlist item como adquirido indicando el collection item resultante THEN el Backend SHALL establecer `is_acquired` en verdadero, registrar `acquired_date` y guardar `acquired_collection_item_id`
8. WHEN un wishlist item queda marcado como adquirido THEN el Backend SHALL excluirlo del listado por defecto de deseos pendientes
9. IF el usuario intenta marcar como adquirido un wishlist item ya adquirido THEN el Backend SHALL rechazar la operación con un error descriptivo y conservar el `acquired_collection_item_id` original
10. WHEN el usuario navega a `/wishlist` THEN el Frontend SHALL listar los wishlist items con prioridad, urgencia, presupuesto máximo y estado, y mostrar un estado vacío cuando no existan items

### Requirement 4: Avistamientos de wishlist

**User Story:** Como coleccionista, quiero registrar los avistamientos de las piezas que busco, para comparar precios y decidir cuándo y a quién comprar.

#### Acceptance Criteria

1. WHEN el usuario registra un avistamiento de un wishlist item con `price` presente THEN el Backend SHALL persistirlo y retornar código 201
2. IF el usuario registra un avistamiento sin `price` THEN el Backend SHALL rechazar la operación con código 422
3. WHEN el usuario registra o edita un avistamiento THEN el Backend SHALL aceptar `sighted_at`, `supplier_id`, `location_description`, `url`, `currency`, `condition`, `is_complete`, `description`, `image_urls`, `is_available`, `quantity_available` y `last_checked_at`
4. WHEN el usuario registra el seguimiento de contacto de un avistamiento THEN el Backend SHALL persistir `contacted`, `contacted_at`, `contact_method` y `response_notes`
5. WHEN el usuario registra una decisión sobre un avistamiento THEN el Backend SHALL aceptar únicamente `interested`, `pass`, `waiting`, `negotiating`, `purchased` o `lost`, y persistir `decision_notes` y `decision_date`
6. WHEN el usuario elimina un avistamiento THEN el Backend SHALL eliminarlo y retornar código 204
7. WHEN el usuario consulta un wishlist item con avistamientos THEN el Backend SHALL retornar el precio promedio, el precio mínimo, el precio máximo, `total_sightings` y `available_sightings`
8. WHILE un wishlist item no tiene avistamientos THE Backend SHALL retornar los agregados de precio como nulos y los conteos en cero
9. WHEN el Backend calcula los agregados de precio sobre PostgreSQL THEN el Backend SHALL usar la vista `v_wishlist_with_avg_price`, y WHEN se ejecuta sobre SQLite en el entorno de test THEN el Backend SHALL calcular los mismos agregados mediante consultas equivalentes en el service
10. WHEN el usuario navega a `/wishlist/:id` THEN el Frontend SHALL listar los avistamientos ordenados por `sighted_at` descendente y mostrar los agregados de precio

### Requirement 5: Componentes de items

**User Story:** Como coleccionista, quiero registrar qué componentes tiene cada pieza (caja, manual, inserto), para conocer el grado de completitud real de mi colección.

#### Acceptance Criteria

1. WHEN el usuario abre el registro de componentes de un collection item THEN el Backend SHALL retornar los `standard_components` definidos para la sub-categoría del item como plantilla inicial
2. WHEN el usuario guarda el estado de un componente THEN el Backend SHALL persistir en `item_components` los campos `standard_component_id`, `component_name`, `component_type`, `is_present`, `condition`, `condition_notes` y `variant_description`
3. WHEN el usuario registra un componente que no existe en los `standard_components` de la sub-categoría THEN el Backend SHALL aceptarlo con `standard_component_id` nulo y `component_name` obligatorio
4. IF el usuario guarda un componente con `component_name` vacío y sin `standard_component_id` THEN el Backend SHALL rechazar la operación con código 422
5. WHEN todos los componentes marcados como requeridos de la sub-categoría tienen `is_present` en verdadero THEN el Backend SHALL considerar el collection item como completo
6. WHEN al menos un componente requerido tiene `is_present` en falso THEN el Backend SHALL considerar el collection item como incompleto y reflejarlo en el conteo `complete_items` de las estadísticas de la colección
7. WHEN el usuario modifica la presencia de un componente THEN el Frontend SHALL actualizar el indicador de completitud del item sin recargar la página
8. WHEN el usuario elimina un registro de componente THEN el Backend SHALL eliminarlo y recalcular la completitud del item

### Requirement 6: Búsqueda avanzada

**User Story:** Como coleccionista con miles de items en catálogo, quiero buscar por texto libre y filtrar por múltiples criterios, para encontrar una pieza concreta en segundos.

#### Acceptance Criteria

1. WHEN el usuario ejecuta una búsqueda de texto sobre catalog items en PostgreSQL THEN el Backend SHALL consultar la columna `search_vector` y retornar los resultados ordenados por relevancia descendente
2. WHEN dos catalog items coinciden con el término buscado y uno coincide en `title` mientras el otro coincide solo en `description` THEN el Backend SHALL ordenar primero el que coincide en `title`, conforme a los pesos A/B/C del trigger `catalog_items_search_vector_trigger`
3. WHEN el usuario ejecuta una búsqueda con un término mal escrito en PostgreSQL THEN el Backend SHALL retornar coincidencias aproximadas por similitud de título usando `pg_trgm`, con un umbral de similitud configurable
4. WHEN el Backend ejecuta una búsqueda sobre SQLite en el entorno de test THEN el Backend SHALL degradar explícitamente a una búsqueda `LIKE`/`ILIKE` sobre `title`, `subtitle` y `alternate_titles`, e indicar en la respuesta que el modo de búsqueda es degradado
5. WHEN el usuario aplica filtros de `main_category_id`, `sub_category_id`, `language`, `region`, `manufacturer`, `publisher`, `developer`, `brand`, `rarity`, año mínimo o año máximo THEN el Backend SHALL retornar únicamente los catalog items que cumplen simultáneamente todos los filtros aplicados
6. WHEN el usuario combina un término de búsqueda con uno o más filtros THEN el Backend SHALL aplicar los filtros sobre el conjunto de resultados de la búsqueda de texto y conservar el orden por relevancia
7. WHEN una búsqueda no produce resultados THEN el Backend SHALL retornar una lista vacía con código 200 y el Frontend SHALL mostrar un estado vacío con sugerencia de ampliar o quitar filtros
8. WHEN el usuario solicita resultados de búsqueda THEN el Backend SHALL soportar paginación mediante `skip` y `limit` y retornar el total de coincidencias
9. WHEN el usuario modifica el término de búsqueda en el Frontend THEN el Frontend SHALL aplicar debounce antes de emitir la consulta al Backend
10. WHEN el usuario limpia los filtros THEN el Frontend SHALL restaurar el listado sin filtros y anunciar el cambio de cantidad de resultados a lectores de pantalla

### Requirement 7: Estadísticas

**User Story:** Como coleccionista, quiero ver estadísticas de mi colección, para entender cuánto invertí, cuánto vale hoy y cómo evoluciona.

#### Acceptance Criteria

1. WHEN el usuario consulta el endpoint de dashboard THEN el Backend SHALL retornar el total de items, la valorización total, el ROI general, las últimas adquisiciones, los items más valiosos y los wishlist items de alta prioridad
2. WHEN el usuario consulta el endpoint de estadísticas por colección THEN el Backend SHALL retornar, para cada colección activa, `total_items`, `total_invested`, `current_value`, `value_gain` y `roi_percentage`
3. WHEN el usuario consulta el endpoint de valorización THEN el Backend SHALL retornar la inversión total, el valor de mercado actual, la ganancia absoluta y el ROI porcentual
4. WHEN el usuario consulta el endpoint de categorías THEN el Backend SHALL retornar el conteo de items y el valor acumulado agrupados por categoría principal
5. WHEN el usuario consulta el endpoint de timeline THEN el Backend SHALL retornar las adquisiciones agregadas por período, con conteo de items y monto invertido por período
6. WHEN un collection item no tiene `purchase_price` THEN el Backend SHALL excluir ese item del cálculo de inversión sin producir error
7. WHEN la inversión total es cero THEN el Backend SHALL retornar el ROI como nulo en lugar de producir una división por cero
8. WHEN el usuario navega a `/stats` THEN el Frontend SHALL mostrar las métricas del dashboard y los desgloses por colección y categoría
9. WHILE no existen colecciones ni items THE Frontend SHALL mostrar un estado vacío en `/stats` en lugar de métricas en cero sin contexto
10. IF una consulta de estadísticas falla THEN el Frontend SHALL mostrar un mensaje de error accesible con opción de reintentar

### Requirement 8: Dark mode accesible

**User Story:** Como usuario que colecciona de noche, quiero un modo oscuro accesible, para usar la aplicación sin fatiga visual.

#### Acceptance Criteria

1. WHEN el usuario abre la aplicación por primera vez sin preferencia guardada THEN el Frontend SHALL aplicar el tema indicado por `prefers-color-scheme` del sistema operativo
2. WHEN el usuario selecciona explícitamente un tema THEN el Frontend SHALL persistir la preferencia en `localStorage` y aplicarla en las siguientes visitas por encima de `prefers-color-scheme`
3. WHEN el usuario alterna el tema THEN el Frontend SHALL actualizar todos los componentes visibles sin recargar la página
4. WHEN el usuario selecciona el modo automático THEN el Frontend SHALL eliminar la preferencia persistida y volver a seguir `prefers-color-scheme`
5. IF el valor almacenado en `localStorage` es inválido o `localStorage` no está disponible THEN el Frontend SHALL aplicar el tema por defecto sin producir un error visible al usuario
6. WHEN se ejecuta la auditoría automatizada de accesibilidad con axe-core sobre cada página en tema claro y en tema oscuro THEN el Sistema SHALL reportar cero violaciones de contraste de nivel WCAG 2.1 AA
7. WHEN el control de cambio de tema recibe el foco THEN el Frontend SHALL exponer su estado actual mediante atributos ARIA y ser operable con teclado

### Requirement 9: Idiomas adicionales (pt, fr, de)

**User Story:** Como usuario no hispanohablante ni anglófono, quiero la interfaz en portugués, francés o alemán, para usar la aplicación en mi idioma.

#### Acceptance Criteria

1. WHEN el usuario selecciona portugués, francés o alemán THEN el Frontend SHALL mostrar toda la interfaz en el idioma seleccionado
2. WHEN se comparan los archivos `translation.json` de los cinco idiomas (es, en, pt, fr, de) THEN el Sistema SHALL contener exactamente el mismo conjunto de claves en todos ellos, sin claves faltantes ni sobrantes
3. WHEN ninguna traducción existe para una clave en el idioma activo THEN el Frontend SHALL mostrar el valor del idioma de respaldo en lugar de la clave cruda
4. WHEN el usuario cambia el idioma THEN el Frontend SHALL persistir la preferencia y aplicarla en las siguientes visitas
5. WHEN el usuario abre el selector de idioma THEN el Frontend SHALL exponerlo como control accesible, operable con teclado, con el idioma activo anunciado a lectores de pantalla
6. WHEN el idioma activo cambia THEN el Frontend SHALL actualizar el atributo `lang` del documento HTML al código del idioma seleccionado

### Requirement 10: Historial de precios de catálogo

**User Story:** Como coleccionista, quiero llevar el historial de precios de mercado de cada item de catálogo, para saber cuánto vale realmente lo que tengo.

#### Acceptance Criteria

1. WHEN se ejecutan las consultas del Backend sobre `catalog_price_history` THEN el Backend SHALL disponer de un modelo SQLAlchemy `CatalogPriceHistory` que mapee `catalog_item_id`, `condition`, `is_complete`, `completeness_description`, `price`, `currency`, `source`, `source_url`, `price_date`, `region`, `notes` y `recorded_at`
2. WHEN el usuario registra un precio histórico con `catalog_item_id` existente, `price` y `price_date` THEN el Backend SHALL persistirlo y retornar código 201
3. IF el usuario registra un precio histórico que duplica la combinación `catalog_item_id`, `condition`, `is_complete`, `price_date` y `source` THEN el Backend SHALL rechazar la operación con un error de duplicado
4. IF el usuario registra un precio histórico con `price` negativo THEN el Backend SHALL rechazar la operación con código 422
5. WHEN el usuario consulta el historial de precios de un catalog item filtrando por `condition`, `is_complete`, `region` o rango de `price_date` THEN el Backend SHALL retornar únicamente los registros que cumplen todos los filtros, ordenados por `price_date` descendente
6. WHEN el usuario solicita actualizar el valor de mercado de un collection item desde el historial THEN el Backend SHALL tomar el registro de precio más reciente que coincida con la condición y completitud del item y escribir `current_market_value`, `current_value_currency`, `last_value_update` y `value_source`
7. IF no existe ningún precio histórico compatible con la condición y completitud del collection item THEN el Backend SHALL dejar `current_market_value` sin modificar y retornar un resultado que indique que no hubo actualización
8. WHEN el valor de mercado de un collection item se actualiza THEN el Backend SHALL reflejar el nuevo valor en los cálculos de valorización y ROI de las estadísticas
9. WHEN el usuario visualiza un catalog item en el Frontend THEN el Frontend SHALL mostrar el historial de precios y el último precio conocido por condición

### Requirement 11: Transacciones de items

**User Story:** Como coleccionista, quiero registrar todas las transacciones de mis items (compras, ventas, envíos, gradings), para conocer mi inversión real y mi rentabilidad efectiva.

#### Acceptance Criteria

1. WHEN se ejecutan las consultas del Backend sobre `item_transactions` THEN el Backend SHALL disponer de un modelo SQLAlchemy `ItemTransaction` que mapee `transaction_type`, `transaction_date`, `amount`, `currency`, `shipping_cost`, `tax_amount`, `other_fees`, `total_amount`, `supplier_id`, `counterpart_name`, `invoice_number`, `receipt_path`, `payment_method` y `notes`
2. WHEN el usuario registra una transacción con `transaction_type` dentro de `purchase`, `sale`, `trade_in`, `trade_out`, `gift_received`, `gift_given`, `repair`, `appraisal`, `grading` o `insurance_claim` THEN el Backend SHALL persistirla y retornar código 201
3. IF el usuario registra una transacción con un `transaction_type` no permitido THEN el Backend SHALL rechazar la operación con código 422
4. WHEN el Backend persiste una transacción en PostgreSQL THEN el Backend SHALL leer `total_amount` desde la columna `GENERATED`, y WHEN la persiste en SQLite en el entorno de test THEN el Backend SHALL calcular `total_amount` como la suma de `amount`, `shipping_cost`, `tax_amount` y `other_fees`, obteniendo el mismo resultado en ambos entornos
5. WHEN alguno de los campos `shipping_cost`, `tax_amount` u `other_fees` es nulo THEN el Backend SHALL tratarlo como cero en el cálculo de `total_amount`
6. WHEN el usuario consulta las transacciones de un collection item THEN el Backend SHALL retornarlas ordenadas por `transaction_date` descendente, con el total por transacción
7. WHEN el usuario consulta la inversión real de un collection item THEN el Backend SHALL calcularla como la suma de los `total_amount` de las transacciones de egreso menos la suma de los `total_amount` de las transacciones de ingreso
8. WHEN existen transacciones para un collection item THEN el Backend SHALL calcular el ROI del item a partir de la inversión real derivada de transacciones en lugar de `purchase_price`
9. WHEN el usuario elimina una transacción THEN el Backend SHALL eliminarla y recalcular la inversión real y el ROI del item

### Requirement 12: Accesorios y stock

**User Story:** Como coleccionista, quiero administrar mi stock de accesorios (fundas, cajas protectoras) y asignarlos a mis piezas, para saber cuántos me quedan y cuándo reponer.

#### Acceptance Criteria

1. WHEN el usuario crea un accesorio con `name` no vacío y `quantity_total` mayor o igual a cero THEN el Backend SHALL persistirlo y retornar código 201
2. IF el usuario crea un accesorio con `quantity_total` negativo o `name` vacío THEN el Backend SHALL rechazar la operación con código 422
3. WHEN el usuario crea o edita un accesorio THEN el Backend SHALL aceptar `category`, `subcategory`, `compatible_sub_categories`, `size_specifications`, `minimum_stock_alert`, `reorder_quantity`, `unit_cost`, `currency`, `supplier_id`, `supplier_sku` y `supplier_url`
4. WHEN se ejecutan las consultas del Backend sobre `item_accessories` THEN el Backend SHALL disponer de un modelo SQLAlchemy `ItemAccessory` que mapee `collection_item_id`, `accessory_id`, `quantity_used`, `assigned_at` y `notes`
5. WHEN el usuario asigna un accesorio a un collection item THEN el Backend SHALL crear el registro en `item_accessories` e incrementar `quantity_in_use` del accesorio en `quantity_used`
6. WHEN el usuario desasigna un accesorio de un collection item THEN el Backend SHALL eliminar el registro y decrementar `quantity_in_use` en la cantidad previamente asignada
7. IF el usuario asigna el mismo accesorio al mismo collection item más de una vez THEN el Backend SHALL rechazar la operación por violación de la restricción de unicidad y retornar un error descriptivo
8. IF el usuario asigna una cantidad mayor que `quantity_available` THEN el Backend SHALL rechazar la operación con un error descriptivo y dejar `quantity_in_use` sin modificar
9. WHEN el Backend opera sobre PostgreSQL THEN el ajuste de `quantity_in_use` SHALL provenir del trigger `update_accessory_stock_trigger` y `quantity_available` SHALL leerse de la columna `GENERATED`, y WHEN opera sobre SQLite en el entorno de test THEN el service SHALL producir los mismos valores de `quantity_in_use` y `quantity_available` mediante lógica equivalente
10. WHEN el usuario consulta el listado de stock bajo THEN el Backend SHALL retornar los accesorios cuyo `quantity_available` es menor o igual a `minimum_stock_alert`, con la `reorder_quantity` sugerida
11. WHEN el usuario navega a `/accessories` THEN el Frontend SHALL listar los accesorios con total, en uso y disponible, y destacar visualmente y textualmente los que están en stock bajo

### Requirement 13: Exportación de datos

**User Story:** Como coleccionista, quiero exportar mis colecciones y catálogos, para tener una copia legible de mis datos y poder migrarlos.

#### Acceptance Criteria

1. WHEN el usuario solicita la exportación de una colección THEN el Backend SHALL retornar un documento JSON que incluya los datos de la colección, sus collection items, sus componentes y las referencias a los catalog items asociados
2. WHEN el usuario solicita la exportación de un catálogo en formato JSON THEN el Backend SHALL retornar un documento JSON con los datos del catálogo y todos sus catalog items
3. WHEN el usuario solicita la exportación de un catálogo en formato CSV THEN el Backend SHALL retornar un CSV cuya fila de encabezado sea compatible con el importador CSV existente
4. IF el usuario solicita la exportación de una colección o catálogo inexistente THEN el Backend SHALL retornar código 404 con un mensaje descriptivo
5. WHEN el Backend responde una exportación THEN el Backend SHALL incluir los encabezados HTTP de tipo de contenido y de nombre de archivo que permitan la descarga directa
6. WHEN el documento JSON exportado se vuelve a importar THEN el Sistema SHALL producir un conjunto de entidades equivalente al original en los campos exportados
7. WHEN el usuario dispara una exportación desde `/export` THEN el Frontend SHALL iniciar la descarga del archivo y mostrar un indicador de progreso mientras la exportación está en curso
8. IF la exportación falla THEN el Frontend SHALL mostrar un mensaje de error accesible con opción de reintentar

### Requirement 14: Importación de datos

**User Story:** Como coleccionista que viene de otra herramienta, quiero importar mis datos desde JSON con vista previa, para migrar sin duplicar ni corromper información.

#### Acceptance Criteria

1. WHEN el usuario sube un archivo JSON de colección, catálogo o wishlist THEN el Backend SHALL validar la estructura del documento antes de persistir cualquier dato
2. IF el archivo subido no es JSON válido o no corresponde a ninguna estructura soportada THEN el Backend SHALL rechazar la importación con código 422 y un mensaje que identifique el problema
3. WHEN el usuario solicita la vista previa de una importación THEN el Backend SHALL retornar el conteo de entidades a crear, a actualizar y a omitir, sin escribir en la base de datos
4. WHEN el Backend valida una importación THEN el Backend SHALL reportar los errores por fila o por entidad, indicando identificador y motivo de cada error
5. WHEN el Backend ejecuta una importación THEN el Backend SHALL retornar el resultado usando el mismo patrón `BatchImportResult` empleado por el importador CSV existente
6. WHEN una entidad importada coincide con una existente según su clave natural THEN el Backend SHALL actualizarla en lugar de crear un duplicado
7. WHEN una importación contiene entidades válidas e inválidas THEN el Backend SHALL persistir las válidas, omitir las inválidas y reportar ambas cantidades
8. WHEN el mismo archivo se importa dos veces consecutivas THEN el Backend SHALL producir el mismo estado final que tras la primera importación, sin crear entidades duplicadas
9. WHEN el usuario navega a `/import` THEN el Frontend SHALL guiarlo por el flujo de subir archivo, revisar la vista previa, confirmar y ver el reporte final de resultados
10. IF el usuario cancela en la etapa de vista previa THEN el Sistema SHALL descartar la importación sin modificar ningún dato

### Requirement 15: Backups automáticos

**User Story:** Como usuario self-hosted, quiero backups automáticos configurables, para no perder mi colección si falla el servidor.

#### Acceptance Criteria

1. WHEN el usuario solicita crear un backup manual THEN el Backend SHALL generar un archivo de backup en el directorio indicado por `BACKUP_DIR` que contenga el dump de la base de datos, las imágenes y la configuración de la aplicación
2. WHEN un backup se crea correctamente THEN el Backend SHALL registrar su identificador, fecha de creación, tamaño y contenido incluido
3. WHEN el usuario solicita el listado de backups THEN el Backend SHALL retornar los backups disponibles ordenados por fecha de creación descendente
4. WHEN el usuario solicita descargar un backup existente THEN el Backend SHALL retornar el archivo con los encabezados HTTP que permitan la descarga directa
5. IF el usuario solicita descargar o restaurar un backup inexistente THEN el Backend SHALL retornar código 404 con un mensaje descriptivo
6. WHEN el usuario solicita restaurar un backup válido THEN el Backend SHALL restaurar la base de datos, las imágenes y la configuración contenidas en el archivo, y reportar el resultado de la operación
7. IF el archivo de backup está corrupto o incompleto THEN el Backend SHALL abortar la restauración sin modificar los datos actuales y retornar un error descriptivo
8. WHEN el usuario configura la frecuencia de backup THEN el Backend SHALL aceptar únicamente `daily`, `weekly` o `monthly` y persistir la configuración junto con el número de backups a retener
9. WHEN el usuario consulta la configuración de backups THEN el Backend SHALL retornar la frecuencia activa, la retención configurada y la fecha de la próxima ejecución programada
10. WHEN se crea un backup automático y la cantidad de backups almacenados excede la retención configurada THEN el Backend SHALL eliminar los backups más antiguos hasta cumplir la retención
11. IF la creación de un backup automático falla THEN el Backend SHALL registrar el error y conservar los backups existentes sin eliminarlos
12. WHEN el usuario navega a `/settings/backups` THEN el Frontend SHALL permitir crear, listar, descargar y restaurar backups y editar frecuencia y retención, solicitando confirmación explícita antes de restaurar

### Requirement 16: Gráficos de valorización y timeline

**User Story:** Como coleccionista, quiero ver gráficos de la evolución de mi colección, para entender tendencias de un vistazo.

#### Acceptance Criteria

1. WHEN el usuario visualiza la sección de gráficos THEN el Frontend SHALL mostrar la valorización en el tiempo, la comparación de inversión frente a valor actual, la distribución por categoría y el timeline de adquisiciones
2. WHEN un gráfico se renderiza THEN el Frontend SHALL exponer una alternativa textual equivalente, en forma de tabla accesible o resumen, con los mismos datos representados
3. WHEN un gráfico distingue series THEN el Frontend SHALL diferenciarlas por al menos un atributo adicional al color, como etiqueta, patrón o forma de marcador
4. WHEN un gráfico no tiene datos suficientes THEN el Frontend SHALL mostrar un estado vacío explicativo en lugar de un lienzo en blanco
5. WHEN el usuario navega con teclado por la sección de gráficos THEN el Frontend SHALL permitir alcanzar la alternativa textual de cada gráfico sin usar el ratón
6. WHEN se ejecuta la auditoría automatizada con axe-core sobre la sección de gráficos THEN el Sistema SHALL reportar cero violaciones de nivel WCAG 2.1 AA
7. IF la carga de los datos de un gráfico falla THEN el Frontend SHALL mostrar un mensaje de error accesible para ese gráfico sin afectar los demás

### Requirement 17: PWA y modo sin conexión

**User Story:** Como coleccionista que revisa su colección en tiendas físicas, quiero instalar la aplicación y usarla sin conexión, para consultar y agregar items aunque no tenga señal.

#### Acceptance Criteria

1. WHEN el usuario abre la aplicación en un navegador compatible THEN el Sistema SHALL exponer un manifest de aplicación web con nombre, iconos, color de tema y modo de visualización que permita la instalación en escritorio y en móvil
2. WHEN la aplicación se carga por primera vez con conexión THEN el Sistema SHALL registrar un service worker que cachee los recursos estáticos de la aplicación
3. WHILE el dispositivo está sin conexión THE Frontend SHALL permitir visualizar las colecciones, los collection items y las estadísticas previamente cacheadas
4. WHILE el dispositivo está sin conexión THE Frontend SHALL permitir buscar dentro de los datos de la colección cacheados
5. WHILE el dispositivo está sin conexión THE Frontend SHALL indicar de forma visible y anunciada a lectores de pantalla que la aplicación opera en modo sin conexión
6. WHEN el usuario crea o modifica un item sin conexión THEN el Frontend SHALL encolar la operación de forma persistente y confirmar al usuario que quedó pendiente de sincronización
7. WHEN la conexión se restablece THEN el Frontend SHALL enviar las operaciones encoladas al Backend en el orden en que fueron creadas y vaciar la cola de las operaciones aplicadas correctamente
8. IF una operación encolada afecta a una entidad modificada en el servidor después de que la operación fue creada THEN el Sistema SHALL conservar el cambio del servidor, marcar la operación como en conflicto y presentarla al usuario para su resolución
9. IF una operación encolada es rechazada por el Backend por un error de validación THEN el Frontend SHALL mantenerla marcada como fallida con el motivo y no reintentarla de forma indefinida
10. WHEN el usuario consulta el estado de sincronización THEN el Frontend SHALL mostrar la cantidad de operaciones pendientes, aplicadas y en conflicto

### Requirement 18: Accesibilidad avanzada y auditoría WCAG 2.1 AA

**User Story:** Como usuario con discapacidad, quiero que toda la aplicación cumpla WCAG 2.1 AA, para poder usarla con mis tecnologías asistivas.

#### Acceptance Criteria

1. WHEN el sistema operativo del usuario indica `prefers-reduced-motion` THEN el Frontend SHALL suprimir o reducir las animaciones y transiciones no esenciales
2. WHEN el Sistema produce un mensaje de estado, éxito o error THEN el Frontend SHALL anunciarlo mediante una live region ARIA con el nivel de urgencia adecuado
3. WHEN el usuario enfoca un elemento con tooltip THEN el Frontend SHALL mostrar el tooltip mediante foco de teclado además de con el puntero, y asociarlo al elemento por atributos ARIA
4. WHEN el usuario aplica zoom del navegador al 200 por ciento THEN el Frontend SHALL mantener todo el contenido y los controles accesibles sin pérdida de funcionalidad ni desplazamiento horizontal en dos dimensiones
5. WHEN el usuario navega con teclado THEN el Frontend SHALL mostrar un indicador de foco visible en todos los elementos interactivos y ofrecer un enlace de salto al contenido principal
6. WHEN el usuario abre un modal o diálogo THEN el Frontend SHALL confinar el foco dentro del diálogo, cerrarlo con Escape y devolver el foco al elemento que lo abrió
7. WHEN se ejecuta la auditoría automatizada de accesibilidad sobre cada página y componente nuevo THEN el Sistema SHALL reportar cero violaciones de nivel WCAG 2.1 AA
8. WHEN se documenta el resultado de la auditoría THEN el Sistema SHALL declarar explícitamente que la validación completa de conformidad WCAG 2.1 AA requiere pruebas manuales con tecnologías asistivas y revisión experta, que la auditoría automatizada no sustituye

### Requirement 19: Estándares transversales

**User Story:** Como mantenedor del proyecto, quiero que todo lo construido en estas fases respete los estándares transversales de H.O.A.R.D., para que el código sea sostenible y la calidad no dependa de cada feature.

#### Acceptance Criteria

1. WHEN se agrega cualquier texto visible en el Frontend THEN el Sistema SHALL definir su clave de traducción en los cinco archivos de idioma (es, en, pt, fr, de)
2. WHEN se crea un componente React nuevo THEN el Sistema SHALL incluir un test automatizado con axe-core que verifique cero violaciones de accesibilidad para ese componente
3. WHEN se crea un componente React nuevo con elementos interactivos THEN el Sistema SHALL incluir tests que verifiquen su operación mediante teclado y la presencia de los roles y etiquetas ARIA correspondientes
4. WHEN se ejecuta la suite de tests sobre el código de los Requirements 1 a 9 THEN el Sistema SHALL alcanzar una cobertura mayor al 80 por ciento
5. WHEN se ejecuta la suite de tests sobre el código de los Requirements 10 a 18 THEN el Sistema SHALL alcanzar una cobertura mayor al 85 por ciento
6. WHEN se implementa una regla de negocio nueva en el Backend THEN el Sistema SHALL ubicarla en la capa de services, dejando las routes limitadas a validación de entrada, delegación y traducción de errores a respuestas HTTP
7. WHEN se agrega código TypeScript THEN el Sistema SHALL compilar en modo estricto sin utilizar el tipo `any`
8. WHEN se ejecuta la suite de tests THEN el Sistema SHALL correr sobre SQLite in-memory, y todo criterio que dependa de funcionalidad exclusiva de PostgreSQL SHALL verificarse con el comportamiento equivalente declarado para el entorno de test
9. WHEN se agrega un endpoint nuevo THEN el Sistema SHALL incluir tests de integración que verifiquen códigos de estado, formato de respuesta y manejo de errores
10. WHEN se agrega un service nuevo THEN el Sistema SHALL incluir tests unitarios que cubran los casos válidos, los casos límite y las condiciones de error

---

## Fuera de Alcance

Los siguientes elementos quedan explícitamente excluidos de este spec:

- **Google Drive, Dropbox y AWS S3 como destino de backups.** Corresponden a la Fase 4 (Integraciones). En este spec el único destino de backup es el sistema de archivos local indicado por `BACKUP_DIR`.
- **Integración con APIs externas (IGDB, PriceCharting, Discogs).** Corresponden a la Fase 4. El historial de precios del Requirement 10 se alimenta por carga manual o import, no por consulta automática a terceros.
- **Portal de contribución de traducciones.** Excluido. Existe una discrepancia documental: `KIRO_HANDOFF.md` lo ubica en la Fase 4 mientras que `README.md` lo menciona en la Fase 3. Se resuelve a favor de la Fase 4 y este spec se limita a agregar los idiomas pt, fr y de mediante archivos de traducción versionados en el repositorio.
- **Multi-usuario, autenticación JWT, permisos y rate limiting.** Corresponden a la Fase 5 (Production). Este spec asume una instancia self-hosted de un solo usuario sin capa de autenticación.
- **Notificaciones push y notification service.** Marcado como "Futuro" en `README.md`. Las alertas de stock bajo del Requirement 12 se resuelven mediante consulta y presentación en la interfaz, no mediante notificaciones enviadas al usuario.
- **Exportación de estadísticas a PDF y Excel.** Excluida. La exportación del Requirement 13 cubre únicamente JSON y CSV de colecciones y catálogos.
- **Tests de layout RTL (árabe, hebreo).** Excluidos porque este spec no agrega idiomas de escritura derecha a izquierda; los cinco idiomas soportados son de escritura izquierda a derecha.
- **Procesamiento de imágenes (generación de thumbnails, watermark, deduplicación).** Excluido por no formar parte del roadmap de las Fases 2 y 3. Los backups del Requirement 15 copian los archivos de imagen tal como están almacenados, sin transformarlos.
