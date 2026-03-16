---
inclusion: always
---

# Testing Standards - OBLIGATORIO

Los tests son OBLIGATORIOS en H.O.A.R.D. No se implementa ninguna funcionalidad sin sus tests correspondientes. Sin excepciones.

## Regla de Oro

TODA pieza de código que se cree o modifique DEBE tener tests asociados. Si se crea un service, se crean sus tests. Si se crea un componente, se crean sus tests. Si se modifica un endpoint, se actualizan sus tests.

## Coverage Mínimo por Fase

- Fase 1 (MVP): >70% coverage
- Fase 2 (Core): >80% coverage
- Fase 3+ (Advanced): >85% coverage

## Backend (Python/pytest)

### Estructura de Tests
```
backend/tests/
├── conftest.py              # Fixtures compartidos (db session, client, factories)
├── unit/                    # Tests unitarios
│   ├── test_services/       # Tests de lógica de negocio
│   ├── test_models/         # Tests de modelos
│   └── test_utils/          # Tests de utilidades
├── integration/             # Tests de integración
│   ├── test_routes/         # Tests de endpoints completos
│   └── test_database/       # Tests de queries complejas
└── factories/               # Factories para generar datos de test
```

### Reglas Backend
- Usar pytest (no unittest)
- Fixtures para setup/teardown (conftest.py)
- Factories para crear datos de test (factory_boy o funciones custom)
- Base de datos de test aislada (SQLite in-memory o PostgreSQL de test)
- Cada test es independiente y puede correr en cualquier orden
- Naming: `test_{what}_{scenario}_{expected_result}`
- Mocks solo para dependencias externas (APIs, filesystem, email)
- NO mockear la base de datos en tests de integración

```python
# Ejemplo de test de service
class TestCollectionService:
    async def test_create_collection_with_valid_data_returns_collection(
        self, collection_service: CollectionService, db_session: AsyncSession
    ):
        data = CollectionCreate(name="Mi Colección N64", collection_type="single_category", ...)
        result = await collection_service.create(data)
        assert result.name == "Mi Colección N64"
        assert result.id is not None

    async def test_create_collection_with_duplicate_name_raises_error(
        self, collection_service: CollectionService, existing_collection: Collection
    ):
        data = CollectionCreate(name=existing_collection.name, ...)
        with pytest.raises(DuplicateError):
            await collection_service.create(data)
```

```python
# Ejemplo de test de endpoint
class TestCollectionRoutes:
    async def test_get_collections_returns_200_with_list(self, client: AsyncClient):
        response = await client.get("/api/collections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_collection_returns_201(self, client: AsyncClient):
        payload = {"name": "Test Collection", "collection_type": "mixed"}
        response = await client.post("/api/collections", json=payload)
        assert response.status_code == 201
        assert response.json()["name"] == "Test Collection"
```

### Qué Testear en Backend
- Services: toda la lógica de negocio, casos edge, validaciones
- Routes: status codes, response format, error handling, auth
- Models: relaciones, constraints, métodos custom
- Utils: funciones de utilidad, procesamiento de datos

## Frontend (Vitest + Testing Library + Playwright)

### Estructura de Tests
```
frontend/
├── src/
│   ├── components/
│   │   └── collections/
│   │       ├── CollectionCard.tsx
│   │       └── CollectionCard.test.tsx    # Test junto al componente
│   ├── hooks/
│   │   ├── useCollections.ts
│   │   └── useCollections.test.ts
│   └── services/
│       ├── api.ts
│       └── api.test.ts
└── tests/
    ├── e2e/                               # Playwright E2E
    │   ├── collections.spec.ts
    │   └── wishlist.spec.ts
    └── accessibility/                     # Tests de accesibilidad
        └── components.a11y.test.ts
```

### Reglas Frontend
- Tests unitarios con Vitest + Testing Library
- Tests E2E con Playwright
- Tests de accesibilidad con axe-core en CADA componente
- Testear comportamiento del usuario, NO implementación interna
- Usar `screen.getByRole`, `getByLabelText`, `getByText` (queries accesibles)
- NO usar `getByTestId` salvo último recurso
- Mock de API con MSW (Mock Service Worker)

```typescript
// Ejemplo de test de componente con accesibilidad
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { CollectionCard } from './CollectionCard';

expect.extend(toHaveNoViolations);

describe('CollectionCard', () => {
  const mockCollection = { id: '1', name: 'Nintendo 64', totalItems: 42 };

  it('renders collection name as heading', () => {
    render(<CollectionCard collection={mockCollection} onEdit={vi.fn()} />);
    expect(screen.getByRole('heading', { name: /nintendo 64/i })).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', async () => {
    const onEdit = vi.fn();
    render(<CollectionCard collection={mockCollection} onEdit={onEdit} />);
    await userEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith('1');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<CollectionCard collection={mockCollection} onEdit={vi.fn()} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Qué Testear en Frontend
- Componentes: renderizado, interacciones, estados (loading/error/empty), accesibilidad
- Hooks: lógica de estado, llamadas a API, edge cases
- Pages: integración de componentes, routing
- E2E: flujos completos del usuario (crear colección, agregar item, etc.)

## Tests de Accesibilidad

OBLIGATORIO en cada componente React:
- Test con axe-core para violaciones automáticas
- Verificar navegación por teclado (Tab, Enter, Escape)
- Verificar ARIA labels y roles
- Verificar contraste (via axe-core)
- Verificar focus management en modales/dialogs

## Convenciones de Naming

### Backend
- Archivos: `test_{module}.py`
- Clases: `Test{Feature}`
- Funciones: `test_{what}_{scenario}_{expected}`

### Frontend
- Archivos: `{Component}.test.tsx` o `{hook}.test.ts` (colocados junto al código)
- E2E: `{feature}.spec.ts` en `tests/e2e/`
- Describe: nombre del componente/hook
- It: descripción del comportamiento esperado en inglés

## Antes de Considerar Completa una Tarea

1. ¿Se crearon tests unitarios para la lógica nueva?
2. ¿Se crearon tests de integración si hay interacción entre capas?
3. ¿Los componentes React tienen test de accesibilidad con axe-core?
4. ¿Los tests pasan localmente?
5. ¿El coverage no bajó del mínimo requerido?
