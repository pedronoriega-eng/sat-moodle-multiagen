import logging
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

from config import settings
from agents import coordinator_agent
from database import db_manager

# Configuración de Logging
logger = logging.getLogger("SAT_Main")
logging.basicConfig(level=logging.INFO)

# Inicialización de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Motor de Alertas Tempranas Institucional SAT-V 2026 impulsado por enjambre multiagente FIPA-ACL y Gemini 1.5/3.1."
)

# Configuración de CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ESQUEMAS DE ENTRADA Y SALIDA (PYDANTIC V2)
# =============================================================================
class MoodleLogRequest(BaseModel):
    moodle_id: str = Field(..., example="EST-2026-8841")
    nombre_completo: str = Field(..., example="Carlos Eduardo Pérez")
    email: EmailStr = Field(..., example="carlos.perez@institucion.edu.co")
    nivel_academico: str = Field(..., example="pregrado", description="'pregrado' o 'posgrado'")
    programa: str = Field(..., example="Ingeniería de Software Virtual")
    dias_inactividad: int = Field(default=0, ge=0, example=4)
    total_clics: int = Field(default=0, ge=0, example=120)
    minutos_navegacion: float = Field(default=0.0, ge=0.0, example=45.5)
    descargas_rafaga: int = Field(default=0, ge=0, example=0, description="Descargas <60s")
    calificaciones: List[Optional[Any]] = Field(
        default_factory=list,
        example=[3.5, 0.0, None, 4.0],
        description="Lista de notas evaluadas (ceros explícitos incluidos, celdas vacías/guiones omitidos)"
    )

class ProcessResponse(BaseModel):
    mensaje: str
    moodle_id: str
    estado: str
    timestamp: str

# =============================================================================
# ENDPOINTS
# =============================================================================
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Endpoint de diagnóstico de salud del servicio.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_mock_mode": db_manager.use_mock
    }

async def task_procesar_estudiante(payload_dict: Dict[str, Any]):
    """
    Tarea asíncrona ejecutada en segundo plano por FastAPI BackgroundTasks.
    """
    try:
        res = await coordinator_agent.execute_sat_pipeline(payload_dict)
        logger.info(f"Procesamiento en segundo plano completado para: {res['moodle_id']} -> Riesgo: {res['nivel_riesgo']}")
    except Exception as e:
        logger.error(f"Error procesando estudiante en segundo plano: {e}")

@app.post(
    f"{settings.API_PREFIX}/procesar",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ProcessResponse
)
async def procesar_estudiante(request: MoodleLogRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal POST para ingestar logs de Moodle.
    Retorna 202 Accepted inmediatamente y procesa el enjambre de agentes en segundo plano.
    """
    payload_dict = request.model_dump()
    
    # Encolar procesamiento no bloqueante
    background_tasks.add_task(task_procesar_estudiante, payload_dict)
    
    from datetime import datetime
    return ProcessResponse(
        mensaje="Solicitud de evaluación SAT recibida exitosamente. Procesando en segundo plano.",
        moodle_id=request.moodle_id,
        estado="EN_PROCESAMIENTO",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get(f"{settings.API_PREFIX}/moodle/curso/{{course_id}}/evaluar")
async def evaluar_curso_moodle(course_id: int, background_tasks: BackgroundTasks):
    """
    Endpoint para disparar la evaluación masiva del enjambre multiagente sobre los estudiantes
    matriculados en un curso de Moodle (ej. Curso ID 956 de Tecnológico del Oriente).
    """
    from moodle_connector import moodle_connector
    estudiantes = moodle_connector.get_enrolled_students(course_id)
    
    if not estudiantes:
        # Fallback a simulación estructurada para el Curso 956 si no hay Token activo
        estudiantes_simulados = [
            {
                "moodle_id": f"EST-M956-{idx+1:03d}",
                "nombre_completo": f"Estudiante Moodle {idx+1}",
                "email": f"estudiante{idx+1}@tecnologicadeloriente.edu.co",
                "nivel_academico": "pregrado" if idx % 2 == 0 else "posgrado",
                "programa": "Educación Virtual - Curso 956",
                "dias_inactividad": (idx * 2) % 7,
                "total_clics": 100 + (idx * 30),
                "minutos_navegacion": 45.0 + (idx * 15),
                "descargas_rafaga": 2 if idx == 1 else 0,
                "calificaciones": [3.5 + (idx * 0.2), 0.0, None]
            }
            for idx in range(5)
        ]
        for est in estudiantes_simulados:
            background_tasks.add_task(task_procesar_estudiante, est)
        
        return {
            "mensaje": f"Evaluación en curso iniciada para {len(estudiantes_simulados)} estudiantes del Curso Moodle ID {course_id} (Modo Simulación Activo).",
            "course_id": course_id,
            "estudiantes_encolados": len(estudiantes_simulados)
        }
    
    for est in estudiantes:
        payload = {
            "moodle_id": str(est.get("id")),
            "nombre_completo": est.get("fullname", "Estudiante Moodle"),
            "email": est.get("email", "estudiante@tecnologicadeloriente.edu.co"),
            "nivel_academico": "pregrado",
            "programa": f"Curso Moodle ID {course_id}",
            "dias_inactividad": 0,
            "total_clics": 50,
            "minutos_navegacion": 30.0,
            "descargas_rafaga": 0,
            "calificaciones": []
        }
        background_tasks.add_task(task_procesar_estudiante, payload)
        
    return {
        "mensaje": f"Evaluación iniciada para {len(estudiantes)} estudiantes matriculados en el Curso ID {course_id}.",
        "course_id": course_id,
        "total_estudiantes": len(estudiantes)
    }

@app.get(f"{settings.API_PREFIX}/estudiantes/{{moodle_id}}/alertas")
async def obtener_alertas_estudiante(moodle_id: str):
    """
    Consulta el historial de alertas registradas en Supabase / Persistencia para un estudiante.
    """
    historial = await db_manager.obtener_historial_estudiante(moodle_id)
    return {
        "moodle_id": moodle_id,
        "total_alertas": len(historial),
        "alertas": historial
    }
