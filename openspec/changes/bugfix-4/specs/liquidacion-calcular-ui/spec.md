## ADDED Requirements

### Requirement: Botón calcular liquidaciones en VistaPeriodo
La VistaPeriodo SHALL mostrar un botón "Calcular liquidaciones" cuando no existan datos de liquidaciones para el período seleccionado (general.length === 0). Al hacer click, SHALL llamar a `calcularLiquidaciones` con cohorte_id y período.

#### Scenario: Mostrar botón cuando no hay liquidaciones
- **WHEN** VistaPeriodo se renderiza con datos vacíos (general.length === 0)
- **THEN** se muestra el botón "Calcular liquidaciones"

#### Scenario: Ocultar botón cuando hay liquidaciones
- **WHEN** VistaPeriodo se renderiza con datos existentes (general.length > 0)
- **THEN** el botón "Calcular liquidaciones" NO se muestra

#### Scenario: Calcular liquidaciones exitoso
- **WHEN** el usuario hace click en "Calcular liquidaciones"
- **THEN** se llama a `calcularLiquidaciones({ cohorte_id, periodo })` y al成功 se refresca la vista
