# Prestameami.pe

Aplicación web administrativa para que el dueño de una bodega gestione pequeños
créditos comerciales ("fiados"): registro de clientes, simulación y otorgamiento
de créditos con **método francés**, registro de pagos y control de morosidad.

Proyecto académico del curso de **Finanzas e Ingeniería Económica**.

## Reglas de negocio

| Regla | Valor |
| --- | --- |
| Monto máximo por crédito | S/ 200.00 |
| Plazo máximo | 14 días |
| Moneda | PEN (S/) |
| Método de amortización | Francés (cuota constante) |
| Año financiero | 360 días |
| Precisión de tasas | 7 decimales |
| Precisión de importes | 2 decimales |

Un cliente con una obligación vencida queda **bloqueado** y no puede recibir un
nuevo crédito hasta regularizar su deuda.

## Estructura del monorepo

```
prestameami/
├── apps/
│   ├── api/      FastAPI + SQLAlchemy 2.x + SQLite (toda la lógica financiera)
│   └── web/      React + TypeScript + Vite + Tailwind
├── docs/         Anexos académicos (ERD, C4, flujos, casos de prueba)
└── design_handoff_prestameami/   Referencia de diseño (Modernist, 10 pantallas)
```

## Stack

- **Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2.x, SQLite, `uv`
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query
- **Todo corre en local.** Sin servicios externos, sin Docker, sin nube.

## Cómo ejecutar

Ver instrucciones detalladas más abajo conforme avanza la implementación.

```bash
# Backend
cd apps/api && uv sync && uv run fastapi dev app/main.py

# Frontend
cd apps/web && npm install && npm run dev
```
