---
inclusion: fileMatch
fileMatchPattern: "**/*.tsx,**/*.jsx,**/locales/**,**/i18n/**"
---

# Accessibility & Internationalization Standards

## Accesibilidad (WCAG 2.1 AA)

H.O.A.R.D. DEBE ser accesible para todos. La accesibilidad no es opcional.

### HTML Semántico
- Usar elementos semánticos: `<main>`, `<nav>`, `<article>`, `<section>`, `<aside>`, `<header>`, `<footer>`
- Headings jerárquicos: un solo `<h1>` por página, luego `<h2>`, `<h3>` en orden
- Listas para grupos de items: `<ul>`, `<ol>`
- `<button>` para acciones, `<a>` para navegación (nunca al revés)
- `<table>` con `<thead>`, `<th scope>` para datos tabulares

### ARIA
- ARIA labels en elementos interactivos sin texto visible
- `aria-labelledby` para vincular headings con regiones
- `aria-describedby` para instrucciones adicionales en formularios
- `aria-live="polite"` para mensajes de estado y notificaciones
- `aria-expanded` en elementos colapsables (accordions, dropdowns)
- `aria-current="page"` en navegación para la página actual
- NO usar ARIA si el HTML semántico ya comunica el rol

### Navegación por Teclado
- Todo elemento interactivo accesible con Tab
- Skip links al inicio de la página: "Saltar al contenido principal"
- Focus visible en TODOS los elementos interactivos (outline nunca `none` sin alternativa)
- Orden de Tab lógico (no usar tabindex > 0)
- Escape cierra modales/dropdowns y devuelve focus al trigger
- Enter/Space activan botones
- Arrow keys para navegar dentro de componentes compuestos (tabs, menus)
- Focus trap en modales y dialogs (usar focus-trap-react)

### Contraste y Visual
- Contraste mínimo 4.5:1 para texto normal, 3:1 para texto grande
- No transmitir información solo con color (agregar iconos/texto)
- `prefers-reduced-motion`: respetar preferencia del usuario, reducir/eliminar animaciones
- `prefers-color-scheme`: soporte dark/light mode
- Zoom hasta 200% sin pérdida de funcionalidad ni overflow horizontal

### Formularios
- Cada input tiene un `<label>` asociado (htmlFor/id)
- Errores de validación vinculados con `aria-describedby`
- `aria-invalid="true"` en campos con error
- `aria-required="true"` en campos obligatorios
- Mensajes de error descriptivos (no solo "campo inválido")
- Agrupar campos relacionados con `<fieldset>` y `<legend>`

### Imágenes
- `alt` descriptivo en imágenes informativas
- `alt=""` en imágenes decorativas
- `role="img"` y `aria-label` en SVGs informativos

### Componentes (react-aria + shadcn/ui)
- Usar react-aria para componentes interactivos complejos
- shadcn/ui ya incluye accesibilidad base, verificar y complementar
- Testear con axe-core en cada componente

## Internacionalización (i18n)

### Reglas Generales
- NUNCA hardcodear texto visible al usuario en componentes
- TODO texto visible usa `t('key')` de i18next
- Claves de traducción en formato `namespace.section.key`
- Idiomas iniciales: ES (español) y EN (inglés)

### Estructura de Traducciones
```
frontend/public/locales/
├── es/translation.json
├── en/translation.json
├── pt/translation.json
└── fr/translation.json
```

### Formato de Claves
```json
{
  "common": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar",
    "edit": "Editar",
    "loading": "Cargando...",
    "error": "Ocurrió un error",
    "noResults": "Sin resultados"
  },
  "collections": {
    "title": "Colecciones",
    "create": "Crear Colección",
    "editLabel": "Editar {{name}}",
    "itemCount": "{{count}} item",
    "itemCount_plural": "{{count}} items",
    "deleteConfirm": "¿Eliminar la colección \"{{name}}\"?"
  }
}
```

### Reglas de Traducción
- Usar interpolación para valores dinámicos: `{{variable}}`
- Usar plurales de i18next: `key` y `key_plural`
- Incluir contexto en las claves para traductores
- Los ARIA labels también se traducen
- Formatos de fecha/número via i18next o Intl API (no formatear manualmente)
- Dirección de texto: preparar para RTL (usar logical properties en CSS: `margin-inline-start` en vez de `margin-left`)
