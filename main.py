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
