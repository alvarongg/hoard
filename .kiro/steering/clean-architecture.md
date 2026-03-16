---
inclusion: always
---

# Clean Architecture & Clean Code Standards

Todas las implementaciones en H.O.A.R.D. DEBEN seguir los principios de Clean Architecture y Clean Code.

## Principios Fundamentales

### SOLID
- Single Responsibility: cada clase/módulo/función tiene UNA sola razón para cambiar
- Open/Closed: abierto para extensión, cerrado para modificación
- Liskov Substitution: las subclases deben ser sustituibles por sus clases base
- Interface Segregation: interfaces pequeñas y específicas, no interfaces gordas
- Dependency Inversion: depender de abstracciones, no de implementaciones concretas

### Clean Code
- Nombres descriptivos y pronunciables (no abreviaturas crípticas)
- Funciones pequeñas que hacen UNA sola cosa (máximo ~20 líneas)
- Sin efectos secundarios ocultos
- Sin números mágicos ni strings hardcodeados
- DRY: no repetir lógica, extraer a funciones/utilidades
- KISS: la solución más simple que funcione
- YAGNI: no implementar lo que no se necesita ahora

## Backend (Python/FastAPI) - Capas

### Capa de Presentación (`api/routes/`)
- Solo recibe requests y devuelve responses
- Validación de entrada via Pydantic schemas
- NO contiene lógica de negocio
- Delega TODO al service correspondiente
- Manejo de errores HTTP (HTTPException)

```python
# CORRECTO
@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(
    data: CollectionCreate,
    service: CollectionService = Depends(get_collection_service),
) -> CollectionResponse:
    return await service.create(data)

# INCORRECTO - lógica de negocio en el route
@router.post("/collections")
async def create_collection(data: CollectionCreate, db: Session = Depends(get_db)):
    collection = Collection(**data.dict())
    db.add(collection)
    db.commit()
    return collection
```

### Capa de Negocio (`api/services/`)
- Contiene TODA la lógica de negocio
- Orquesta operaciones entre repositorios/modelos
- Validaciones de negocio (no de formato, eso es Pydantic)
- Independiente del framework (no importar FastAPI aquí)
- Recibe dependencias por inyección (constructor o parámetros)

### Capa de Datos (`api/models/`)
- Modelos SQLAlchemy que representan las tablas
- Relaciones entre entidades
- Sin lógica de negocio en los modelos
- Métodos de conveniencia solo para queries simples

### Schemas (`api/schemas/`)
- Pydantic v2 models para validación de entrada/salida
- Separar: Base, Create, Update, InDB, Response
- Validators para reglas de formato
- Field descriptions para documentación automática

### Dependencias (`api/dependencies.py`)
- Inyección de dependencias de FastAPI
- Factory functions para services
- Gestión de sesiones de DB

## Frontend (React/TypeScript) - Capas

### Componentes (`components/`)
- Componentes presentacionales: solo UI, reciben props, sin lógica de negocio
- Componentes contenedores: conectan hooks con componentes presentacionales
- Un componente = un archivo. Si crece mucho, dividir
- Props tipadas con interfaces TypeScript
- Siempre exportar named exports (no default)

### Pages (`pages/`)
- Composición de componentes
- Conexión con hooks de datos
- Layout de la página
- No contienen lógica de negocio directa

### Hooks (`hooks/`)
- Custom hooks para lógica reutilizable
- Encapsulan llamadas a API via React Query
- Encapsulan lógica de estado compleja
- Prefijo `use` obligatorio

### Services (`services/`)
- Clientes HTTP (Axios/fetch)
- Solo comunicación con API
- Sin lógica de negocio
- Tipado completo de request/response

### Types (`types/`)
- Interfaces y types compartidos
- Un archivo por dominio (collection.ts, item.ts, etc.)
- No usar `any` NUNCA. Usar `unknown` si es necesario y hacer type narrowing

## Reglas de Código

### Python
- Type hints obligatorios en TODAS las funciones
- Docstrings en funciones públicas (Google style)
- Máximo 100 caracteres por línea
- Imports ordenados: stdlib → third-party → local
- Async/await para operaciones de I/O
- Context managers para recursos (db sessions, files)

### TypeScript
- Strict mode habilitado
- No usar `any` bajo ninguna circunstancia
- Interfaces para objetos, types para uniones/intersecciones
- Funciones puras siempre que sea posible
- Destructuring para props de componentes
- Manejo explícito de estados: loading, error, success, empty

### Ambos
- Máximo 1 nivel de anidamiento en condicionales (early return)
- Sin console.log/print en código de producción (usar logger)
- Manejo de errores explícito y específico (no catch genéricos)
- Constantes en UPPER_SNAKE_CASE en archivos dedicados
- Archivos de máximo ~200 líneas. Si crece, refactorizar
