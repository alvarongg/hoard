# 🐉 H.O.A.R.D. - Brand Identity Guide

## Nombre

**H.O.A.R.D.**
- **H**obby
- **O**rganization,
- **A**rchive &
- **R**egistry
- **D**atabase

## Concepto

Como un dragón (al estilo Smaug de El Hobbit) que custodia celosamente su montaña de tesoros, H.O.A.R.D. representa la pasión del coleccionista por organizar, valorizar y proteger sus posesiones más preciadas.

---

## 🎨 Logo

### Concepto Principal

**Dragón sobre su tesoro**
- Un dragón majestuoso enroscado sobre una montaña de items de colección
- Los items brillan con resplandor dorado bajo las escamas del dragón
- Transmite: Protección, Valor, Organización, Pasión

### Descripción Visual Detallada

**El Dragón:**
- Estilo inspirado en Smaug (El Hobbit)
- Silueta elegante y amenazante a la vez
- Postura protectora, enroscado alrededor del tesoro
- Ojo vigilante mirando hacia el espectador
- Alas parcialmente extendidas formando un marco

**La Montaña de Tesoros:**
- Items variados visibles: cartuchos de juegos, vinilos, libros, figuras, cartas TCG
- Disposición caótica pero con armonía visual
- Resplandor dorado emanando desde el centro
- Algunos items destacados con más detalle

**Composición:**
- El dragón ocupa 60% del espacio visual
- La montaña de items ocupa 40%
- Balance visual con peso hacia abajo (estabilidad)
- Espaciado adecuado para que funcione en tamaños pequeños

### Paleta de Colores

#### Versión Principal (Color)
```
Dragón:
- Escamas: #B8860B (Dark Goldenrod) con highlights #FFD700 (Gold)
- Sombras: #8B4513 (Saddle Brown)
- Ojos: #FF4500 (Orange Red) con brillo #FFD700

Montaña/Items:
- Base: #2C2C2C (Gris oscuro)
- Highlights dorados: #FFD700, #FFA500, #FF8C00
- Items: Colores variados pero desaturados

Fondo:
- Degradado: #1A1A1A → #000000
- O transparente para versión con fondo
```

#### Versión Monocromática
```
Negro (#000000) y Blanco (#FFFFFF)
Para: Favicons, iconos de app, versiones pequeñas
```

#### Versión Invertida (Fondo Claro)
```
Dragón en negro con highlights grises
Tesoros en colores sutiles
```

---

## 📐 Variantes del Logo

### 1. Logo Completo (Horizontal)
```
[Dragón + Montaña]  H.O.A.R.D.
                     Hobby Organization, Archive & Registry Database
```
**Uso:** Header principal, presentaciones, documentación

### 2. Logo Compacto (Vertical)
```
    [Dragón + Montaña]
         H.O.A.R.D.
```
**Uso:** Sidebar, mobile, espacios reducidos

### 3. Icono/Favicon
```
[Solo silueta del dragón]
```
**Uso:** Favicon, app icon, notificaciones

### 4. Logo Simplificado
```
[Dragón minimalista]  H.O.A.R.D.
```
**Uso:** Cargando, splash screen, marcas de agua

---

## 🎯 Taglines

### Principal
**"Build your H.O.A.R.D."**
- Directo, activo, motivador
- Juega con el acrónimo

### Alternativos

**"Guard your treasures like a dragon"**
- Conecta con la temática del dragón
- Enfatiza protección y valor

**"Every treasure, organized"**
- Simple, funcional
- Para audiencia menos "geek"

**"Your collection, perfected"**
- Aspiracional
- Enfoque en calidad

**"Where collectors become dragons"**
- Transformacional
- Empoderamiento del usuario

---

## 🎨 Paleta de Colores Extendida (UI)

### Colores Primarios
```css
--dragon-gold:     #FFD700  /* Dorado principal */
--dragon-dark:     #8B4513  /* Marrón oscuro */
--treasure-glow:   #FFA500  /* Naranja dorado */
--dragon-eye:      #FF4500  /* Rojo naranja */
```

### Colores de Fondo
```css
--bg-dark:         #1A1A1A  /* Fondo principal oscuro */
--bg-darker:       #0D0D0D  /* Fondo más oscuro */
--bg-card:         #2C2C2C  /* Cards/Containers */
--bg-hover:        #3A3A3A  /* Hover states */
```

### Colores de Texto
```css
--text-primary:    #F5F5F5  /* Texto principal */
--text-secondary:  #B8B8B8  /* Texto secundario */
--text-muted:      #808080  /* Texto suave */
--text-gold:       #FFD700  /* Acentos dorados */
```

### Colores Semánticos
```css
--success:         #10B981  /* Verde - Item adquirido */
--warning:         #F59E0B  /* Amarillo - Wishlist */
--error:           #EF4444  /* Rojo - Error/Falta */
--info:            #3B82F6  /* Azul - Información */
```

### Categorías de Colección (UI)
```css
--category-games:     #9333EA  /* Púrpura */
--category-music:     #EC4899  /* Rosa */
--category-books:     #F97316  /* Naranja */
--category-tcg:       #06B6D4  /* Cyan */
--category-toys:      #84CC16  /* Lima */
--category-anime:     #EAB308  /* Amarillo */
```

---

## ✍️ Tipografía

### Logo/Marca
```
Familia: "Cinzel" (Google Fonts)
Estilo: Bold, serif decorativo
Uso: Solo para "H.O.A.R.D."
Alternativa: "Trajan Pro" o "Goudy Trajan"
```

### Subtítulos (Tagline, descriptores)
```
Familia: "Lato"
Peso: Regular (400) / Bold (700)
Tamaño: 60% del tamaño del logo
```

### UI - Títulos
```
Familia: "Inter"
Pesos: 400, 500, 600, 700
Uso: Headers, títulos de sección
```

### UI - Cuerpo
```
Familia: "Inter"
Peso: 400
Uso: Texto general, descripciones
```

### UI - Código/Datos
```
Familia: "JetBrains Mono"
Uso: IDs, códigos, datos técnicos
```

---

## 🖼️ Aplicaciones del Branding

### 1. Interfaz Web

**Header:**
```
[Logo completo]                    [Navegación]  [Usuario]
```

**Splash Screen (PWA):**
```
        [Dragón grande animado]
             H.O.A.R.D.
       Build your H.O.A.R.D.
            [Loading...]
```

**Empty States:**
```
    [Dragón triste/vacío]
    No tienes items en esta colección
       [Botón: Agregar Item]
```

### 2. Mobile App

**Icon (iOS/Android):**
- Fondo degradado negro a marrón oscuro
- Dragón dorado centralizado
- Sin texto (solo icono)

**Splash:**
- Dragón completo
- "H.O.A.R.D." grande
- Tagline pequeño abajo

### 3. Documentación

**Portada README:**
```markdown
# 🐉 H.O.A.R.D.
## Hobby Organization, Archive & Registry Database
> Build your H.O.A.R.D.
```

**Badges:**
```
[HOARD v1.0.0] [FastAPI] [React] [PostgreSQL]
```
Con colores: Dorado para versión, grises para tech stack

### 4. Marketing

**Página Landing:**
- Hero section: Dragón grande + "Build your H.O.A.R.D."
- Features con iconos temáticos (escamas, tesoros, etc.)
- CTA: "Start Your H.O.A.R.D." (botón dorado)

**Social Media:**
- Avatar: Icono del dragón
- Banner: Logo completo + tagline
- Posts: Marco dorado con tema de tesoro

---

## 📱 Iconografía Temática

### Iconos Personalizados (estilo dragón/tesoro)

```
Colecciones:    Montaña de items apilados
Items:          Gema brillante
Wishlist:       Tesoro con signo de interrogación
Catálogo:       Pergamino enrollado
Proveedores:    Mercader con bolsa
Accesorios:     Cofre protector
Estadísticas:   Gráfico con monedas
Búsqueda:       Lupa sobre tesoro
Configuración:  Engranajes dorados
Usuario:        Corona/escudo
```

---

## 🎭 Tono de Voz

### Personalidad de Marca

**Palabras clave:**
- Épico
- Protector
- Meticuloso
- Apasionado
- Poderoso

**Tono:**
- Amigable pero con autoridad
- Geek-friendly pero accesible
- Profesional pero no aburrido
- Motivador, no instructivo

### Ejemplos de Copy

**Mensajes de Éxito:**
✅ "¡Tesoro agregado a tu H.O.A.R.D.!"
✅ "Tu colección crece, dragón"
✅ "Item protegido en tu guarida"

**Mensajes de Error:**
❌ "Tu dragón no puede guardar esto aquí"
❌ "Tesoro no encontrado en las profundidades"

**Call to Actions:**
- "Agregar a mi H.O.A.R.D."
- "Proteger este tesoro"
- "Explorar el catálogo"
- "Construir mi guarida"

**Empty States:**
- "Tu guarida está vacía... ¡por ahora!"
- "Ningún tesoro encontrado. ¿Comenzamos a buscar?"
- "Tu dragón espera sus primeros tesoros"

---

## 🎬 Animaciones y Efectos

### Animación del Logo
- Dragón "despierta" al cargar
- Ojos brillan
- Tesoros brillan secuencialmente
- Humo/niebla sutil en el fondo

### Transiciones
- Items "caen" al agregarse (como tesoros a la pila)
- Efecto de brillo dorado al completar acciones
- Hover: Resplandor sutil dorado

### Sonidos (opcional)
- Agregar item: Moneda cayendo
- Eliminar item: Whoosh suave
- Completar colección: Rugido de dragón (sutil)

---

## 📦 Assets a Crear

### Prioridad Alta
- [ ] Logo completo (SVG)
- [ ] Icono/Favicon (PNG, ICO, SVG)
- [ ] Logo monocromático (SVG)
- [ ] App icons (iOS/Android - múltiples tamaños)

### Prioridad Media
- [ ] Splash screen (1920x1080)
- [ ] Empty state illustrations
- [ ] Error state illustrations
- [ ] Loading animations

### Prioridad Baja
- [ ] Social media templates
- [ ] Email templates
- [ ] Presentation template
- [ ] Stickers/Merchandising

---

## 🔗 Recursos y Referencias

### Inspiración Visual
- Smaug (The Hobbit - Peter Jackson)
- Dragones de Game of Thrones
- Art de Magic: The Gathering (dragones)
- Estética de Skyrim (tesoros)

### Herramientas de Diseño
- **Logo:** Adobe Illustrator / Inkscape
- **Mockups:** Figma
- **Animaciones:** Lottie / After Effects
- **Iconos:** Heroicons + custom

---

## ✅ Checklist de Implementación

### Básico (MVP)
- [ ] Logo SVG simple (monocromático)
- [ ] Favicon
- [ ] Paleta de colores en CSS variables
- [ ] Tipografía configurada
- [ ] Nombre en todos los archivos

### Completo
- [ ] Logo a color completo
- [ ] Todas las variantes
- [ ] Iconografía custom
- [ ] Animaciones básicas
- [ ] Guía de estilo documentada

### Premium
- [ ] Logo animado
- [ ] Efectos de partículas
- [ ] Sonidos UI
- [ ] Easter eggs temáticos
- [ ] Merchandising

---

**Tagline oficial:** "Build your H.O.A.R.D."
**Versión completa:** H.O.A.R.D. - Hobby Organization, Archive & Registry Database
**Concepto:** Tu colección es tu tesoro. Protégela como un dragón.
