## ADDED Requirements

### Requirement: Modal de creación de factura
La TablaFacturas SHALL mostrar un botón "+ Nueva factura" que abre un modal con formulario para crear una factura. El modal SHALL contener campos para: usuario_id, periodo (YYYY-MM), monto, número de factura (opcional) y fecha de emisión (opcional).

#### Scenario: Abrir modal de nueva factura
- **WHEN** el usuario hace click en "+ Nueva factura"
- **THEN** se abre un modal con el formulario de creación

#### Scenario: Crear factura con datos válidos
- **WHEN** el usuario completa usuario_id, periodo, monto y hace click en "Crear factura"
- **THEN** se llama a `createFactura` con los datos y el modal se cierra al成功

#### Scenario: Botón deshabilitado con datos inválidos
- **WHEN** el modal está abierto y usuario_id, periodo están vacíos o monto ≤ 0
- **THEN** el botón "Crear factura" está deshabilitado
