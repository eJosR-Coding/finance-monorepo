# Anexo D — Diagrama de flujo del otorgamiento de credito

Flujo principal que sigue el sistema desde que el administrador elige un cliente
hasta que el credito queda registrado con su cronograma.

```mermaid
flowchart TD
    inicio([Inicio]) --> seleccionar[Seleccionar cliente]
    seleccionar --> habilitado{¿Cliente habilitado?}

    habilitado -- No --> bloqueo[/"Mensaje: el cliente mantiene una deuda vencida<br/>y no puede recibir un nuevo credito"/]
    bloqueo --> regularizar[Registrar pago de la deuda vencida]
    regularizar --> revision{¿Quedan cuotas vencidas?}
    revision -- Si --> bloqueo
    revision -- No --> habilita[Cliente vuelve a estado habilitado]
    habilita --> ingresar

    habilitado -- Si --> ingresar[Ingresar condiciones del credito<br/>monto, fecha, plazo, cuotas, frecuencia, tasa, gracia]
    ingresar --> validar{"¿Monto ≤ S/ 200.00<br/>y plazo ≤ 14 dias<br/>y cronograma dentro del plazo?"}

    validar -- No --> errorLimites[/"Mensaje con el limite incumplido"/]
    errorLimites --> ingresar

    validar -- Si --> convertir["Convertir tasa anual a tasa del periodo<br/>TEA: i_d = (1 + TEA)^(d/360) - 1<br/>TNA: i_d = TNA × d/360"]
    convertir --> gracia{¿Periodo de gracia?}

    gracia -- Parcial --> graciaParcial[Cuota extra de solo interes<br/>el capital no se toca]
    gracia -- Total --> graciaTotal[El interes se capitaliza al principal]
    gracia -- Sin gracia --> frances

    graciaParcial --> frances
    graciaTotal --> frances

    frances["Calcular cuota por metodo frances<br/>C = P · i(1+i)^n / ((1+i)^n − 1)"]
    frances --> cronograma[Generar cronograma<br/>I_t = saldo × i · A_t = C − I_t · S_t = saldo − A_t]
    cronograma --> ajuste[Ajustar la ultima cuota<br/>para que el saldo cierre en S/ 0.00]
    ajuste --> mostrar[Mostrar simulacion:<br/>tasa periodica, cuota, interes total, total a pagar]

    mostrar --> confirmar{¿Confirmar credito?}
    confirmar -- No --> ingresar
    confirmar -- Si --> transaccion[(Transaccion)]
    transaccion --> guardar[Guardar CREDIT + INSTALLMENT]
    guardar --> exito{¿Se guardo todo?}
    exito -- No --> rollback[Rollback: no se guarda nada]
    rollback --> mostrar
    exito -- Si --> commit[Commit y toast<br/>'Credito registrado correctamente']
    commit --> fin([Fin])
```

## Notas

- La validacion de limites corre **en el backend**. El frontend repite las
  mismas comprobaciones solo para dar feedback inmediato, pero la decision final
  siempre es del servidor.
- El estado de mora se recalcula **antes** de evaluar si el cliente esta
  habilitado, no despues: un cliente cuya cuota vencio hoy queda bloqueado en el
  mismo momento en que se intenta otorgarle credito.
- El bloque `Transaccion` es literal: credito y cuotas se guardan juntos o no se
  guarda nada (`apps/api/app/services/credits.py`).

## Flujo de registro de pago

```mermaid
flowchart TD
    inicio([Inicio]) --> elegir[Elegir credito y cuota]
    elegir --> monto[Ingresar monto recibido]
    monto --> calcularMora{"¿Hoy > fecha de vencimiento<br/>y la cuota no esta pagada?"}

    calcularMora -- Si --> mora["Calcular interes moratorio<br/>i = (1 + TEM)^(dias/30) − 1"]
    calcularMora -- No --> sinMora[Interes moratorio = S/ 0.00]

    mora --> aplicar
    sinMora --> aplicar

    aplicar[Aplicar el pago en orden]
    aplicar --> paso1[1 . Interes moratorio]
    paso1 --> paso2[2 . Interes compensatorio]
    paso2 --> paso3[3 . Capital]
    paso3 --> exceso{¿Sobra dinero?}

    exceso -- Si, y quedan cuotas --> siguiente[Aplicar a la siguiente cuota]
    siguiente --> paso1
    exceso -- "Si, y no queda deuda" --> rechazo[/"Mensaje: el monto excede la deuda pendiente"/]
    exceso -- No --> actualizar[Actualizar cuota, saldo del credito y estado del cliente]

    actualizar --> saldado{¿Credito saldado?}
    saldado -- Si --> pagado[Credito = pagado]
    saldado -- No --> vigente[Credito = vigente u overdue segun vencimientos]

    pagado --> liberar
    vigente --> liberar{"¿Al cliente le quedan cuotas vencidas?"}
    liberar -- No --> habilitar[Cliente = habilitado]
    liberar -- Si --> mantener[Cliente sigue bloqueado]

    habilitar --> fin([Fin])
    mantener --> fin
    rechazo --> monto
```
