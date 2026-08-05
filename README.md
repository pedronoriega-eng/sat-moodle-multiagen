# Sistema de Alertas Tempranas (SAT-V) Moodle 2026

Motor asíncrono y distribuido de retención y permanencia estudiantil en modalidad virtual, alimentado por un enjambre multiagente (estilo FIPA-ACL) y modelos **Google Gemini (1.5 Flash / 1.5 Pro)** sobre **FastAPI** y **Supabase Free Tier**.

## 📌 Características Principales

1. **Enjambre Multiagente FIPA-ACL (`asyncio.Queue`)**:
   - **HarvesterAgent (Gemini 1.5 Flash)**: Filtrado y normalización de logs crudos de Moodle.
   - **EvaluatorAgent (Gemini 1.5 Flash)**: Aplicación rigurosa de las reglas del Manual SAT 2026.
   - **NotifierAgent (Gemini 1.5 Flash)**: Generación y envío asíncrono de alertas SMTP dinámicas.
   - **CoordinatorAgent (Gemini 1.5/3.1 Pro)**: Supervisión, prevención de bucles e integridad relacional.

2. **Reglas de Negocio Institucionales SAT 2026**:
   - **Inclusión Explícita de Ceros (0.0)** en la nota acumulada evaluada.
   - **Exclusión Estricta de Celdas Vacías (`-`)** (semanas futuras / no calificadas).
   - **Asimetría de Umbrales**: Pregrado ($\ge 3.0$) vs Posgrado ($\ge 3.5$).
   - **Regla de Veto Aprobatorio**: Promedio aprobatorio prevalece e invalida Alerta Roja por volumen secundario.
   - **Dwell Time & Descargas en Ráfaga (<60s)**.

3. **Arquitectura Backend & Persistencia**:
   - **FastAPI**: Endpoint `POST /api/v1/sat/procesar` no bloqueante (`HTTP 202 Accepted` + `BackgroundTasks`).
   - **Supabase**: Esquema relacional optimizado (`estudiantes`, `moodle_interacciones`, `historial_alertas_sat`).

---

## 🚀 Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/usuario/sat-moodle-multiagent.git
cd sat-moodle-multiagent

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (.env)
cp .env.example .env

# 4. Ejecutar la suite de pruebas de integración
python test_sat_system.py

# 5. Iniciar el servidor FastAPI
uvicorn main:app --reload --port 8000
```

---

## 📄 Endpoints API

- `POST /api/v1/sat/procesar`: Recibe payload de logs Moodle y encola la evaluación multiagente.
- `GET /api/v1/sat/estudiantes/{moodle_id}/alertas`: Consulta el historial de alertas.
- `GET /health`: Diagnóstico de disponibilidad del servicio.
