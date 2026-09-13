# Anexo — C4 Nivel 1: diagrama de contexto del sistema

Este documento es **solo el nivel 1 (System Context)** del modelo C4. A
proposito no aparecen el frontend, FastAPI ni SQLite: esos son componentes
internos y pertenecen a los niveles 2 y 3.

```mermaid
flowchart TB
    admin["<b>Administrador de la bodega</b><br/><i>[Persona]</i><br/><br/>Dueno o encargado.<br/>Decide a quien le fia y cobra."]

    sistema["<b>Prestameami.pe</b><br/><i>[Sistema de software]</i><br/><br/>Digitaliza los fiados de la bodega:<br/>clientes, creditos con metodo frances,<br/>pagos y control de morosidad."]

    cliente["<b>Cliente de la bodega</b><br/><i>[Persona externa al sistema]</i><br/><br/>Vecino que recibe el fiado.<br/>No usa la aplicacion."]

    admin -->|"Registra clientes, simula y otorga<br/>creditos, registra pagos y revisa morosidad"| sistema
    sistema -->|"Le muestra cronogramas, saldos,<br/>vencimientos y clientes bloqueados"| admin

    admin -->|"Entrega el credito y cobra en persona"| cliente
    cliente -->|"Recibe el credito y realiza sus pagos"| admin

    classDef persona fill:#2d2b2b,stroke:#201e1d,color:#ffffff
    classDef externa fill:#7d7979,stroke:#605d5d,color:#ffffff
    classDef sistemaCls fill:#ec3013,stroke:#ae1800,color:#ffffff

    class admin persona
    class cliente externa
    class sistema sistemaCls
```

## Actores

| Elemento | Tipo | Descripcion |
| --- | --- | --- |
| Administrador de la bodega | Persona | Unico usuario del sistema. Registra clientes, otorga creditos, cobra y revisa la morosidad. |
| Prestameami.pe | Sistema de software | El sistema que se esta construyendo. Guarda clientes, creditos, cuotas y pagos, y calcula el cronograma por metodo frances. |
| Cliente de la bodega | Persona externa | Recibe el fiado y paga. **No tiene acceso al sistema**: toda la interaccion es cara a cara con el administrador. |

## Interacciones

| Origen | Destino | Interaccion |
| --- | --- | --- |
| Administrador | Prestameami.pe | Registrar clientes, simular creditos, otorgar creditos, registrar pagos, consultar morosidad. |
| Prestameami.pe | Administrador | Cronogramas de amortizacion, saldos pendientes, proximos vencimientos, alertas de clientes bloqueados. |
| Administrador | Cliente de la bodega | Entrega del dinero o la mercaderia y cobro presencial. |
| Cliente de la bodega | Administrador | Recepcion del credito y entrega de los pagos (efectivo, Yape, Plin o transferencia). |

## Alcance

**Dentro del sistema:** registro de clientes, simulacion y otorgamiento de
creditos, generacion del cronograma frances, registro de pagos con reparto
entre mora, interes y capital, y control de morosidad con bloqueo automatico.

**Fuera del sistema:** portal o app para el cliente de la bodega, notificaciones
por WhatsApp o correo, integraciones bancarias, contabilidad y scoring
crediticio. Tampoco hay sistemas externos: la aplicacion corre entera en local.
