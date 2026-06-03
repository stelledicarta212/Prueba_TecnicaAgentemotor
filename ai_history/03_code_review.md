# Code Review

Este archivo contiene mi revisión del endpoint generado por IA para listar pólizas vencidas de un asesor.

Mi enfoque no fue revisar solo si el código funciona o no funciona. Me enfoqué principalmente en si la solución ayuda realmente a resolver el problema de María: dejar de depender de un Excel, priorizar bien su cartera y no perder clientes por falta de seguimiento.

---

## 1. El endpoint resuelve solo una parte del problema

### Dónde está

En la función completa:

```python
def list_expired_policies(advisor_id):

Qué está mal

El endpoint lista pólizas vencidas, pero el problema de María no es simplemente "ver pólizas vencidas".

El problema real es que María necesita saber:

qué pólizas debe gestionar primero;
qué clientes todavía están dentro de una ventana comercial útil;
qué clientes ya pasaron a una situación más difícil de recuperar;
qué se habló con cada cliente;
qué acciones están pendientes.

El código genera un listado, pero no construye una herramienta de gestión.

Por qué importa

Un listado de vencidas puede parecer útil, pero sigue dejando mucho trabajo manual a María. Ella tendría que interpretar los datos, recordar qué pasó con cada cliente y decidir sola el orden de atención.

Eso se parece demasiado al Excel que se quiere reemplazar.

Qué se rompe para María

María puede seguir perdiendo clientes aunque tenga una lista de pólizas vencidas, porque el sistema no le está ayudando a priorizar ni a tomar decisiones comerciales claras.

Cómo lo corregiría

Diseñaría el endpoint y el dashboard alrededor de prioridades operativas, no solo alrededor de vencimientos.

Por eso en mi solución trabajé con estas categorías:

próxima a vencer;
ventana crítica;
nueva contratación;
renovada.

La idea es que María no solo vea datos, sino que entienda inmediatamente dónde actuar.

2. La prioridad no respeta la regla importante del negocio
Dónde está

En esta línea:

priority = 'urgent' if days_overdue > 7 else 'normal'
Qué está mal

La prioridad se basa en 7 días, pero el enunciado de Agentemotor habla de una ventana crítica de 30 días después del vencimiento.

Ese detalle cambia completamente la lógica del negocio. Una póliza vencida hace 5 días todavía tiene una oportunidad clara de renovación. Una póliza vencida hace 35 días ya debe tratarse más como nueva contratación.

El código no diferencia bien esos escenarios.

Por qué importa

La prioridad es la regla que define el orden de trabajo de María. Si esa regla está mal, todo el sistema puede empujarla a gestionar mal su cartera.

Qué se rompe para María

María podría dedicar tiempo a pólizas menos importantes y dejar pasar pólizas que todavía están dentro de la ventana crítica de 30 días.

Eso impacta directamente en pérdida de clientes y oportunidad comercial.

Cómo lo corregiría

Usaría una clasificación alineada con el negocio:

if 0 <= days_until_expiration <= 30:
    priority = "proxima_a_vencer"
elif -30 <= days_until_expiration <= -1:
    priority = "ventana_critica"
elif days_until_expiration < -30:
    priority = "nueva_contratacion"
else:
    priority = "sin_prioridad"

Y esta regla debe vivir en backend, no en frontend, para que exista una sola versión de la verdad.

3. El código cuenta intentos de contacto, pero no conserva contexto suficiente
Dónde está

En esta parte:

cursor.execute(
    "SELECT COUNT(*) FROM contact_attempts WHERE policy_id = ?",
    (policy_id,)
)
attempts = cursor.fetchone()[0]
Qué está mal

El código solo devuelve cuántos intentos de contacto existen.

Pero para María no basta saber que hubo 3 intentos. Lo importante es saber qué pasó en cada uno:

si el cliente contestó;
si pidió cotización;
si dijo que llamaran después;
si no está interesado;
qué canal se usó;
qué observación dejó el asesor.

El número de intentos es una métrica pobre si no viene acompañado de contexto.

Por qué importa

El problema original menciona pérdida de contexto. Si el sistema solo guarda o muestra conteos, no está resolviendo uno de los dolores principales.

Qué se rompe para María

María puede llamar a un cliente sin saber que ya había pedido una cotización o que había dicho que lo llamaran otro día. Eso genera una mala experiencia para el cliente y hace que el sistema pierda valor.

Cómo lo corregiría

Además del conteo, devolvería un historial de gestiones con:

canal;
resultado;
notas;
fecha de intento.

Ese historial debe estar asociado a la póliza y persistido en la base de datos.

4. El diseño está centrado en la consulta, no en el flujo de trabajo
Dónde está

En el diseño general del endpoint:

GET /advisors/<advisor_id>/expired-policies
Qué está mal

El endpoint está pensado como una consulta aislada: "dame pólizas vencidas".

Pero el flujo de María necesita más que consultar. Necesita gestionar:

ver qué requiere atención;
contactar al cliente;
registrar el resultado;
renovar si corresponde;
dejar trazabilidad;
ver el dashboard actualizado.

El código no muestra una estrategia para completar ese ciclo.

Por qué importa

Una aplicación útil para María debe reemplazar el Excel completo, no solo una pestaña del Excel.

Qué se rompe para María

Si el sistema no permite registrar acciones y ver el estado actualizado, María termina usando la app para mirar datos y vuelve al Excel para operar.

Cómo lo corregiría

Diseñaría una API con endpoints de operación, por ejemplo:

GET /api/dashboard
POST /api/contact-attempts
POST /api/policies/{id}/renew

Y si el alcance lo permite:

POST /api/policies
PUT /api/policies/{id}
PATCH /api/policies/{id}/archive

Así el sistema no solo informa, también permite trabajar.

5. No existe una fuente de verdad clara más allá de la consulta directa
Dónde está

En el uso directo de SQLite dentro del endpoint:

conn = sqlite3.connect(DB)
cursor = conn.cursor()
Qué está mal

El endpoint accede directamente a la base de datos y arma toda la lógica en una sola función.

Esto no es solo un problema técnico. También afecta la claridad del sistema: no queda bien separado dónde se consulta, dónde se valida y dónde vive la regla de negocio.

Por qué importa

Si la lógica queda repartida o mezclada, es más fácil que en el futuro frontend, backend o scripts calculen cosas distintas.

Qué se rompe para María

Podrían aparecer inconsistencias: una póliza marcada como urgente en un lugar y normal en otro, o un dashboard que no refleje realmente lo persistido.

Cómo lo corregiría

Definiría explícitamente la base de datos como fuente de verdad y haría que toda modificación pase por la API.

También separaría el acceso a datos en un módulo propio para que los endpoints no dependan de detalles de SQLite.

6. No hay manejo suficiente de casos incompletos o inconsistentes
Dónde está

En varias partes de la función, por ejemplo:

client = cursor.fetchone()

Y después:

'client_name': client[0]
'client_phone': client[1]
Qué está mal

El código asume que siempre existe un cliente válido para cada póliza y que la fecha siempre está bien formada.

En una operación real, especialmente si María viene de Excel, pueden existir datos incompletos, duplicados o mal migrados.

Por qué importa

Un solo dato malo no debería tumbar todo el endpoint.

Qué se rompe para María

María podría perder acceso a todo el listado solo porque una póliza tiene una fecha inválida o un cliente no relacionado correctamente.

Cómo lo corregiría

Haría dos cosas:

reforzar integridad en base de datos con claves foráneas y restricciones;
devolver errores JSON controlados cuando algo no se pueda procesar.
7. El endpoint expone datos por advisor_id sin una estrategia de seguridad
Dónde está

En la ruta:

@app.route('/advisors/<advisor_id>/expired-policies', methods=['GET'])
Qué está mal

El asesor se define desde la URL. En un sistema real, cualquier usuario podría cambiar ese valor e intentar consultar datos de otro asesor.

Para la prueba se puede dejar autenticación fuera de alcance, pero como revisión de producción este punto debe mencionarse.

Por qué importa

El sistema maneja datos sensibles de clientes, teléfonos, pólizas y aseguradoras.

Qué se rompe para María

La cartera de María podría ser visible para otro asesor o usuario no autorizado.

Cómo lo corregiría

En producción agregaría autenticación y obtendría el asesor desde la sesión del usuario autenticado, no desde un parámetro manipulable.

En el alcance de la prueba, lo documentaría claramente como una funcionalidad excluida por tiempo.

Conclusión

El código generado por IA puede servir como punto de partida, pero responde de forma muy literal al prompt: lista pólizas vencidas.

El problema de Agentemotor requiere algo más que listar datos. Requiere construir una herramienta que ayude a María a priorizar, registrar contexto, renovar y mantener una fuente de verdad confiable.

Mi principal conclusión es que el valor no está en tener un endpoint que devuelva pólizas vencidas, sino en diseñar un flujo de trabajo que reduzca la pérdida de clientes.

Por eso en mi solución prioricé:

clasificación por regla de negocio de 30 días;
dashboard operativo;
historial de gestiones;
renovación de pólizas;
SQLite como fuente de verdad;
backend como lugar único para reglas críticas;
tests sobre el comportamiento más importante.