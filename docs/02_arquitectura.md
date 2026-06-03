flowchart LR

U[María / Asesora]
--> FE[Frontend HTML, CSS y JavaScript]

FE --> API[API REST Flask]

API --> RS[Servicio de clasificación de renovaciones]

RS --> DB[(SQLite)]

API --> CA[Gestión de intentos de contacto]
CA --> DB

API --> RN[Gestión de renovación de pólizas]
RN --> DB

### Descripción del Diagrama 2 — Arquitectura de la solución

Este diagrama representa la arquitectura lógica de la aplicación propuesta para reemplazar el proceso manual que actualmente realiza María mediante hojas de cálculo. La solución adopta una arquitectura de tres capas compuesta por interfaz de usuario, lógica de negocio y persistencia de datos, priorizando simplicidad, mantenibilidad y facilidad de ejecución.

La capa de presentación está compuesta por una interfaz web desarrollada con HTML, CSS y JavaScript, desde donde el asesor puede consultar las pólizas de su cartera, registrar actividades de seguimiento y actualizar renovaciones. Esta interfaz consume los servicios expuestos por la API REST sin acceder directamente a la base de datos, garantizando una correcta separación de responsabilidades.

La capa de negocio se implementa mediante una API REST construida con Flask. Esta capa centraliza las reglas del dominio, incluyendo la clasificación de pólizas según su fecha de vencimiento, la gestión de intentos de contacto y el proceso de renovación. Concentrar estas reglas en el backend permite mantener consistencia en el comportamiento de la aplicación y facilita futuras extensiones funcionales.

Como mecanismo de persistencia se utiliza SQLite, una base de datos ligera que elimina dependencias externas y simplifica la ejecución del proyecto en cualquier entorno. Esta decisión está alineada con los requisitos de la prueba técnica, donde se privilegia la facilidad de despliegue sobre la escalabilidad empresarial.

Desde una perspectiva arquitectónica, el diseño busca maximizar la claridad y minimizar la complejidad innecesaria. Se evita introducir componentes como autenticación, colas de procesamiento, microservicios o integraciones externas debido a que no aportan valor directo al objetivo principal de la prueba: proporcionar una herramienta que permita gestionar eficazmente el ciclo de renovación de pólizas y reducir la pérdida de clientes por falta de seguimiento oportuno.