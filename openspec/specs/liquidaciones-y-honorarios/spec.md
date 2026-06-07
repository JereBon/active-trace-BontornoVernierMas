# Spec: Liquidaciones y Honorarios

> Synced from change `c-18-liquidaciones-y-honorarios` on 2026-06-07.

### Requirement: Grilla salarial Base con vigencia temporal
El sistema SHALL mantener una tabla de salario Base por rol con vigencia temporal abierta (`desde` obligatorio, `hasta` nullable), scoped por tenant. Al calcular una liquidación de un período, SHALL tomar el registro Base cuyo `rol` coincide y cuyo rango `desde <= período <= hasta` (o `hasta` NULL) está vigente.

#### Scenario: Base vigente correcta con múltiples vigencias
- **WHEN** existen dos registros Base para PROFESOR (uno con `hasta` cerrado en un mes anterior y otro vigente) y se calcula la liquidación del mes actual
- **THEN** el cálculo usa el `monto` del registro vigente para ese período, no el caducado

#### Scenario: ABM de Base requiere permiso
- **WHEN** un usuario sin `liquidaciones:operar` invoca el ABM de la grilla Base
- **THEN** el sistema responde 403 (fail-closed)

### Requirement: Grilla salarial Plus por (grupo × rol) con vigencia
El sistema SHALL mantener una tabla de salario Plus identificada por (`grupo` texto libre × `rol`) con `monto`, `descripcion` y vigencia (`desde`, `hasta` nullable), scoped por tenant. El `grupo` mapea a la `categoria_clave` de las materias.

#### Scenario: ABM de Plus persiste grupo texto libre
- **WHEN** FINANZAS crea un Plus con `grupo="PROG"`, `rol=PROFESOR`, `monto=1000`
- **THEN** queda disponible para el cálculo de liquidaciones de ese tenant

### Requirement: Mapeo materia a categoría de clave
La entidad `Materia` SHALL exponer un campo `categoria_clave: str | None`. Una materia con `categoria_clave = NULL` no genera Plus.

#### Scenario: Materia sin categoria_clave no genera Plus
- **WHEN** un docente tiene comisiones cuya materia tiene `categoria_clave = NULL`
- **THEN** la liquidación calcula solo el Base, no falla y `monto_plus` no incluye esas comisiones

### Requirement: Cálculo de liquidación por (cohorte × mes)
El sistema SHALL calcular la liquidación de cada docente de la cohorte en el período como `Total = Base(rol vigente) + Σ(Plus(clave, rol) × N_comisiones_de_esa_clave)`, con acumulación lineal sin tope, generando un registro `Liquidacion` por docente con `monto_base`, `monto_plus`, `total`, `comisiones`, `rol`.

#### Scenario: Acumulación lineal de plus de la misma clave
- **WHEN** un PROFESOR tiene 2 comisiones cuya materia es de clave PROG y Plus(PROG, PROFESOR)=1000
- **THEN** `monto_plus` incluye 2 × 1000 = 2000 por la clave PROG

#### Scenario: Claves distintas acumulan independientemente
- **WHEN** un docente tiene 1 comisión de clave PROG (Plus 1000) y 2 de clave BD (Plus 500)
- **THEN** `monto_plus` = 1×1000 + 2×500 = 2000

#### Scenario: Base se suma al total
- **WHEN** Base(PROFESOR)=5000 y `monto_plus`=2000
- **THEN** `total` = 7000

### Requirement: Exclusión de docentes facturantes de la liquidación general
Los docentes con modalidad facturante (`Usuario.facturador = true`) SHALL marcarse en su `Liquidacion` con `excluido_por_factura = true` y NO contar en el total de liquidación general; su pago se gestiona por el módulo de facturas.

#### Scenario: Facturante excluido del total general
- **WHEN** se calcula la liquidación de una cohorte que incluye un docente facturante
- **THEN** su registro aparece con `excluido_por_factura = true`, su `total` es informativo y NO suma al KPI "total sin factura"

### Requirement: Segmentación NEXO diferenciada
Las liquidaciones del rol NEXO SHALL marcarse con `es_nexo = true` y presentarse en un segmento diferenciado, pero su importe SHALL sumar al total general.

#### Scenario: NEXO en segmento propio
- **WHEN** se calcula una cohorte con un docente NEXO
- **THEN** su registro tiene `es_nexo = true`, aparece en el segmento NEXO y suma al total general

### Requirement: KPIs contables con y sin factura
La vista del período SHALL exponer `total_sin_factura` (universo en relación de dependencia, NEXO incluido) y `total_con_factura` (universo facturante) por separado.

#### Scenario: KPIs correctos
- **WHEN** la cohorte tiene docentes en relación de dependencia y facturantes
- **THEN** `total_sin_factura` suma solo los no-facturantes y `total_con_factura` suma solo los facturantes

### Requirement: Cierre inmutable de liquidación
El cierre de una liquidación (estado Abierta → Cerrada) SHALL inmutabilizar el registro: cualquier intento posterior de modificarlo SHALL ser rechazado. El cierre SHALL registrar auditoría `LIQUIDACION_CERRAR`.

#### Scenario: Cierre registra auditoría
- **WHEN** FINANZAS cierra una liquidación abierta
- **THEN** el estado pasa a Cerrada y se registra una entrada de auditoría `LIQUIDACION_CERRAR`

#### Scenario: Modificación tras cierre rechazada
- **WHEN** se intenta modificar o recalcular una liquidación ya Cerrada
- **THEN** el sistema responde 409/422 y el registro no cambia

### Requirement: Historial de liquidaciones cerradas
El sistema SHALL exponer el historial de liquidaciones cerradas con filtros por cohorte y período.

#### Scenario: Filtrar historial por cohorte y período
- **WHEN** FINANZAS consulta el historial filtrando por una cohorte y un período
- **THEN** recibe solo las liquidaciones cerradas que coinciden

### Requirement: Gestión de facturas de docentes facturantes
El sistema SHALL permitir cargar facturas (`detalle`, `referencia_archivo`, `tamano_kb`, `periodo`, `usuario_id`) en estado Pendiente y cambiar su estado entre Pendiente y Abonada, registrando `abonada_at` al abonarse.

#### Scenario: Carga y cambio de estado de factura
- **WHEN** FINANZAS carga una factura y luego la marca Abonada
- **THEN** la factura queda en estado Abonada con `abonada_at` seteado

#### Scenario: Filtros de facturas
- **WHEN** FINANZAS lista facturas filtrando por estado Pendiente
- **THEN** recibe solo las facturas pendientes del tenant

### Requirement: Aislamiento multi-tenant
Todas las operaciones de liquidaciones y facturas SHALL filtrar por `tenant_id` de la sesión; un tenant nunca SHALL ver datos de otro.

#### Scenario: Tenant A no ve liquidaciones de tenant B
- **WHEN** un usuario de tenant A consulta liquidaciones existentes en tenant B
- **THEN** no recibe ningún registro de tenant B

### Requirement: Control de acceso FINANZAS
Todos los endpoints `/api/liquidaciones/*` y `/api/facturas/*` SHALL exigir el permiso correspondiente (`liquidaciones:operar`, `liquidaciones:cerrar`, `facturas:gestionar`). Sin permiso → 403 (fail-closed).

#### Scenario: Acceso sin permiso denegado
- **WHEN** un usuario sin permiso de liquidaciones invoca cualquier endpoint del módulo
- **THEN** el sistema responde 403
