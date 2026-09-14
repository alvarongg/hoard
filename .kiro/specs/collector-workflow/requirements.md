# Requerimientos — Flujo del coleccionista (collector-workflow)

## Introducción

Este spec convierte a H.O.A.R.D. en una herramienta de **organización** de la colección (no de especulación de precios). Cubre el flujo completo del coleccionista: encontrar un ítem en la búsqueda, saber si ya lo tiene, agregarlo a una colección con todos sus datos reales de ejemplar (original/bootleg, país de origen, estado, precio pagado, proveedor), o mandarlo a la wishlist de una colección y luego marcarlo "ya lo conseguí". Incorpora altas rápidas (proveedor, catálogo, ítem de catálogo) que dejan datos faltantes en una solapa de **Pendientes**, ubicación física libre, recordatorios de **mantenimiento** (p.ej. batería de cartuchos), y una consulta de precio **on-demand** contra PriceCharting (nunca masiva).

El objetivo es organizar cada colección de un coleccionista; el precio es solo una referencia puntual que el propio coleccionista dispara.

## Glosario

- **CatalogItem**: identidad del producto (título, región, fabricante). Es lo compartido/catalogable.
- **CollectionItem**: el EJEMPLAR concreto que posee el coleccionista (estado, precio pagado, proveedor, ubicación).
- **Catálogo (Catalog)**: agrupación de CatalogItems bajo una sub-categoría. Una colección puede tener varios catálogos asociados (N:M).
- **Pendiente**: registro de datos faltantes de una entidad (ítem, catálogo, proveedor) que el coleccionista puede completar después.

---

## Requerimiento 1 — Agregar a colección desde la búsqueda, con formulario completo del ejemplar

**Historia:** Como coleccionista, quiero, al entrar a un ítem encontrado en la búsqueda, agregarlo a una de mis colecciones eligiendo todos los datos del ejemplar, para registrar fielmente lo que poseo.

#### Criterios de aceptación
1. CUANDO el coleccionista abre un resultado de búsqueda ENTONCES el sistema DEBERÁ mostrar una página de detalle del CatalogItem con un botón "Agregar a colección".
2. CUANDO el coleccionista pulsa "Agregar a colección" ENTONCES el sistema DEBERÁ mostrar un formulario que permita elegir la colección destino y capturar: autenticidad (original/bootleg), país de origen, estado (condición), precio pagado + moneda, y proveedor.
3. CUANDO el coleccionista guarda el formulario ENTONCES el sistema DEBERÁ crear un CollectionItem persistiendo todos esos campos, incluyendo `supplier_id`, `is_authentic`, `country_of_origin`, `condition`, `purchase_price`, `purchase_currency`.
4. SI la colección destino es `single_category` Y el CatalogItem no pertenece a su sub-categoría permitida ENTONCES el sistema DEBERÁ rechazar el alta con un error de validación claro.
5. CUANDO el formulario referencia un proveedor que no existe ENTONCES el sistema DEBERÁ permitir dar de alta un proveedor rápido con solo nombre y país (ver Req 4).

---

## Requerimiento 2 — Alta rápida de proveedor con datos mínimos y su pendiente

**Historia:** Como coleccionista, quiero crear un proveedor al vuelo con solo nombre y país mientras cargo un ítem, para no interrumpir el flujo, y completar el resto después.

#### Criterios de aceptación
1. CUANDO el coleccionista no encuentra el proveedor ENTONCES el sistema DEBERÁ permitir crear uno con `name` (requerido) y `country` (opcional) sin exigir más campos.
2. CUANDO se crea un proveedor por alta rápida ENTONCES el sistema DEBERÁ registrar un Pendiente con los campos faltantes recomendados (tipo, ciudad, contacto).
3. CUANDO se crea el proveedor rápido ENTONCES el sistema DEBERÁ seleccionarlo automáticamente en el formulario de ítem en curso.

---

## Requerimiento 3 — Catálogos como parte del filtro de búsqueda y detalle de ítem con "¿ya lo tengo?"

**Historia:** Como coleccionista, quiero que la vista de Catálogos se integre al filtro de búsqueda, y que al entrar a un ítem vea toda su información y si ya lo tengo en alguna colección.

#### Criterios de aceptación
1. CUANDO el coleccionista usa la búsqueda ENTONCES el sistema DEBERÁ ofrecer un filtro por catálogo (y por sistema/sub-categoría) que restrinja los resultados; la vista de Catálogos DEBERÁ ser alcanzable desde el mismo buscador (merge de navegación).
2. CUANDO el coleccionista entra directamente a un catálogo y de ahí a un ítem ENTONCES el sistema DEBERÁ mostrar la página de detalle del CatalogItem con toda su información asociada.
3. CUANDO el coleccionista ve el detalle de un CatalogItem ENTONCES el sistema DEBERÁ indicar si ya lo posee, mostrando en qué colección(es) y en qué CollectionItem(s).
4. CUANDO no posee el ítem ENTONCES el sistema DEBERÁ ofrecer "Agregar a colección" (Req 1) y "Agregar a wishlist" (Req 7).

---

## Requerimiento 4 — Solapa de Pendientes (datos faltantes)

**Historia:** Como coleccionista, quiero una solapa de Pendientes donde vea qué datos faltan en ítems, catálogos y proveedores, para completarlos cuando pueda.

#### Criterios de aceptación
1. CUANDO una entidad (CollectionItem, Catalog, CatalogItem o Supplier) se crea por alta rápida con datos mínimos ENTONCES el sistema DEBERÁ registrar un Pendiente que referencie la entidad y liste los campos faltantes.
2. CUANDO el coleccionista abre la solapa de Pendientes ENTONCES el sistema DEBERÁ listar todos los pendientes abiertos agrupados por tipo de entidad.
3. CUANDO el coleccionista completa los datos faltantes de un pendiente ENTONCES el sistema DEBERÁ actualizar la entidad y marcar el pendiente como resuelto.
4. CUANDO todos los campos faltantes de un pendiente quedan completos ENTONCES el sistema DEBERÁ cerrar el pendiente automáticamente.

---

## Requerimiento 5 — Colecciones con catálogos asociados (N:M) y alta rápida de catálogo

**Historia:** Como coleccionista, quiero entrar a mis colecciones, ver todos sus ítems, y que cada colección tenga al menos un catálogo asociado, pudiendo crear un catálogo rápido con nombre y temática.

#### Criterios de aceptación
1. CUANDO el coleccionista abre una colección ENTONCES el sistema DEBERÁ listar todos los CollectionItems asociados con su título resuelto, estado y datos clave.
2. CUANDO el coleccionista gestiona una colección ENTONCES el sistema DEBERÁ permitir asociar y desasociar uno o más catálogos (relación N:M mediante `collection_catalogs`).
3. CUANDO una colección no tiene ningún catálogo asociado y el coleccionista intenta agregar un ítem ENTONCES el sistema DEBERÁ requerir/ofrecer asociar (o crear) al menos un catálogo primero.
4. CUANDO el catálogo buscado no existe ENTONCES el sistema DEBERÁ permitir crear un catálogo rápido con `name` y `tematica` (temática), resolviendo o creando la sub-categoría subyacente automáticamente, y registrando un Pendiente con los campos faltantes.
5. CUANDO se crea un catálogo rápido ENTONCES el sistema DEBERÁ asociarlo a la colección en curso y permitir luego entrar al catálogo para modificarlo y agregar ítems.

---

## Requerimiento 6 — Alta rápida de CatalogItem al agregar a colección

**Historia:** Como coleccionista, cuando agrego un ítem a una colección y no lo encuentro en el catálogo, quiero crear ese ítem de catálogo con datos mínimos y que se cree a la vez en el catálogo y en la colección.

#### Criterios de aceptación
1. CUANDO el coleccionista agrega un ítem a una colección y no existe en ningún catálogo asociado ENTONCES el sistema DEBERÁ permitir crear un CatalogItem con datos mínimos (`title` requerido) dentro de un catálogo asociado elegido.
2. CUANDO se crea el CatalogItem rápido ENTONCES el sistema DEBERÁ, en la misma operación, crear el CollectionItem correspondiente en la colección.
3. CUANDO se crea el CatalogItem rápido ENTONCES el sistema DEBERÁ registrar un Pendiente con los campos faltantes del ítem de catálogo (región, fabricante, fecha, etc.).

---

## Requerimiento 7 — Wishlist asociada a colección y flujo "ya lo conseguí"

**Historia:** Como coleccionista, quiero mandar un ítem a la wishlist de una colección desde la búsqueda, y luego, cuando lo consiga, cargarlo como ítem de colección desde la propia wishlist, decidiendo si lo quito de la wishlist.

#### Criterios de aceptación
1. CUANDO el coleccionista ve el detalle de un CatalogItem ENTONCES el sistema DEBERÁ ofrecer "Agregar a wishlist" eligiendo la colección a la que queda asociada la wishlist.
2. CUANDO el coleccionista abre un ítem de la wishlist ENTONCES el sistema DEBERÁ ofrecer la acción "Ya lo conseguí".
3. CUANDO el coleccionista pulsa "Ya lo conseguí" ENTONCES el sistema DEBERÁ mostrar el mismo formulario de alta de CollectionItem (Req 1), pre-cargado con la colección y el CatalogItem de la wishlist.
4. CUANDO el coleccionista finaliza ese formulario ENTONCES el sistema DEBERÁ crear el CollectionItem, marcar el WishlistItem como adquirido (`is_acquired`, `acquired_date`, `acquired_collection_item_id`), y ofrecer una opción final para **quitar o conservar** el ítem en la wishlist.
5. SI el coleccionista elige quitar de la wishlist ENTONCES el sistema DEBERÁ desactivar/eliminar el WishlistItem; SI elige conservar ENTONCES el sistema DEBERÁ dejarlo marcado como adquirido pero visible.

---

## Requerimiento 8 — Ubicación física libre

**Historia:** Como coleccionista, quiero anotar la ubicación física de cada ejemplar como texto libre, para encontrarlo en mi casa.

#### Criterios de aceptación
1. CUANDO el coleccionista carga o edita un CollectionItem ENTONCES el sistema DEBERÁ ofrecer un campo de ubicación física de texto libre (`storage_location`).
2. CUANDO el coleccionista guarda la ubicación ENTONCES el sistema DEBERÁ persistirla y mostrarla en el detalle del ítem.

---

## Requerimiento 9 — Recordatorio de mantenimiento (p.ej. batería)

**Historia:** Como coleccionista, quiero, si el ítem lo requiere, programar una revisión de mantenimiento (p.ej. cambiar la batería de cartuchos NES/Famicom/Game Boy), para conservar la colección.

#### Criterios de aceptación
1. CUANDO el coleccionista agrega o edita un CollectionItem ENTONCES el sistema DEBERÁ permitir marcar que el ítem requiere mantenimiento y programar una revisión con fecha objetivo, tipo (p.ej. "batería") y notas.
2. CUANDO existe una revisión programada ENTONCES el sistema DEBERÁ listarla y señalar cuáles están vencidas o próximas.
3. CUANDO el coleccionista completa una revisión ENTONCES el sistema DEBERÁ registrarla (fecha realizada, notas) y permitir programar la siguiente.
4. CUANDO NO se marca que el ítem requiere mantenimiento ENTONCES el sistema NO DEBERÁ crear ninguna revisión.

---

## Requerimiento 10 — Precio on-demand desde PriceCharting (nunca masivo)

**Historia:** Como coleccionista, quiero consultar puntualmente el precio de referencia de un ítem en PriceCharting cuando yo lo pido, sin que la app actualice precios masivamente.

#### Criterios de aceptación
1. CUANDO el coleccionista pulsa "Buscar precio" en un ítem ENTONCES el sistema DEBERÁ consultar PriceCharting SOLO para ese ítem, en ese momento.
2. CUANDO PriceCharting responde ENTONCES el sistema DEBERÁ guardar el resultado como un registro de historial de precios con `source="PriceCharting"` y `source_url`, y `price_date` = la fecha de la consulta.
3. CUANDO se muestra el historial de precios ENTONCES el sistema DEBERÁ calcularlo únicamente a partir de los precios que el coleccionista consultó/ingresó (no hay refresco automático ni backfill).
4. EN NINGÚN caso el sistema DEBERÁ ejecutar actualizaciones masivas o programadas de precios.
5. CUANDO se realiza la llamada saliente ENTONCES el sistema DEBERÁ restringir el host destino mediante una allowlist (guard anti-SSRF) y usar timeout.
