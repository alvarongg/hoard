---
inclusion: always
---

# Coding Standards & Conventions

## Convención de Commits (Conventional Commits)

Formato: `<type>(<scope>): <subject>`

Types: feat, fix, docs, style, refactor, test, chore
Scopes: backend, frontend, db, docker, docs, i18n, a11y

Ejemplos:
- `feat(backend): add collection CRUD endpoints`
- `fix(frontend): correct wishlist price calculation`
- `test(backend): add integration tests for catalog service`
- `docs(readme): update deployment instructions`

## Python (Backend)

### Naming
- Archivos: `snake_case.py`
- Clases: `PascalCase`
- Funciones/métodos: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
- Variables privadas: `_prefixed`

### Imports (orden)
```python
# 1. Standard library
from datetime import datetime
from typing import Optional
from uuid import UUID

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local
from api.models.collection import Collection
from api.schemas.collection import CollectionCreate
from api.services.collection_service import CollectionService
```

### Estructura de un Route
```python
router = APIRouter(prefix="/collections", tags=["collections"])

@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CollectionService = Depends(get_collection_service),
) -> list[CollectionResponse]:
    """List all collections with pagination."""
    return await service.list(skip=skip, limit=limit)
```

### Estructura de un Service
```python
class CollectionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: CollectionCreate) -> Collection:
        """Create a new collection."""
        collection = Collection(**data.model_dump())
        self._db.add(collection)
        await self._db.commit()
        await self._db.refresh(collection)
        return collection
```

### Manejo de Errores Backend
- Errores de negocio: excepciones custom (DuplicateError, NotFoundError, ValidationError)
- Los services lanzan excepciones de dominio
- Los routes capturan y convierten a HTTPException
- Usar exception handlers globales para errores comunes

## TypeScript (Frontend)

### Naming
- Archivos de componentes: `PascalCase.tsx`
- Archivos de hooks: `camelCase.ts` (ej: `useCollections.ts`)
- Archivos de utils/services: `camelCase.ts`
- Archivos de types: `camelCase.ts`
- Interfaces: `PascalCase` (sin prefijo I)
- Types: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`
- Funciones/variables: `camelCase`

### Estructura de un Componente
```typescript
import { useTranslation } from 'react-i18next';

interface CollectionCardProps {
  collection: Collection;
  onEdit: (id: string) => void;
}

export function CollectionCard({ collection, onEdit }: CollectionCardProps) {
  const { t } = useTranslation();

  return (
    <article aria-labelledby={`collection-${collection.id}`}>
      <h2 id={`collection-${collection.id}`}>{collection.name}</h2>
      <p>{t('collections.itemCount', { count: collection.totalItems })}</p>
      <button
        onClick={() => onEdit(collection.id)}
        aria-label={t('collections.editLabel', { name: collection.name })}
      >
        {t('common.edit')}
      </button>
    </article>
  );
}
```

### Estructura de un Hook
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { collectionsApi } from '../services/api';
import type { Collection, CollectionCreate } from '../types/collection';

export function useCollections() {
  const queryClient = useQueryClient();

  const query = useQuery<Collection[]>({
    queryKey: ['collections'],
    queryFn: collectionsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: CollectionCreate) => collectionsApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  });

  return { ...query, create: createMutation };
}
```

## Estructura de Archivos

### Al crear un nuevo recurso backend (ej: "suppliers"):
1. `api/models/supplier.py` - Modelo SQLAlchemy
2. `api/schemas/supplier.py` - Schemas Pydantic (Base, Create, Update, Response)
3. `api/services/supplier_service.py` - Lógica de negocio
4. `api/routes/suppliers.py` - Endpoints REST
5. `tests/unit/test_services/test_supplier_service.py` - Tests unitarios
6. `tests/integration/test_routes/test_suppliers.py` - Tests de integración

### Al crear un nuevo feature frontend (ej: "suppliers"):
1. `src/types/supplier.ts` - Types/interfaces
2. `src/services/suppliersApi.ts` - Cliente API
3. `src/hooks/useSuppliers.ts` - Custom hook
4. `src/components/suppliers/SupplierCard.tsx` - Componente
5. `src/components/suppliers/SupplierCard.test.tsx` - Test del componente
6. `src/pages/Suppliers.tsx` - Página
7. Actualizar traducciones en `public/locales/{lang}/translation.json`

## Git Workflow

- Branch naming: `feat/description`, `fix/description`, `test/description`
- Commits atómicos: un commit = un cambio lógico
- No commitear archivos generados, node_modules, __pycache__, .env
