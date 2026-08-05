import logging
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger("SAT_Database")
logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    """
    Gestor de persistencia asíncrono para Supabase Free Tier vía REST API nativa.
    """
    def __init__(self):
        self.url = settings.SUPABASE_URL.rstrip('/')
        self.key = settings.SUPABASE_KEY
        self.rest_url = f"{self.url}/rest/v1"
        self.use_mock = False

        if not self.key or not self.url:
            logger.info("ℹ️ Credenciales SUPABASE no provistas. Operando en modo contingencia (In-Memory).")
            self.use_mock = True
        else:
            logger.info(f"✅ Cliente Supabase REST listo en {self.rest_url}")

        # En memoria fallback storage
        self._memory_estudiantes: Dict[str, Dict[str, Any]] = {}
        self._memory_interacciones: List[Dict[str, Any]] = []
        self._memory_alertas: List[Dict[str, Any]] = []

    def _headers(self, prefer: Optional[str] = None) -> Dict[str, str]:
        h = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if prefer:
            h["Prefer"] = prefer
        return h

    async def registrar_estudiante(self, estudiante_data: Dict[str, Any]) -> Dict[str, Any]:
        moodle_id = estudiante_data["moodle_id"]
        if self.use_mock:
            self._memory_estudiantes[moodle_id] = estudiante_data
            return estudiante_data

        try:
            req_url = f"{self.rest_url}/estudiantes"
            data_bytes = json.dumps([estudiante_data]).encode('utf-8')
            headers = self._headers()
            headers["Prefer"] = "resolution=merge-duplicates,return=representation"
            req = urllib.request.Request(
                req_url,
                data=data_bytes,
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                logger.info(f"✅ Estudiante registrado en Supabase: {moodle_id}")
                return res[0] if res else estudiante_data
        except Exception as e:
            logger.warning(f"⚠️ Error al guardar estudiante en Supabase REST ({e}). Usando fallback en memoria.")
            self._memory_estudiantes[moodle_id] = estudiante_data
            return estudiante_data

    async def registrar_interaccion(self, interaccion_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            self._memory_interacciones.append(interaccion_data)
            return interaccion_data

        try:
            req_url = f"{self.rest_url}/moodle_interacciones"
            data_bytes = json.dumps([interaccion_data]).encode('utf-8')
            req = urllib.request.Request(
                req_url,
                data=data_bytes,
                headers=self._headers(prefer="return=representation"),
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                logger.info(f"✅ Interacción Moodle registrada en Supabase para {interaccion_data.get('estudiante_moodle_id')}")
                return res[0] if res else interaccion_data
        except Exception as e:
            logger.warning(f"⚠️ Error al registrar interacción en Supabase REST ({e}). Usando fallback en memoria.")
            self._memory_interacciones.append(interaccion_data)
            return interaccion_data

    async def registrar_alerta_sat(self, alerta_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            self._memory_alertas.append(alerta_data)
            return alerta_data

        try:
            req_url = f"{self.rest_url}/historial_alertas_sat"
            data_bytes = json.dumps([alerta_data]).encode('utf-8')
            req = urllib.request.Request(
                req_url,
                data=data_bytes,
                headers=self._headers(prefer="return=representation"),
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                logger.info(f"✅ Alerta SAT registrada en Supabase para {alerta_data.get('estudiante_moodle_id')}")
                return res[0] if res else alerta_data
        except Exception as e:
            logger.warning(f"⚠️ Error al guardar alerta SAT en Supabase REST ({e}). Usando fallback en memoria.")
            self._memory_alertas.append(alerta_data)
            return alerta_data

    async def obtener_historial_estudiante(self, moodle_id: str) -> List[Dict[str, Any]]:
        if self.use_mock:
            return [a for a in self._memory_alertas if a.get("estudiante_moodle_id") == moodle_id]

        try:
            encoded_id = urllib.parse.quote(moodle_id)
            req_url = f"{self.rest_url}/historial_alertas_sat?estudiante_moodle_id=eq.{encoded_id}&order=fecha_evaluacion.desc"
            req = urllib.request.Request(req_url, headers=self._headers(), method="GET")
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                return res
        except Exception as e:
            logger.warning(f"⚠️ Error al consultar historial de {moodle_id} en Supabase ({e}). Usando fallback en memoria.")
            return [a for a in self._memory_alertas if a.get("estudiante_moodle_id") == moodle_id]

db_manager = DatabaseManager()
