import logging
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger("SAT_Database")
logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    """
    Gestor de persistencia asíncrono para Supabase Free Tier.
    Incluye capa de almacenamiento en memoria como fallback resiliente cuando
    las credenciales de Supabase no están configuradas en entorno local.
    """
    def __init__(self):
        self.supabase_client = None
        self.use_mock = False
        
        # En memoria fallback storage
        self._memory_estudiantes: Dict[str, Dict[str, Any]] = {}
        self._memory_interacciones: List[Dict[str, Any]] = []
        self._memory_alertas: List[Dict[str, Any]] = []

        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client, Client
                self.supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("✅ Conexión con Supabase establecida exitosamente.")
            except Exception as e:
                logger.warning(f"⚠️ Error al conectar con Supabase: {e}. Activando modo contingencia (Memory Mock).")
                self.use_mock = True
        else:
            logger.info("ℹ️ Credenciales SUPABASE no provistas. Operando en modo contingencia (In-Memory).")
            self.use_mock = True

    async def registrar_estudiante(self, estudiante_data: Dict[str, Any]) -> Dict[str, Any]:
        moodle_id = estudiante_data["moodle_id"]
        if self.use_mock:
            self._memory_estudiantes[moodle_id] = estudiante_data
            return estudiante_data
        
        try:
            res = self.supabase_client.table("estudiantes").upsert(estudiante_data).execute()
            return res.data[0] if res.data else estudiante_data
        except Exception as e:
            logger.error(f"Error al guardar estudiante en Supabase: {e}")
            self._memory_estudiantes[moodle_id] = estudiante_data
            return estudiante_data

    async def registrar_interaccion(self, interaccion_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            self._memory_interacciones.append(interaccion_data)
            return interaccion_data

        try:
            res = self.supabase_client.table("moodle_interacciones").insert(interaccion_data).execute()
            return res.data[0] if res.data else interaccion_data
        except Exception as e:
            logger.error(f"Error al registrar interacción en Supabase: {e}")
            self._memory_interacciones.append(interaccion_data)
            return interaccion_data

    async def registrar_alerta_sat(self, alerta_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            self._memory_alertas.append(alerta_data)
            return alerta_data

        try:
            res = self.supabase_client.table("historial_alertas_sat").insert(alerta_data).execute()
            return res.data[0] if res.data else alerta_data
        except Exception as e:
            logger.error(f"Error al guardar alerta SAT en Supabase: {e}")
            self._memory_alertas.append(alerta_data)
            return alerta_data

    async def obtener_historial_estudiante(self, moodle_id: str) -> List[Dict[str, Any]]:
        if self.use_mock:
            return [a for a in self._memory_alertas if a.get("estudiante_moodle_id") == moodle_id]

        try:
            res = self.supabase_client.table("historial_alertas_sat")\
                .select("*")\
                .eq("estudiante_moodle_id", moodle_id)\
                .order("fecha_evaluacion", desc=True)\
                .execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error al consultar historial de {moodle_id}: {e}")
            return [a for a in self._memory_alertas if a.get("estudiante_moodle_id") == moodle_id]

db_manager = DatabaseManager()
