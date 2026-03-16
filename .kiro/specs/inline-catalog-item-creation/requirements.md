# Requisitos: Creación Inline de Catalog Items

## Contexto

Actualmente, cuando un usuario quiere agregar un ítem a su colección desde `CollectionDetailPage`, debe seleccionar un `CatalogItem` existente del catálogo. Si el ítem no existe en el catálogo, el usuario debe abandonar el flujo, navegar a la página del catálogo, crear el ítem allí, y luego volver a la colección para agregarlo. Este feature permite crear un nuevo `CatalogItem` directamente desde el formulario de agregar ítem a la colección (inline), sin interrumpir el flujo del usuario.

---

## Requirement 1

**User Story:** Como coleccionista, quiero poder crear un nuevo ítem de catálogo directamente desde el formulario de agregar ítem a mi colección, para no tener que abandonar el flujo cuando el ítem que busco no existe en el catálogo.

### Acceptance Criteria

1. WHEN el usuario está en el formulario de agregar ítem a una colección y el catalog item deseado no existe THEN el sistema SHALL mostrar una opción visible para crear un nuevo catalog item inline
2. WHEN el usuario hace clic en "Crear nuevo ítem de catálogo" THEN el sistema SHALL mostrar un formulario inline con los campos mínimos requeridos (título) y campos opcionales (subtítulo, descripción, fabricante, publisher, developer, marca, idioma, región, rareza)
3. WHEN el usuario envía el formulario de creación inline con un título válido THEN el sistema SHALL crear el CatalogItem en el backend y seleccionarlo automáticamente en el formulario de agregar ítem a la colección
4. WHEN el usuario envía el formulario de creación inline con un título vacío o solo espacios THEN el sistema SHALL rechazar la creación y mostrar un mensaje de error de validación
5. WHEN el CatalogItem se crea exitosamente inline THEN el sistema SHALL actualizar la lista de catalog items disponibles en el selector sin recargar la página

## Requirement 2

**User Story:** Como coleccionista, quiero que el formulario inline de creación de catalog item sea simple y rápido, para que no interrumpa mi flujo de agregar ítems a la colección.

### Acceptance Criteria

1. WHEN se muestra el formulario inline de creación THEN el sistema SHALL mostrar solo el campo título como obligatorio, con los demás campos colapsados u opcionales
2. WHEN el usuario cancela la creación inline THEN el sistema SHALL volver al estado anterior del formulario de agregar ítem sin perder los datos ya ingresados (condición, notas, precio)
3. WHEN el formulario inline está visible THEN el sistema SHALL enfocar automáticamente el campo de título para entrada inmediata
4. WHEN la creación inline está en progreso THEN el sistema SHALL mostrar un indicador de carga y deshabilitar el botón de envío para prevenir envíos duplicados

## Requirement 3

**User Story:** Como sistema, quiero validar los datos del nuevo catalog item tanto en frontend como en backend, para mantener la integridad de los datos del catálogo.

### Acceptance Criteria

1. WHEN el backend recibe una solicitud de creación de catalog item THEN el sistema SHALL validar que el título no esté vacío y no exceda 500 caracteres
2. WHEN el backend recibe una solicitud de creación de catalog item THEN el sistema SHALL validar que el catalog_id referenciado exista
3. WHEN la validación del backend falla THEN el sistema SHALL retornar un error descriptivo que el frontend pueda mostrar al usuario
4. WHEN el frontend envía el formulario THEN el sistema SHALL realizar validación local antes de enviar al backend

## Requirement 4

**User Story:** Como coleccionista, quiero que la interfaz de creación inline sea accesible, para poder usarla con teclado y lectores de pantalla.

### Acceptance Criteria

1. WHEN el formulario inline se muestra THEN el sistema SHALL ser navegable completamente por teclado (Tab, Enter, Escape)
2. WHEN hay errores de validación THEN el sistema SHALL anunciarlos a lectores de pantalla usando atributos ARIA apropiados
3. WHEN el usuario presiona Escape en el formulario inline THEN el sistema SHALL cerrar el formulario y devolver el foco al botón que lo abrió

## Requirement 5

**User Story:** Como coleccionista, quiero que la interfaz esté disponible en español e inglés, para poder usarla en mi idioma preferido.

### Acceptance Criteria

1. WHEN el formulario inline se muestra THEN el sistema SHALL mostrar todos los labels, placeholders y mensajes de error en el idioma activo (es/en)
2. WHEN cambia el idioma de la aplicación THEN el formulario inline SHALL reflejar el cambio inmediatamente
