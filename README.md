# Prestameami.pe

Aplicacion web administrativa para que el dueno de una bodega gestione pequenos
creditos comerciales ("fiados"): registro de clientes, simulacion y otorgamiento
de creditos con **metodo frances**, registro de pagos y control de morosidad.

Proyecto academico del curso de **Finanzas e Ingenieria Economica**.

---

## Reglas del producto

| Regla | Valor |
| --- | --- |
| Monto maximo por credito | S/ 200.00 |
| Plazo maximo | 14 dias |
| Moneda | PEN (S/) |
| Metodo de amortizacion | Frances (cuota constante) |
| Ano financiero | 360 dias |
| Precision de tasas | 7 decimales en porcentaje (9 en la fraccion) |
| Precision de importes | 2 decimales |
| Tasa moratoria | 2 % mensual, prorrateada por dias de atraso |

Un cliente con una obligacion vencida queda **bloqueado** y no puede recibir un
nuevo credito hasta regularizar su deuda. El bloqueo se revierte solo cuando
paga lo que debe.

---

## Requisitos

| Herramienta | Version | Para que |
| --- | --- | --- |
| [Python](https://www.python.org/) | 3.12 o superior | Backend |
| [uv](https://docs.astral.sh/uv/) | reciente | Entorno y dependencias de Python |
| [Node.js](https://nodejs.org/) | 20 o superior | Frontend |

No hace falta nada mas: ni Docker, ni base de datos externa, ni cuentas en la
nube. Todo corre en local.

---

## Puesta en marcha

### 1. Backend

```bash
cd apps/api
uv sync                                # instala dependencias y crea el entorno
uv run python scripts/seed.py          # crea la base y carga datos de ejemplo
uv run fastapi dev app/main.py         # levanta la API en el puerto 8000
```

### 2. Frontend

En otra terminal:

```bash
cd apps/web
npm install
npm run dev                            # levanta la app en el puerto 5173
```

### 3. Abrir

| Servicio | URL |
| --- | --- |
| Aplicacion | http://localhost:5173 |
| API | http://localhost:8000 |
| Documentacion interactiva (Swagger) | http://localhost:8000/docs |

### Credenciales

```
correo:      admin@prestameami.pe
contrasenia: admin123
```

La contrasenia se guarda con hash bcrypt, nunca en texto plano.

---

## Comandos utiles

### Backend (`apps/api`)

| Comando | Que hace |
| --- | --- |
| `uv run fastapi dev app/main.py` | Levanta la API con recarga automatica. |
| `uv run python scripts/seed.py` | **Reinicia** la base y carga los datos de demo. |
| `uv run python scripts/reset_db.py` | Deja la base vacia, sin datos. |
| `uv run pytest` | Ejecuta toda la bateria de tests. |
| `uv run pytest -v` | Igual, mostrando el nombre de cada test. |
| `uv run pytest -k caso-1` | Solo el caso de prueba 1 del anexo. |
| `uv run python scripts/generate_docs.py` | Regenera los anexos C, E y F desde el codigo. |
| `uv run python scripts/generate_excel.py` | Regenera el libro de Excel de verificacion. |
| `uv run ruff check .` | Linter. |

La base de datos vive en `apps/api/data/prestameami.db` y no se versiona: se
regenera con el seed. La primera vez que arranca la API, si el archivo no
existe, se crean las tablas vacias.

### Frontend (`apps/web`)

| Comando | Que hace |
| --- | --- |
| `npm run dev` | Servidor de desarrollo en el puerto 5173. |
| `npm run build` | Compilacion de produccion (`tsc -b && vite build`). |
| `npm run preview` | Sirve la compilacion de produccion. |
| `npm run lint` | Chequeo de tipos de TypeScript. |

El servidor de desarrollo hace proxy de `/api` hacia `http://localhost:8000`,
asi que el navegador habla con un solo origen y no hay problemas de CORS.

---

## Estructura del monorepo

```
finanzas_monorepo/
├── apps/
│   ├── api/                       Backend: FastAPI + SQLAlchemy 2.x + SQLite
│   │   ├── app/
│   │   │   ├── core/              Config, enums, tipos Decimal, seguridad, errores
│   │   │   ├── models/            Tablas ORM (identicas al ERD)
│   │   │   ├── schemas/           Contratos de entrada y salida (Pydantic)
│   │   │   ├── repositories/      Acceso a datos
│   │   │   ├── services/          Logica de negocio + motor financiero
│   │   │   ├── routers/           Rutas HTTP
│   │   │   ├── database.py        Motor, sesiones y Base declarativa
│   │   │   └── main.py            Aplicacion FastAPI
│   │   ├── scripts/               seed, reset y generador de anexos
│   │   ├── tests/                 pytest
│   │   └── data/                  prestameami.db (no versionado)
│   │
│   └── web/                       Frontend: React + TypeScript + Vite + Tailwind
│       └── src/
│           ├── components/        Piezas reutilizables de UI
│           ├── pages/             Una pantalla por archivo
│           ├── features/          Sesion y toasts
│           ├── services/          Cliente HTTP y endpoints
│           ├── hooks/             Consultas de TanStack Query
│           ├── lib/               Formateo, i18n y traduccion de errores
│           ├── types/             Espejo tipado de la API
│           └── styles/            Tokens del sistema Modernist
│
├── docs/                          Anexos academicos
└── design_handoff_prestameami/    Referencia de diseno (10 pantallas)
```

### Separacion de capas en el backend

```
router  ->  service  ->  repository  ->  model
  |            |
  |            └── services/finance.py  (motor financiero puro, sin base de datos)
  |
  └── schemas  (validacion y forma del JSON)
```

**La logica financiera vive unicamente en `app/services/finance.py`.** El
frontend nunca recalcula una cuota: pide el cronograma a la API y lo formatea.

---

## Documentacion

| Documento | Contenido |
| --- | --- |
| [docs/erd.md](docs/erd.md) | Anexo E — diagrama entidad-relacion. |
| [docs/c4-context.md](docs/c4-context.md) | C4 nivel 1: contexto del sistema. |
| [docs/flowchart.md](docs/flowchart.md) | Anexo D — diagramas de flujo. |
| [docs/user-flow.md](docs/user-flow.md) | Recorrido del usuario y mapa de rutas. |
| [docs/test-cases.md](docs/test-cases.md) | Anexo C — cronogramas de los casos de prueba. |
| [docs/validation.md](docs/validation.md) | Anexo F — evidencias de validacion. |
| [docs/evidence/prestameami-cronogramas.xlsx](docs/evidence/prestameami-cronogramas.xlsx) | Cronogramas en Excel con formulas vivas, para contrastar el calculo. |

Los anexos C, E y F **se generan desde el codigo**:

```bash
cd apps/api && uv run python scripts/generate_docs.py
```

El ERD se lee de `Base.metadata` (las tablas reales) y los cronogramas salen del
motor financiero. No hay tablas escritas a mano que puedan quedar desfasadas.

---

## Endpoints

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Inicia sesion y devuelve el token. |
| `GET` | `/api/auth/me` | Administrador de la sesion actual. |
| `GET` | `/api/clients` | Lista clientes (`search`, `status`, `sort`). |
| `POST` | `/api/clients` | Registra un cliente. |
| `GET` | `/api/clients/{id}` | Ficha completa del cliente. |
| `PATCH` | `/api/clients/{id}` | Actualiza datos o estado crediticio. |
| `POST` | `/api/credits/simulate` | Calcula el cronograma **sin guardar nada**. |
| `POST` | `/api/credits` | Otorga el credito y persiste sus cuotas. |
| `GET` | `/api/credits` | Lista creditos (`client_id`, `status`). |
| `GET` | `/api/credits/{id}` | Condiciones y cronograma del credito. |
| `POST` | `/api/credits/{id}/payments` | Registra un pago. |
| `POST` | `/api/credits/{id}/payments/preview` | Muestra el reparto sin registrar. |
| `GET` | `/api/credits/{id}/payments` | Historial de pagos del credito. |
| `GET` | `/api/payments` | Todos los cobros registrados. |
| `GET` | `/api/dashboard` | Resumen del negocio. |
| `GET` | `/api/overdue` | Cuotas vencidas y clientes bloqueados. |
| `GET` | `/api/config` | Limites y tasas vigentes del producto. |

Todas las rutas de `/api` piden el token salvo `/api/config` y `/api/auth/login`.

### Formato de error

```json
{
  "code": "AMOUNT_ABOVE_MAX",
  "message": "El monto maximo permitido es S/ 200.00.",
  "details": { "max_amount": "200.00" }
}
```

El `code` es estable y el frontend lo traduce con i18n; el `message` sirve de
respaldo si la clave no existe en el catalogo.

---

## Notas de implementacion

**Los importes son `Decimal`, nunca `float`.** SQLite no tiene tipo decimal
nativo, asi que se guardan como TEXT y vuelven como `Decimal` de Python. Por eso
el saldo final de un credito cancelado es exactamente `S/ 0.00`.

**La ultima cuota absorbe el residuo del redondeo.** Es lo que hace que el
cronograma cierre en cero. En el caso 2 del anexo la ultima cuota es S/ 60.60 y
no S/ 60.59: ese centavo es el ajuste.

**La mora se recalcula al leer.** Cada consulta al dashboard, a los listados o
al detalle vuelve a evaluar que cuotas vencieron hoy y actualiza el estado de la
cuota, del credito y del cliente. En una app local esto es mas simple y mas
honesto que un proceso programado.

**Los pagos se reparten en un orden fijo:** interes moratorio, interes
compensatorio y capital. La API devuelve cuanto fue a cada componente.

**Diferencias deliberadas respecto a los wireframes.** El ERD academico es la
fuente de verdad, asi que:

- El formulario de nuevo cliente no pide fecha de nacimiento, correo ni notas:
  no hay columnas para eso en `CLIENT`.
- La pantalla de Configuracion es de solo lectura: no existe tabla de
  configuracion y crearla dejaria la documentacion peleada con la base.
- La tasa moratoria se muestra pero no se edita por credito: es un parametro del
  sistema (`GET /api/config`).
- La TCEA se calcula de verdad, `(1 + i)^(360/f) − 1`, en vez del valor de
  ejemplo del comp.

---

## Tests

```bash
cd apps/api && uv run pytest
```

Cubren la conversion de tasas (TEA y TNA, base 360), el metodo frances, el caso
de tasa cero, los limites de monto y plazo, los periodos de gracia, el interes
moratorio, el bloqueo y desbloqueo de clientes morosos, y el flujo completo de
la demo a traves de HTTP. Incluye un barrido de 100 combinaciones de monto,
numero de cuotas y tasa que verifica que el saldo final siempre cierre en cero.

Ademas hay una bateria de pruebas de estres (`tests/test_stress.py`) con los
limites exactos, los pagos parciales encadenados, la mora dia a dia y la
idempotencia de cada endpoint, y un contraste contra Excel
(`tests/test_excel.py`) que le pide a LibreOffice recalcular el libro y compara
sus resultados con los del motor, celda por celda.

---

## Stack

**Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2.x, SQLite, uv, pytest, ruff.

**Frontend:** React, TypeScript (modo estricto), Vite, Tailwind CSS v4,
React Router, TanStack Query, react-i18next.

Sin Supabase, Firebase, PostgreSQL remoto, Redis, Docker, microservicios, colas,
nube, autenticacion externa ni IA.
