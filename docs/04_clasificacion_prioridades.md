flowchart TD

A[Poliza]
--> B{Estado frente a la fecha actual}

B -->|Vence en los proximos 30 dias| C[Proxima a vencer]

B -->|Vencio hace 1 a 30 dias| D[Ventana critica de renovacion]

B -->|Vencio hace mas de 30 dias| E[Nueva contratacion]

C --> F[Prioridad Media]

D --> G[Prioridad Alta]

E --> H[Prioridad Baja]

### Descripción del Diagrama 4 — Clasificación de Prioridades

Este diagrama representa la regla de negocio más importante de la solución propuesta. El objetivo principal de la aplicación no es únicamente almacenar pólizas, sino ayudar al asesor a identificar cuáles requieren atención inmediata para maximizar las probabilidades de renovación.

La clasificación se realiza comparando la fecha de vencimiento de cada póliza contra la fecha actual. A partir de esta comparación, las pólizas se agrupan en tres categorías operativas.

Las pólizas que vencerán en los próximos 30 días son consideradas oportunidades de gestión preventiva y reciben una prioridad media. En este escenario el asesor puede contactar al cliente antes del vencimiento para iniciar el proceso de renovación con suficiente anticipación.

Las pólizas vencidas entre 1 y 30 días constituyen la ventana crítica de renovación definida en el contexto del negocio. Estas reciben la máxima prioridad debido a que aún pueden renovarse conservando las condiciones comerciales favorables para el intermediario.

Finalmente, las pólizas vencidas hace más de 30 días son clasificadas como posibles nuevas contrataciones. Aunque siguen siendo oportunidades comerciales, ya no se encuentran dentro de la ventana estratégica de renovación y, por lo tanto, reciben una prioridad menor.

Esta clasificación permite transformar una lista extensa de pólizas en una cola de trabajo priorizada, ayudando al asesor a concentrar sus esfuerzos en las oportunidades con mayor impacto para la retención de clientes y la generación de ingresos.