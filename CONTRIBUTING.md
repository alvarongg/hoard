# 🤝 Contributing to H.O.A.R.D.

¡Gracias por tu interés en contribuir a H.O.A.R.D.! 

---

## 🌍 Tipos de Contribuciones

### 1. **Traducciones (i18n)**

Ayudá a hacer H.O.A.R.D. accesible en más idiomas.

**Idiomas prioritarios:**
- Español (es) ✅
- Inglés (en) ✅
- Portugués (pt)
- Francés (fr)
- Alemán (de)
- Japonés (ja)
- Italiano (it)
- Coreano (ko)
- Chino (zh)

**Cómo contribuir:**
1. Fork el repositorio
2. Ir a `frontend/src/locales/`
3. Copiar `en.json` como base
4. Traducir los strings
5. Enviar Pull Request

**Formato de archivos de traducción:**
```json
{
  "common": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar"
  },
  "collections": {
    "title": "Colecciones",
    "create": "Crear Colección"
  }
}
```

### 2. **Código (Backend/Frontend)**

**Áreas donde necesitamos ayuda:**
- Implementación de endpoints
- Componentes React
- Tests (unitarios, integración, E2E)
- Accesibilidad (ARIA, keyboard navigation)
- Performance optimization
- Bugfixes

**Proceso:**
1. Fork el repositorio
2. Crear branch: `git checkout -b feature/tu-feature`
3. Hacer commits descriptivos
4. Asegurar que tests pasen: `npm test` / `pytest`
5. Push y crear Pull Request

### 3. **Documentación**

Siempre necesitamos mejor documentación:
- Guías de uso
- Tutoriales
- Screenshots
- Videos
- FAQs

### 4. **Diseño**

¿Sos diseñador? Necesitamos:
- Logo del dragón (estilo Smaug)
- Iconografía temática
- Mockups de UI
- Ilustraciones para empty states
- Assets gráficos

### 5. **Testing**

- Reportar bugs
- Testar en diferentes navegadores/dispositivos
- Tests de accesibilidad con screen readers
- Tests de usabilidad

---

## 🐛 Reportar Bugs

**Antes de reportar:**
1. Buscar si ya existe el issue
2. Verificar que estás usando la última versión

**Información a incluir:**
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs real
- Screenshots/videos si aplica
- Versión de H.O.A.R.D.
- Navegador y sistema operativo
- Logs relevantes

**Template de issue:**
```markdown
## Descripción
[Descripción clara del bug]

## Pasos para Reproducir
1. Ir a '...'
2. Click en '...'
3. Ver error

## Comportamiento Esperado
[Qué debería pasar]

## Comportamiento Actual
[Qué pasa realmente]

## Screenshots
[Si aplica]

## Entorno
- H.O.A.R.D. versión: 
- Navegador: 
- OS: 
```

---

## ✨ Proponer Features

**Antes de proponer:**
1. Revisar roadmap y issues existentes
2. Considerar si se alinea con la visión del proyecto

**Template de feature request:**
```markdown
## Problema a Resolver
[¿Qué problema resuelve esto?]

## Solución Propuesta
[Cómo funcionaría]

## Alternativas Consideradas
[Otras formas de resolverlo]

## Casos de Uso
[Ejemplos de uso real]
```

---

## 📋 Estándares de Código

### **Backend (Python/FastAPI)**

**Style Guide:**
- PEP 8
- Type hints obligatorios
- Docstrings en funciones públicas
- Máximo 100 caracteres por línea

**Ejemplo:**
```python
from typing import List
from pydantic import BaseModel

def get_collections(
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[CollectionResponse]:
    """
    Retrieve collections for a user.
    
    Args:
        user_id: User identifier
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of collections
    """
    # Implementation
    pass
```

**Testing:**
```python
def test_get_collections():
    """Test retrieving user collections."""
    response = client.get("/api/collections")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

### **Frontend (React/TypeScript)**

**Style Guide:**
- ESLint + Prettier
- Componentes funcionales con hooks
- TypeScript estricto
- Accesibilidad WCAG 2.1 AA

**Ejemplo:**
```typescript
interface CollectionCardProps {
  collection: Collection;
  onEdit: (id: string) => void;
}

export function CollectionCard({ 
  collection, 
  onEdit 
}: CollectionCardProps) {
  return (
    <article 
      className="collection-card"
      aria-labelledby={`collection-${collection.id}`}
    >
      <h2 id={`collection-${collection.id}`}>
        {collection.name}
      </h2>
      <button 
        onClick={() => onEdit(collection.id)}
        aria-label={`Edit ${collection.name}`}
      >
        Edit
      </button>
    </article>
  );
}
```

**Testing:**
```typescript
describe('CollectionCard', () => {
  it('renders collection name', () => {
    render(<CollectionCard collection={mockCollection} onEdit={jest.fn()} />);
    expect(screen.getByText('My Collection')).toBeInTheDocument();
  });

  it('calls onEdit when button clicked', () => {
    const onEdit = jest.fn();
    render(<CollectionCard collection={mockCollection} onEdit={onEdit} />);
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith(mockCollection.id);
  });
});
```

### **Accesibilidad**

**Checklist obligatorio:**
- [ ] HTML semántico
- [ ] ARIA labels donde sea necesario
- [ ] Navegación por teclado funcional
- [ ] Focus indicators visibles
- [ ] Contraste de colores WCAG AA
- [ ] Texto alternativo en imágenes
- [ ] Tests con axe-core pasan

---

## 🔄 Proceso de Pull Request

1. **Fork y clone**
```bash
git clone https://github.com/tu-usuario/hoard.git
cd hoard
```

2. **Crear branch**
```bash
git checkout -b feature/nombre-descriptivo
```

3. **Hacer cambios**
- Commits atómicos y descriptivos
- Seguir convenciones de commits (ver abajo)

4. **Tests**
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
npm run test:a11y
```

5. **Push**
```bash
git push origin feature/nombre-descriptivo
```

6. **Crear PR**
- Título descriptivo
- Descripción clara de cambios
- Referenciar issues relacionados
- Screenshots si aplica

---

## 📝 Convención de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

**Formato:**
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: Nueva funcionalidad
- `fix`: Bugfix
- `docs`: Cambios en documentación
- `style`: Formato, no afecta código
- `refactor`: Refactoring
- `test`: Agregar/mejorar tests
- `chore`: Mantenimiento

**Ejemplos:**
```
feat(collections): add multi-category support

Implements multi-category collections allowing items from different
categories under a single theme.

Closes #123
```

```
fix(wishlist): correct price calculation for foreign currencies

Previously converting USD to ARS incorrectly.
Now uses correct exchange rate API.
```

```
docs(readme): add deployment instructions
```

---

## 🌟 Código de Conducta

**Esperamos que todos:**
- Sean respetuosos y constructivos
- Acepten críticas constructivas
- Se enfoquen en lo mejor para la comunidad
- Muestren empatía hacia otros

**No toleramos:**
- Lenguaje ofensivo o discriminatorio
- Acoso de cualquier tipo
- Trolling o comentarios despectivos
- Ataques personales o políticos

---

## 🎖️ Reconocimientos

Todos los contributors serán listados en:
- README.md (Contributors section)
- About page en la app
- Release notes

**Contributors especiales reciben:**
- Badge en la app
- Mención en redes sociales
- Créditos permanentes

---

## 📞 Contacto

¿Dudas sobre cómo contribuir?

- GitHub Issues: Para bugs y features
- GitHub Discussions: Para preguntas generales
- Discord: [Coming soon]

---

**¡Gracias por ayudar a hacer H.O.A.R.D. mejor!** 🐉✨
