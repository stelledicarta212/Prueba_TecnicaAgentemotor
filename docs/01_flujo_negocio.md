---
config:
  layout: elk
---
flowchart TD
    A[María ingresa al dashboard]
    --> B[Visualiza pólizas de su cartera]
    B --> C{Clasificación de vencimiento}
    C -->|Próximas a vencer| D[Gestionar preventivamente]
    C -->|Vencidas entre 1 y 30 días| E[Prioridad crítica de recuperación]
    C -->|Vencidas hace más de 30 días| F[Posible nueva contratación]
    D --> G[Registrar llamada, WhatsApp o email]
    E --> G
    F --> G
    G --> H[Guardar intento de contacto y nota]
    H --> I{El cliente renovó?}
    I -->|Sí| J[Marcar póliza como renovada]
    J --> K[Registrar nueva fecha de vencimiento]
    I -->|No| L[Mantener pendiente para seguimiento]
    
    classDef processNode stroke:#818cf8,fill:#eef2ff
    classDef decisionNode stroke:#fb923c,fill:#fff7ed
    classDef actionNode stroke:#4ade80,fill:#f0fdf4
    
    class A,B,G,H,J,K,D,E,F,L processNode
    class C,I decisionNode
    class A actionNode

### Descripción del Diagrama 1 — Flujo principal de negocio

Este diagrama representa el proceso operativo que realiza un asesor de seguros para gestionar la renovación de pólizas de su cartera de clientes. El flujo inicia cuando María accede al dashboard principal y visualiza las pólizas clasificadas según su estado de vencimiento. Esta clasificación permite priorizar el trabajo diario enfocándose en los casos con mayor impacto comercial.

La aplicación distingue tres escenarios principales: pólizas próximas a vencer, pólizas vencidas dentro de la ventana crítica de 30 días y pólizas vencidas fuera de dicha ventana. Esta segmentación responde directamente a la regla de negocio descrita en el enunciado, donde las pólizas vencidas dentro de los primeros 30 días aún pueden renovarse conservando beneficios operativos para el intermediario.

Una vez identificada una póliza, el asesor puede registrar acciones comerciales como llamadas telefónicas, mensajes de WhatsApp o correos electrónicos. Cada interacción queda almacenada junto con observaciones que permiten conservar el contexto histórico de la relación con el cliente y evitar la pérdida de información que actualmente ocurre en el manejo manual mediante hojas de cálculo.

Finalmente, el flujo contempla dos posibles resultados: la renovación de la póliza o la continuidad del seguimiento comercial. En caso de renovación, el sistema actualiza la fecha de vencimiento y mantiene el historial de gestión asociado. En caso contrario, la póliza permanece activa dentro del proceso de seguimiento para futuras acciones.

El objetivo principal de este flujo es proporcionar una herramienta centralizada que permita al asesor priorizar oportunidades de renovación, mantener trazabilidad sobre las gestiones realizadas y reducir la pérdida de clientes ocasionada por vencimientos no gestionados oportunamente.