# Rahab ⏱️

**Rahab** es una aplicación de escritorio avanzada diseñada específicamente para gestionar, cronometrar y proyectar los tiempos de las asignaciones en reuniones de forma fluida. Proveemos el código completo de manera totalmente transparentes para cumplir con las normas de seguridad y confiabilidad.

---

## 🚀 ¿Qué es y para qué sirve?
Rahab actúa como un panel de control maestro para el manejo del tiempo en las reuniones. Sus características principales son:
* **Sincronización automática:** Extrae la información y los tiempos de las asignaciones directamente desde www.jw.org de la semana actual.
* **Gestión flexible de tiempos:** Permite añadir, editar, eliminar y reordenar asignaciones (mediante botones) tanto automáticas como manuales.
* **Proyección en múltiples pantallas:** Envía de forma automática el cronómetro a pantalla completa en la pantalla extendida seleccionada.
* **Alertas visuales:** El reloj cambia de color dinámicamente a medida que se agota el tiempo (aviso en amarillo al faltar 1 minuto y en rojo al excederse).
* **Mensajes flotantes:** Permite enviar avisos de texto breves que se muestran instantáneamente debajo del reloj en la pantalla de proyección.

---

## 🕹️ Cómo se usa la aplicación
1. **Pantalla Principal (Panel de Control):** Al abrir la aplicacióin, se verá la lista de asignaciones de la semana en formato de tabla, con su duración prevista y el tiempo real transcurrido.
2. **Iniciar / Parar y Auto-avance:** Haz clic en **Iniciar / Parar** para controlar el cronómetro. Al detener una asignación, el sistema pasará automáticamente a la siguiente de la lista, dejándola preparada para el siguiente turno.
3. **Segunda Pantalla:** La aplicación detecta las pantallas conectadas y abrirá automáticamente el cronómetro en la última pantalla extendida (configurable desde el botón de Ajustes ⚙).
4. **Mensajes al Proyector:** Escribe cualquier nota breve en la sección "Mensaje en Proyector" del panel lateral y pulsa **Mostrar** para que se muestre por pantalla.

---

## 💻 Instalación y Ejecución

Si bien en el repositorio está disponible una versión precompilada, proveemos con total transparencia el código fuente del aplicativo. Invitamos a todos a desconfiar de software precompilado, por lo que animamos a compilarlo manualmente.

### Instrucciones para compilar:


1. Asegúrese de tener instalado **Python** en tu sistema.
2. Abra Powershell/CMD en el directorio del proyecto e instale las librerías necesarias ejecutando:
   `python -m pip install requests beautifulsoup4 PyQt6 pyinstaller`
3. Compile la aplicación ejecutando el comando de empaquetado:
   `python -m PyInstaller --noconsole --onefile --icon="rahab_icon.ico" main.py`
4. Encontrarás tu archivo ejecutable `rahab.exe` listo para usar dentro de la carpeta `dist`.

---

## 🛑 Aviso sin Ánimo de Lucro y Licencia

* **Sin ánimo de lucro:** Rahab es un proyecto desarrollado de forma completamente altruista. **No se acepta ningún tipo de donación, aportación económica ni patrocinio** a cambio de esta herramienta.
* **Licencia de Código Abierto (Open Source con Restricción No Comercial):** 
  Este software es de código abierto. Todo el mundo tiene el derecho absoluto de descargarlo, usarlo, estudiarlo y modificarlo libremente. 
  
  **Restricción estricta:** Queda **totalmente prohibida** la venta, comercialización, distribución con fines lucrativos o la solicitud de donaciones bajo cualquier pretexto utilizando este software o sus derivadas.