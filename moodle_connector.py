import logging
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger("SAT_MoodleConnector")

class MoodleConnector:
    """
    Conector nativo con la API REST de WebServices de Moodle para el Tecnológico del Oriente.
    Curso Objetivo: ID 956 (https://campusvirtual.tecnologicadeloriente.edu.co/course/view.php?id=956)
    """
    def __init__(self):
        self.base_url = settings.MOODLE_URL.rstrip('/')
        self.token = settings.MOODLE_WS_TOKEN
        self.course_id = settings.MOODLE_COURSE_ID
        self.rest_endpoint = f"{self.base_url}/webservice/rest/server.php"

    def _call_ws(self, wsfunction: str, params: Dict[str, Any]) -> Any:
        if not self.token:
            logger.warning("⚠️ MOODLE_WS_TOKEN no configurado. Operando en modo simulación de WebService para Curso 956.")
            return None

        full_params = {
            "wstoken": self.token,
            "moodlewsrestformat": "json",
            "wsfunction": wsfunction,
            **params
        }
        query_string = urllib.parse.urlencode(full_params)
        req_url = f"{self.rest_endpoint}?{query_string}"
        
        try:
            req = urllib.request.Request(req_url, method="GET")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data
        except Exception as e:
            logger.error(f"❌ Error al consultar Moodle WebService ({wsfunction}): {e}")
            return None

    def get_enrolled_students(self, course_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = course_id or self.course_id
        res = self._call_ws("core_enrol_get_enrolled_users", {"courseid": cid})
        if res and isinstance(res, list):
            return res
        return []

    def get_user_grades(self, student_id: int, course_id: Optional[int] = None) -> List[Optional[float]]:
        cid = course_id or self.course_id
        res = self._call_ws("gradereport_user_get_grade_items", {"courseid": cid, "userid": student_id})
        grades = []
        if res and "usergrades" in res:
            for ug in res["usergrades"]:
                for item in ug.get("gradeitems", []):
                    grade_val = item.get("graderaw")
                    if grade_val is not None:
                        grades.append(float(grade_val))
                    else:
                        grades.append(None)
        return grades

moodle_connector = MoodleConnector()
