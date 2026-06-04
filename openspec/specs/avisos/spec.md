## ADDED Requirements

### Requirement: Publicar aviso institucional
Un COORDINADOR o ADMIN autenticado con permiso `avisos:publicar` SHALL poder crear un aviso institucional en su tenant. El aviso incluye: `titulo` (str, requerido), `cuerpo` (str, requerido), `scope` (enum: TODOS | ROL | USUARIO, requerido), `scope_valor` (str opcional — nombre de rol o UUID de usuario cuando scope ≠ TODOS), `vig_desde` (datetime, requerido), `vig_hasta` (datetime, requerido, > vig_desde), `activo` (bool, default True). El campo `publicado_por` se toma del JWT (nunca de la request).

#### Scenario: Creación exitosa de aviso
- **WHEN** un usuario con permiso `avisos:publicar` envía POST /api/avisos con datos válidos
- **THEN** el sistema crea el aviso con `tenant_id` del JWT, `publicado_por` del JWT, devuelve 201 con el aviso creado incluyendo su `id`

#### Scenario: Sin permiso devuelve 403
- **WHEN** un usuario sin permiso `avisos:publicar` envía POST /api/avisos
- **THEN** el sistema devuelve 403 sin crear el aviso

#### Scenario: vig_hasta anterior a vig_desde es rechazado
- **WHEN** se envía `vig_hasta` anterior o igual a `vig_desde`
- **THEN** el sistema devuelve 422

### Requirement: Listar avisos vigentes del tenant
Cualquier usuario autenticado SHALL poder listar los avisos vigentes de su tenant. Un aviso es vigente si: `activo=True` AND `vig_desde <= now() <= vig_hasta` AND `tenant_id` coincide con el del JWT. Si `scope=ROL`, el aviso se incluye solo si el rol del usuario coincide con `scope_valor`. Si `scope=USUARIO`, el aviso se incluye solo si el `usuario_id` del JWT coincide con `scope_valor`.

#### Scenario: Listado devuelve solo avisos vigentes del tenant
- **WHEN** un usuario autenticado hace GET /api/avisos
- **THEN** recibe solo los avisos con `activo=True`, dentro de la ventana de vigencia, del tenant del JWT

#### Scenario: Aviso desactivado no aparece en el listado
- **WHEN** existe un aviso con `activo=False` en el tenant
- **THEN** ese aviso NO aparece en GET /api/avisos

#### Scenario: Aviso fuera de ventana no aparece
- **WHEN** existe un aviso cuya `vig_hasta` es anterior a la fecha/hora actual
- **THEN** ese aviso NO aparece en GET /api/avisos

### Requirement: Confirmar lectura de aviso (acknowledgment)
Un usuario autenticado con permiso `avisos:confirmar` SHALL poder confirmar la lectura de un aviso mediante POST /api/avisos/{id}/ack. La operación es idempotente: si el usuario ya confirmó, devuelve 200 sin crear un registro duplicado. El campo `leido_en` se registra con la marca de tiempo del primer ack.

#### Scenario: Primer ack crea registro
- **WHEN** un usuario con permiso `avisos:confirmar` hace POST /api/avisos/{id}/ack por primera vez
- **THEN** se crea un registro en `aviso_acks` con `tenant_id`, `aviso_id`, `usuario_id` del JWT y `leido_en` = now(); devuelve 200

#### Scenario: Ack repetido es idempotente
- **WHEN** el mismo usuario hace POST /api/avisos/{id}/ack por segunda vez (o más)
- **THEN** el sistema devuelve 200 sin crear duplicados en `aviso_acks`

#### Scenario: Aviso no existente devuelve 404
- **WHEN** se intenta confirmar lectura de un aviso con id inexistente en el tenant
- **THEN** el sistema devuelve 404

#### Scenario: Sin permiso devuelve 403
- **WHEN** un usuario sin permiso `avisos:confirmar` intenta confirmar lectura
- **THEN** el sistema devuelve 403

### Requirement: Ver confirmaciones de un aviso
Un usuario con permiso `avisos:publicar` SHALL poder listar quiénes confirmaron la lectura de un aviso de su tenant mediante GET /api/avisos/{id}/acks. Devuelve una lista de objetos con `usuario_id` y `leido_en`.

#### Scenario: Listado de acks devuelve confirmaciones del aviso
- **WHEN** un usuario con permiso `avisos:publicar` hace GET /api/avisos/{id}/acks de un aviso de su tenant
- **THEN** recibe la lista de `{usuario_id, leido_en}` para todos los usuarios que confirmaron lectura

#### Scenario: Sin permiso devuelve 403
- **WHEN** un usuario sin permiso `avisos:publicar` intenta ver los acks
- **THEN** el sistema devuelve 403

### Requirement: Desactivar aviso (soft delete)
Un usuario con permiso `avisos:publicar` SHALL poder desactivar un aviso de su tenant (PATCH /api/avisos/{id} con `activo=False`). El registro NUNCA se elimina físicamente.

#### Scenario: Desactivar aviso lo oculta del listado
- **WHEN** se desactiva un aviso (`activo=False`)
- **THEN** ese aviso no aparece en GET /api/avisos y su registro permanece en DB con `activo=False`
