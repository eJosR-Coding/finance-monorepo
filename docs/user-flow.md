# Anexo — User flow

Recorrido del administrador de la bodega por la aplicacion.

## Flujo principal

```mermaid
flowchart TD
    login[Login] --> dashboard[Dashboard]
    dashboard --> clientes[Clientes]
    clientes --> detalleCliente[Detalle del cliente]
    detalleCliente --> nuevoCredito[Nuevo credito]
    nuevoCredito --> simulacion[Simulacion del cronograma]
    simulacion --> confirmacion[Confirmacion]
    confirmacion --> detalleCredito[Detalle del credito]
    detalleCredito --> registrarPago[Registrar pago]
    registrarPago --> saldo[Saldo actualizado]
    saldo --> detalleCredito
```

## Rama de morosidad

```mermaid
flowchart TD
    detalleCliente[Detalle del cliente] --> mora{¿Tiene mora?}
    mora -- Si --> bloqueo[Bloqueo de nuevo credito]
    bloqueo --> morosos[Pantalla Morosos]
    morosos --> cobrar[Registrar pago de la cuota vencida]
    cobrar --> regularizado{¿Regularizo toda la deuda?}
    regularizado -- Si --> habilitado[Cliente habilitado]
    regularizado -- No --> bloqueo
    habilitado --> nuevoCredito[Nuevo credito]
    mora -- No --> nuevoCredito
```

## Mapa de navegacion

```mermaid
flowchart LR
    login["/login"] --> dashboard["/dashboard"]

    dashboard --> clientes["/clientes"]
    dashboard --> creditos["/creditos"]
    dashboard --> morosos["/morosos"]

    clientes --> nuevoCliente["/clientes/nuevo"]
    clientes --> detalleCliente["/clientes/:id"]
    nuevoCliente --> detalleCliente

    detalleCliente --> nuevoCredito["/creditos/nuevo"]
    creditos --> nuevoCredito
    creditos --> detalleCredito["/creditos/:id"]
    nuevoCredito --> detalleCredito

    detalleCredito --> pago["/creditos/:id/pagos/nuevo"]
    morosos --> pago
    pago --> detalleCredito

    dashboard --> pagos["/pagos"]
    dashboard --> config["/configuracion"]
```

## Pantallas

| Pantalla | Ruta | Que resuelve |
| --- | --- | --- |
| Login | `/login` | Acceso del administrador. |
| Dashboard | `/dashboard` | Creditos activos, por cobrar, cobros de hoy, bloqueados, proximos vencimientos. |
| Clientes | `/clientes` | Buscar, filtrar por estado y ordenar por deuda. |
| Nuevo cliente | `/clientes/nuevo` | Registrar a la persona antes de fiarle. |
| Detalle del cliente | `/clientes/:id` | Saldo, creditos, pagos e historial. |
| Nuevo credito | `/creditos/nuevo` | Simular y otorgar. |
| Creditos | `/creditos` | Todos los creditos, filtrables por estado. |
| Detalle del credito | `/creditos/:id` | Condiciones, cronograma completo e historial de pagos. |
| Registrar pago | `/creditos/:id/pagos/nuevo` | Cobrar y ver como se reparte el dinero. |
| Pagos | `/pagos` | Todos los cobros registrados. |
| Morosos | `/morosos` | Cuotas vencidas y clientes bloqueados. |
| Configuracion | `/configuracion` | Parametros vigentes del producto (solo lectura). |
