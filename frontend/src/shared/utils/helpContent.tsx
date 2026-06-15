// shared/utils/helpContent.tsx — Contenido de ayuda centralizado (help-system-content skill)
// Cada clave corresponde a una pagina principal. Importar en la pagina y pasar a PageHelp.
import type { ReactNode } from 'react'

type HelpContentMap = Record<string, ReactNode>

export const helpContent: HelpContentMap = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  login: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Acceso al sistema</p>
      <p>Ingresa tu email institucional y contrasena para acceder. Si tu cuenta tiene autenticacion de dos factores (2FA) activa, se solicitara un codigo adicional.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Email:</strong> Tu direccion de correo institucional.</li>
        <li><strong>Contrasena:</strong> Minimo 8 caracteres.</li>
        <li><strong>Codigo 2FA:</strong> Generado por tu app autenticadora (si aplica).</li>
      </ul>
      <div className="bg-blue-50 p-3 rounded-md">
        <p className="text-blue-700 text-xs">Si olvidaste tu contrasena, usa la opcion "Recuperar contrasena" en la pantalla de inicio.</p>
      </div>
    </div>
  ),

  // ── Dashboard ─────────────────────────────────────────────────────────────
  dashboard: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Panel principal</p>
      <p>Vista general del sistema segun tu rol. Desde aqui accedes a todos los modulos disponibles.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Comision:</strong> Gestion de calificaciones, atrasados y comunicaciones.</li>
        <li><strong>Coordinacion:</strong> Equipos, tareas, encuentros y avisos (COORDINADOR/ADMIN).</li>
        <li><strong>Finanzas:</strong> Liquidaciones y honorarios (FINANZAS/ADMIN).</li>
        <li><strong>Admin:</strong> Estructura academica, usuarios y auditoria (ADMIN).</li>
      </ul>
    </div>
  ),

  // ── Comision — Importacion ────────────────────────────────────────────────
  importacion: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Importar calificaciones</p>
      <p>Sube un archivo CSV o XLSX exportado desde Moodle para importar las calificaciones de una comision.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Formato:</strong> CSV o XLSX exportado desde el libro de calificaciones de Moodle.</li>
        <li><strong>Columnas (Real):</strong> Solo se importan columnas con sufijo "(Real)" — nota numerica.</li>
        <li><strong>Preview:</strong> Antes de confirmar podes ver un resumen de los datos a importar.</li>
        <li><strong>Umbral:</strong> Configura el porcentaje minimo de aprobacion para esta materia.</li>
      </ul>
      <div className="bg-amber-50 p-3 rounded-md">
        <p className="text-amber-700 text-xs">La importacion reemplaza las calificaciones existentes para el mismo periodo y materia.</p>
      </div>
    </div>
  ),

  // ── Comision — Atrasados ──────────────────────────────────────────────────
  atrasados: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Alumnos atrasados</p>
      <p>Lista de alumnos que estan por debajo del umbral de aprobacion o tienen entregas faltantes.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Atrasado:</strong> Nota inferior al umbral configurado O entrega faltante.</li>
        <li><strong>Filtros:</strong> Podes filtrar por actividad, estado y criterio de atraso.</li>
        <li><strong>Comunicar:</strong> Selecciona alumnos y usa "Comunicar" para enviar mensajes.</li>
      </ul>
    </div>
  ),

  // ── Comision — Comunicacion ───────────────────────────────────────────────
  comunicacion: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Comunicaciones a alumnos</p>
      <p>Redacta y envia mensajes a los alumnos seleccionados. Todos los mensajes quedan registrados en el sistema.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Preview:</strong> Siempre revisa el mensaje antes de enviar.</li>
        <li><strong>Aprobacion:</strong> Segun la configuracion del tenant, puede requerirse aprobacion administrativa.</li>
        <li><strong>Tracking:</strong> Seguimiento del estado: Pendiente → Enviando → Enviado / Error.</li>
      </ul>
      <div className="bg-amber-50 p-3 rounded-md">
        <p className="text-amber-700 text-xs">Una vez enviado, el mensaje no puede modificarse. Usa el preview para verificar antes de confirmar.</p>
      </div>
    </div>
  ),

  // ── Comision — Monitor ────────────────────────────────────────────────────
  monitor: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Monitor de calificaciones</p>
      <p>Vista en tiempo real del estado de calificaciones de la comision.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Por actividad:</strong> Ve el estado de entrega por cada actividad evaluable.</li>
        <li><strong>Sin corregir:</strong> Entregas recibidas que aun no tienen nota.</li>
        <li><strong>Ranking:</strong> Alumnos ordenados por rendimiento.</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Equipos ────────────────────────────────────────────────
  equipos: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Asignaciones docentes</p>
      <p>Gestion de asignaciones de docentes a materias y comisiones con vigencia por periodo.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Asignar:</strong> Vincula un docente a una materia con rol y fechas de vigencia.</li>
        <li><strong>Clonar:</strong> Duplica el equipo de un cuatrimestre anterior para agilizar el armado.</li>
        <li><strong>Exportar CSV:</strong> Descarga el listado de asignaciones vigentes.</li>
        <li><strong>Vigencia masiva:</strong> Actualiza las fechas de hasta para multiples asignaciones a la vez.</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Tareas ─────────────────────────────────────────────────
  tareas: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Tareas internas</p>
      <p>Gestion de tareas de coordinacion con asignacion, seguimiento y comentarios.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Estado:</strong> Pendiente → En progreso → Resuelta / Cancelada.</li>
        <li><strong>Delegar:</strong> Reasigna la tarea a otro miembro del equipo.</li>
        <li><strong>Comentarios:</strong> Hilo cronologico de comentarios por tarea.</li>
        <li><strong>Prioridad:</strong> Baja / Media / Alta para ordenar el trabajo.</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Encuentros ─────────────────────────────────────────────
  encuentros: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Slots de encuentro</p>
      <p>Agenda de clases, tutorías y reuniones virtuales o presenciales con generacion de instancias recurrentes.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Recurrente:</strong> Indica cantidad de semanas para generar instancias automaticamente.</li>
        <li><strong>Unico:</strong> Usa 0 semanas para un encuentro de una sola vez.</li>
        <li><strong>Meet URL:</strong> Link de Google Meet u otra plataforma (opcional).</li>
        <li><strong>Exportar HTML:</strong> Genera bloque para insertar en el LMS.</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Coloquios ──────────────────────────────────────────────
  coloquios: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Evaluaciones y coloquios</p>
      <p>Gestion de instancias de evaluacion con cupos, reservas y registro de resultados.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Cupo:</strong> Maximo de alumnos que pueden reservar lugar.</li>
        <li><strong>Reservas:</strong> Los alumnos reservan su lugar hasta agotar el cupo.</li>
        <li><strong>Resultados:</strong> Registro del resultado (Aprobado / Desaprobado / Ausente).</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Avisos ─────────────────────────────────────────────────
  avisos: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Avisos institucionales</p>
      <p>Publicacion de avisos con control de vigencia y confirmacion de lectura (acknowledgment).</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Vigencia:</strong> Define desde/hasta cuando es visible el aviso.</li>
        <li><strong>Roles:</strong> Segmenta el aviso a roles especificos o todo el tenant.</li>
        <li><strong>ACK:</strong> Registra quienes confirmaron haber leido el aviso.</li>
        <li><strong>Archivar:</strong> Desactiva el aviso sin eliminarlo (queda en historial).</li>
      </ul>
    </div>
  ),

  // ── Coordinacion — Monitor Global ─────────────────────────────────────────
  monitorGlobal: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Monitor global de comisiones</p>
      <p>Vista consolidada del estado de todas las comisiones del cuatrimestre activo.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Estado:</strong> Cantidad de atrasados y sin corregir por comision.</li>
        <li><strong>Umbral:</strong> Porcentaje de aprobacion configurado por materia.</li>
        <li><strong>Acceso rapido:</strong> Click en una comision para ir a su vista detallada.</li>
      </ul>
    </div>
  ),

  // ── Finanzas — Periodo ────────────────────────────────────────────────────
  periodo: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Vista de liquidacion del periodo</p>
      <p>Calculo y cierre de liquidaciones de honorarios docentes para el periodo seleccionado.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Calcular:</strong> Genera los montos segun la grilla salarial vigente y asignaciones del periodo.</li>
        <li><strong>Segmentacion:</strong> Vista separada para docentes de planta, NEXO y facturantes.</li>
        <li><strong>KPIs:</strong> Total a liquidar, cantidad de docentes y promedio por rol.</li>
        <li><strong>Cerrar:</strong> Congela la liquidacion. No puede recalcularse una vez cerrada.</li>
      </ul>
      <div className="bg-amber-50 p-3 rounded-md">
        <p className="text-amber-700 text-xs">El cierre es irreversible. Verificar los montos antes de confirmar.</p>
      </div>
    </div>
  ),

  // ── Finanzas — Grilla Salarial ────────────────────────────────────────────
  grilla: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Grilla salarial</p>
      <p>Configuracion de los montos base y plus por rol y clave categorica.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Salario base:</strong> Monto fijo por rol (PROFESOR, TUTOR, NEXO, COORDINADOR).</li>
        <li><strong>Plus por clave:</strong> Adicional por comision segun la categoria de la materia.</li>
        <li><strong>Vigencia:</strong> Cada registro tiene desde/hasta. Se usa el vigente al momento del calculo.</li>
      </ul>
    </div>
  ),

  // ── Finanzas — Facturas ───────────────────────────────────────────────────
  facturas: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Facturas de docentes</p>
      <p>Gestion de facturas emitidas por docentes en modalidad facturante.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Estados:</strong> Pendiente → Aprobada → Pagada / Rechazada.</li>
        <li><strong>Docente facturante:</strong> No usa CBU — el pago se procesa contra la factura.</li>
      </ul>
    </div>
  ),

  // ── Finanzas — Historial ──────────────────────────────────────────────────
  historial: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Historial de liquidaciones</p>
      <p>Consulta de liquidaciones cerradas filtradas por periodo y cohorte.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Inmutables:</strong> Los registros cerrados no pueden modificarse.</li>
        <li><strong>Filtros:</strong> Periodo (YYYY-MM) y cohorte para acotar la busqueda.</li>
      </ul>
    </div>
  ),

  // ── Admin — Estructura Academica ──────────────────────────────────────────
  estructura: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Estructura academica</p>
      <p>Gestion del catalogo de carreras, cohortes y materias del tenant.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Carreras:</strong> Programas academicos con codigo unico por tenant.</li>
        <li><strong>Cohortes:</strong> Grupos de alumnos con vigencia (desde/hasta) vinculados a asignaciones.</li>
        <li><strong>Materias:</strong> Catalogo con codigo y categoria clave para el calculo de Plus.</li>
      </ul>
    </div>
  ),

  // ── Admin — Usuarios ──────────────────────────────────────────────────────
  usuarios: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Usuarios del tenant</p>
      <p>Gestion de cuentas de usuario con roles y datos de pago.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Activar/Desactivar:</strong> Los usuarios inactivos no pueden iniciar sesion.</li>
        <li><strong>CBU:</strong> Requerido para docentes de planta (no facturantes) antes de liquidar.</li>
        <li><strong>Roles:</strong> Se asignan via el modulo de asignaciones, no directamente aqui.</li>
      </ul>
      <div className="bg-amber-50 p-3 rounded-md">
        <p className="text-amber-700 text-xs">Los datos de PII (CBU, DNI, CUIL) se almacenan cifrados. Solo ADMIN puede verlos.</p>
      </div>
    </div>
  ),

  // ── Admin — Auditoria ─────────────────────────────────────────────────────
  auditoria: (
    <div className="space-y-3 text-sm text-gray-600">
      <p className="font-medium text-gray-800">Panel de auditoria</p>
      <p>Log inmutable de todas las acciones realizadas en el sistema.</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Log completo:</strong> Cada accion registra actor, accion, recurso, timestamp e IP.</li>
        <li><strong>Impersonacion:</strong> Las acciones por impersonacion muestran tanto el actor real como el impersonado.</li>
        <li><strong>Filtros:</strong> Por actor, accion, recurso y rango de fechas.</li>
      </ul>
      <div className="bg-blue-50 p-3 rounded-md">
        <p className="text-blue-700 text-xs">El log de auditoria es append-only — ningun registro puede eliminarse o modificarse.</p>
      </div>
    </div>
  ),
}
