# Anexo C — Cronogramas de prueba
> Documento generado automaticamente por `apps/api/scripts/generate_docs.py`.
> No lo edites a mano: su contenido se lee del sistema real.

Casos de prueba del motor financiero. Los mismos numeros estan verificados por `pytest` en `apps/api/tests/test_finance.py`.

Convenciones: metodo frances, base 360 dias, tasas con 7 decimales en porcentaje e importes con 2 decimales.

## Caso 1 — S/ 200.00, TEA 60 %, 14 dias, 2 cuotas cada 7 dias

### Datos iniciales

| Variable | Valor |
| --- | --- |
| Capital (P) | S/ 200.00 |
| Tipo de tasa | TEA |
| Tasa anual | 60.00 % |
| Fecha de inicio | 12/09/2026 |
| Plazo | 14 dias |
| Numero de cuotas (n) | 2 |
| Frecuencia de pago | cada 7 dias |
| Periodo de gracia | Sin gracia |
| Base anual | 360 dias |

### Conversion de la tasa

```
i_d = (1 + TEA)^(d / 360) - 1
i_7 = (1 + 0.60)^(7 / 360) - 1
i_7 = 0.009180847
i_7 = 0.9180847 %
```

### Cuota (metodo frances)

```
C = P * [ i (1+i)^n ] / [ (1+i)^n - 1 ]
C = 200.00 * [ 0.009180847 (1+0.009180847)^2 ] / [ (1+0.009180847)^2 - 1 ]
C = 101.38
```

### Cronograma de amortizacion

| # | Fecha | Saldo inicial | Interes | Amortizacion | Cuota | Saldo final |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 19/09/2026 | S/ 200.00 | S/ 1.84 | S/ 99.54 | S/ 101.38 | S/ 100.46 |
| 2 | 26/09/2026 | S/ 100.46 | S/ 0.92 | S/ 100.46 | S/ 101.38 | S/ 0.00 |

### Resultados

| Variable | Valor |
| --- | --- |
| Tasa efectiva por periodo | 0.9180847 % |
| Cuota constante | S/ 101.38 |
| Interes total | S/ 2.76 |
| Total a pagar | S/ 202.76 |
| TCEA | 60.00 % |
| **Saldo final** | **S/ 0.00** |

---

## Caso 2 — S/ 120.00, TEA 40 %, 14 dias, 2 cuotas cada 7 dias

### Datos iniciales

| Variable | Valor |
| --- | --- |
| Capital (P) | S/ 120.00 |
| Tipo de tasa | TEA |
| Tasa anual | 40.00 % |
| Fecha de inicio | 12/09/2026 |
| Plazo | 14 dias |
| Numero de cuotas (n) | 2 |
| Frecuencia de pago | cada 7 dias |
| Periodo de gracia | Sin gracia |
| Base anual | 360 dias |

### Conversion de la tasa

```
i_d = (1 + TEA)^(d / 360) - 1
i_7 = (1 + 0.40)^(7 / 360) - 1
i_7 = 0.006563965
i_7 = 0.6563965 %
```

### Cuota (metodo frances)

```
C = P * [ i (1+i)^n ] / [ (1+i)^n - 1 ]
C = 120.00 * [ 0.006563965 (1+0.006563965)^2 ] / [ (1+0.006563965)^2 - 1 ]
C = 60.59
```

### Cronograma de amortizacion

| # | Fecha | Saldo inicial | Interes | Amortizacion | Cuota | Saldo final |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 19/09/2026 | S/ 120.00 | S/ 0.79 | S/ 59.80 | S/ 60.59 | S/ 60.20 |
| 2 | 26/09/2026 | S/ 60.20 | S/ 0.40 | S/ 60.20 | S/ 60.60 | S/ 0.00 |

### Resultados

| Variable | Valor |
| --- | --- |
| Tasa efectiva por periodo | 0.6563965 % |
| Cuota constante | S/ 60.59 |
| Interes total | S/ 1.19 |
| Total a pagar | S/ 121.19 |
| TCEA | 40.00 % |
| **Saldo final** | **S/ 0.00** |

> Nota: la ultima cuota es S/ 60.60 y no S/ 60.59 (diferencia de S/ 0.01). Es el ajuste de redondeo que absorbe la ultima cuota para que el saldo cierre exactamente en S/ 0.00.

---

