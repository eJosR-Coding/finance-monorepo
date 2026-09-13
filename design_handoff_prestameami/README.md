# Handoff: Prestameami.pe — Admin Web App (8 screens)

## Overview
Prestameami.pe is an internal admin tool for a bodega (corner store) owner in Lima, Perú to manage microcréditos ("fiados"): register clients, simulate and grant credits (max S/ 200, max 14 days, French amortization method), register payments, and track overdue/blocked clients. This package covers 8 full screens of the same product, sharing one visual system.

## About the Design Files
The files in this bundle (`*.dc.html`) are **design references built in HTML** — interactive prototypes showing intended look, content, and navigation, not production code to copy directly. The task is to **recreate these designs in the target codebase's existing environment** (React, Vue, etc.) using its established component library and patterns — or, if no environment/stack exists yet, choose React (the designs assume component-based, state-driven UI) and implement there. Do not literally ship this HTML/inline-style markup to production; treat it as the spec for pixel/behavior fidelity.

Note: `*.dc.html` files use a small proprietary template runtime (`support.js`, `<x-dc>` wrapper, `{{ }}` bindings) — this is a design-tool authoring format, not a library to depend on. Read the files for their rendered structure/content/styles only.

## Fidelity
**High-fidelity (hifi).** Colors, typography, spacing, copy and component states are final/intentional. Recreate pixel-close using the codebase's own component library where one exists (buttons, inputs, tables, dialogs, tags) — don't hand-roll from scratch if equivalents already exist; otherwise implement to match exactly as designed here.

## Design system
All screens are built on **Modernist**: a flat, architectural system — Archivo typeface, a single red accent, zero border-radius everywhere, strong 2px dividers, no shadows except very subtle elevation on cards/dialogs. The full token sheet is included at `_ds/styles.css` in this bundle — port these CSS variables directly into the target codebase's theme (design tokens below are extracted from it for convenience).

## Global layout (present on every screen except Login)
- **Sidebar**: fixed left, 230px wide, dark background (`--color-neutral-900` #2d2b2b), full viewport height, sticky.
  - Top: logo lockup — 22×22px red square + "Prestameami.pe" wordmark (Archivo 800, 16.5px; ".pe" in `--color-accent-400`).
  - Nav: 6 links stacked with 2px gap — Dashboard, Clientes, Créditos, Pagos, Morosos, Configuración. Each: 17px Lucide icon + label, 13.5px/600 weight. Inactive: `--color-neutral-400` text. Active: white text, 20%-opacity accent-tinted background, 2px solid accent left border. Hover (inactive): 6%-opacity white background.
  - Bottom: user block — 32×32px square avatar (initials "CM", `--color-accent-700` bg, white text) + name "Carlos Mendoza" (700/12.5px white) + role "Administrador" (11px, neutral-500) + icon-only logout button (opens a confirm dialog, see Interactions).
- **Topbar**: 64px tall, sticky, bottom border 2px `--color-divider`, page background. Left: breadcrumb/page title (13–14px). Right: notification bell (icon button with a subtle frosted/glass treatment — `backdrop-filter: blur(6px)` + translucent surface fill; this is the ONE place any glass effect is used in the system, intentionally, per the client's request — nowhere else), 28×28px avatar chip + name.
- **Main content**: max-width 1180px (1100px on Registrar pago), padding 32px 40px 72px.

## Screens

### 1. Login (`Login.dc.html`)
Split screen, no sidebar. Left ~45%: centered login form (max-width 380px) — logo, H1 "Bienvenido de vuelta" (28px), subtitle, form (email, password, "Recordarme" checkbox, "¿Olvidaste tu contraseña?" link, primary "Ingresar" button full-width), footer note with shield icon "Acceso exclusivo para administradores de la bodega." Right ~55%: dark panel (`--color-neutral-900`) with a muted mini dashboard preview card (2 stat values + 2 mock table rows) and a quote line. Submitting the form navigates to Dashboard.

### 2. Dashboard (`Dashboard.dc.html`)
H1 "Dashboard" + subtitle + primary button "+ Nuevo crédito" (top right, → Nuevo crédito). 4 KPI cards in a row (Créditos activos: 18, Por cobrar: S/ 1,284.50, Cobros de hoy: S/ 185.00, Clientes bloqueados: 3 in accent-700), each with a small muted comparison line. Two-column body: left (2fr) has "Próximos cobros" table (Cliente/Cuota/Vence/Estado/Acción) and "Últimos créditos" table (Cliente/Capital/Plazo/Cuotas/Total/Estado); right (1fr) "Requiere atención" panel with 2 small cards (3 cuotas vencidas → link to Morosos; 5 cobros esta semana, informational).

### 3. Clientes (`Clientes.dc.html`)
H1 + subtitle + "+ Nuevo cliente" button. Filter row: search input (icon-prefixed, placeholder "Buscar por nombre o DNI"), Estado select (Todos/Habilitados/Bloqueados), sort select (Más recientes/Mayor deuda). Table: Cliente (avatar initials + name) / DNI / Teléfono / Crédito activo / Saldo pendiente / Estado (tag) / Último movimiento / "Ver cliente" link. 5 example rows (María Torres, Luis Herrera, Andrea Flores, Pedro Salazar, Marcela Díaz). Footer: result count + Anterior/Siguiente pagination buttons.

### 4. Detalle de cliente (`ClienteDetalle.dc.html`)
Breadcrumb "Clientes / María Torres". Header: 52px avatar, name + status tag, DNI/phone/address line, action buttons (+Nuevo crédito, Registrar pago, "···" more). 4 summary KPI cards (Saldo pendiente, Créditos activos, Total pagado, Último pago). Tabs (Créditos / Pagos / Actividad — client-side state, no reload) each rendering a table or empty note. Below: "Historial reciente" — vertical timeline with dot markers, date/title/amount per entry.

### 5. Nuevo crédito / Simulador (`NuevoCredito.dc.html`)
Two-column layout (1.3fr form / 1fr sticky summary). Form sections separated by `.hr` dividers and small-caps section labels: Cliente (autocomplete input + status tag), Condiciones del crédito (monto with S/200 max helper, fecha, plazo with 14-day max helper, número de cuotas, frecuencia), Tasa (tipo TEA with info tooltip, tasa %), Período de gracia (3-option segmented control, default "Sin gracia"), Mora (tasa moratoria input with tooltip). Buttons: Cancelar / Simular crédito. Right: sticky "Resumen del crédito" card — capital/plazo/cuotas/tasa efectiva por período grid, divider, cuota estimada (large), interés total, total a pagar, TCEA (with tooltip), divider, compact 2-row cronograma table (#, Fecha, Interés, Capital, Cuota), saldo final, full-width primary "Confirmar crédito" button (→ Crédito detalle).

### 6. Detalle de crédito (`CreditoDetalle.dc.html`)
Breadcrumb "Clientes / María Torres / Crédito CR-0021". Header: title + "Vigente" tag, created-date subtext, buttons (Registrar pago, Descargar cronograma, "···"). 5 KPI cards (Capital, Saldo pendiente, Cuota, Total a pagar, Próximo vencimiento). "Condiciones" as an 8-item label/value grid (tipo de tasa, TEA, tasa periódica, plazo, cuotas, frecuencia, gracia, tasa moratoria). "Cronograma de amortización" full table (#, Fecha, Saldo inicial, Interés, Amortización, Cuota, Saldo final, Estado) — 2 rows. "Historial de pagos" — bordered empty state (icon, "Aún no se han registrado pagos.", "Registrar primer pago" button) when no payments exist yet; should switch to a payments table (Fecha/Monto/Mora/Interés/Capital/Saldo) once payments exist.

### 7. Registrar pago (`RegistrarPago.dc.html`)
Breadcrumb, H1, subtitle. Context strip (Cliente/Crédito/Cuota/Vence, 4 inline fields on a tinted surface bar). Two columns: left form (Fecha, Monto recibido, Medio de pago as a 4-option segmented control — Efectivo/Yape/Plin/Transferencia, Observaciones textarea). Right: "Aplicación del pago" card breaking down Saldo exigible → Interés moratorio / Interés compensatorio / Capital → Total aplicado (large) → Saldo del crédito después del pago, plus a contextual status tag ("Pago exacto" shown; also design/support "Pago parcial", "Pago excedente", "Cuota vencida" as visual states — swatch shown below the card). Buttons: Cancelar / Registrar pago → opens a confirm dialog ("Confirmar registro de pago") → on confirm, shows a bottom-right toast "Pago registrado correctamente" and redirects to Crédito detalle after ~1.4s.

### 8. Morosos (`Morosos.dc.html`)
H1 + subtitle. 3 KPI cards (Clientes bloqueados: 3, Saldo vencido: S/ 164.80 in accent-700, Cuotas vencidas: 4). Two-column body: left (2.4fr) filter row (4-option segmented control Todos/Vencidos/Bloqueados/Seguimiento hoy + search input) and the main table (Cliente/Crédito/Vencimiento/Días de mora/Saldo vencido/Estado/Último pago/Acción, 3 example rows). Right (1fr): a small informational card "Regla de crédito" with an info icon — explicitly NOT styled as an alarming/red alert, just a quiet note: "Los clientes con una obligación vencida no pueden recibir un nuevo crédito hasta regularizar su deuda."

## Interactions & Behavior
- Sidebar navigation links are plain routes between the 8 screens (`href="./Screen.dc.html"` in the prototype → map to your router).
- Logout icon button (sidebar, every screen) opens a confirm dialog ("¿Cerrar sesión?", Cancelar / Cerrar sesión) before navigating to Login.
- ClienteDetalle tabs (Créditos/Pagos/Actividad) are local UI state, no navigation.
- NuevoCredito: "Confirmar crédito" navigates to CreditoDetalle (in a real app: submit → create credit → redirect).
- RegistrarPago: "Registrar pago" opens a confirm dialog, then shows a success toast and redirects to CreditoDetalle after a short delay.
- Tooltips: small "?" info glyphs next to TEA, TCEA and Tasa moratoria labels show explanatory text on hover/focus (native `title` attribute in the prototype — replace with a proper tooltip component).
- All monetary values are formatted "S/ #,##0.00"; dates are "dd/mm/aaaa".

## State Management (suggested)
- Auth: logged-in admin user (name, role) — session state.
- Clients list + selected client detail (credits, payments, activity feed).
- Active credit simulation form state (amount, term, installments, rate type/value, grace period, late-fee rate) → derived schedule (French amortization: fixed installment, interest = balance × periodic rate, amortization = installment − interest).
- Selected credit detail + its amortization schedule + payment history.
- Payment form state → computed allocation (mora interest → compensatory interest → principal, in that order) and resulting balance.
- Delinquency: computed list of clients/credits past due, with days-overdue and blocked flag (client is blocked once any installment is overdue, until fully regularized).
- UI-only state: active client tab, logout dialog open, payment confirm dialog open, toast visibility.

## Design Tokens (from Modernist, `_ds/styles.css`)
- **Colors**: bg `#f3f2f2`, surface `#eae9e9`, text `#201e1d`, accent `#ec3013` (ramp 100→900: `#fff2ef … #4d170e`), neutral ramp 100→900: `#f8f4f4 … #2d2b2b`, divider = text at 40% opacity.
- **Status colors (added for this app, harmonized in OKLCH — not in base Modernist, which is single-accent)**: success/paid bg `oklch(93% 0.05 145)` / text `oklch(35% 0.1 145)`; warning/pending bg `oklch(94% 0.07 80)` / text `oklch(38% 0.1 55)`; danger/overdue/blocked reuses the Modernist accent tag (`.tag-accent`).
- **Type**: `--font-heading` / `--font-body` = Archivo (400/600/800 weights). h1 42px / h2 32px / h3 25px base scale (screens use custom smaller sizes for app density: page titles 24–26px, KPI values 19–24px).
- **Spacing scale**: 4, 8, 12, 16, 24, 32px.
- **Radius**: 0px everywhere — no rounded corners anywhere in this product.
- **Shadows**: sm/md/lg soft ink-tinted shadows, used only on cards (`.elev-sm/md`) and dialogs (`.elev-lg`).
- **Components used**: `.btn` (`-primary/-secondary/-ghost/-icon/-block`), `.tag` (`-accent/-neutral/-outline` + the two custom status colors above), `.field`/`.input`/`.seg`/`.seg-opt`/`.radio`, `.card` (`-kicker/-title/-body/-meta`), `.table`, `.dialog-backdrop`/`.dialog`, `.hr`.

## Assets
- Icons: inline Lucide SVGs (stroke-based, 2px stroke, 14–17px), no icon font/library dependency — swap for your icon library's equivalent names (layout-dashboard, users, credit-card, wallet, alert-triangle, settings, log-out, search, bell, plus, more-horizontal, download, check-circle, info, shield-check).
- No photography/imagery used in this flow (numbers/text only, per the "no decorative illustration" brief).
- Avatars are plain initials on a flat square tile — no photo uploads used in these screens.

## Files in this bundle
- `Login.dc.html`, `Dashboard.dc.html`, `Clientes.dc.html`, `ClienteDetalle.dc.html`, `NuevoCredito.dc.html`, `CreditoDetalle.dc.html`, `RegistrarPago.dc.html`, `Morosos.dc.html` — the 8 screens (open directly in a browser to view/interact).
- `_ds/styles.css` — the full Modernist token sheet + component CSS referenced by all screens.
