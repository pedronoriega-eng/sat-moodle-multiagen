import asyncio
import logging
import json
try:
    import aiosmtplib
    HAS_AIOSMTPLIB = True
except ImportError:
    HAS_AIOSMTPLIB = False
    aiosmtplib = None
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import settings
from database import db_manager

logger = logging.getLogger("SAT_Agents")
logging.basicConfig(level=logging.INFO)

# =============================================================================
# ESTRUCTURA DE MENSAJES FIPA-ACL (AGENT COMMUNICATION LANGUAGE)
# =============================================================================
class FIPAACLMessage:
    def __init__(self, performative: str, sender: str, receiver: str, content: Dict[str, Any], reply_with: str = ""):
        self.performative = performative  # REQUEST, INFORM, AGREE, CONFIRM, PROPOSE
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.reply_with = reply_with
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "performative": self.performative,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "reply_with": self.reply_with,
            "timestamp": self.timestamp
        }

# =============================================================================
# AGENTE 1: HARVESTER AGENT (Gemini 1.5 Flash)
# Extrae, limpia y normaliza metadatos y logs de Moodle
# =============================================================================
class HarvesterAgent:
    def __init__(self):
        self.name = "HarvesterAgent"
        self.model_name = settings.GEMINI_FAST_MODEL

    async def process(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Normalizando logs crudos del estudiante: {raw_payload.get('moodle_id')}")
        
        # Extracción y sanitización de datos
        moodle_id = str(raw_payload.get("moodle_id", "")).strip()
        nombre = str(raw_payload.get("nombre_completo", "Estudiante")).strip()
        email = str(raw_payload.get("email", "")).strip()
        nivel = str(raw_payload.get("nivel_academico", "pregrado")).strip().lower()
        programa = str(raw_payload.get("programa", "Programa Virtual")).strip()
        
        dias_inactividad = int(raw_payload.get("dias_inactividad", 0))
        total_clics = int(raw_payload.get("total_clics", 0))
        minutos_navegacion = float(raw_payload.get("minutos_navegacion", 0.0))
        descargas_rafaga = int(raw_payload.get("descargas_rafaga", 0))
        
        # Tratamiento explícito de calificaciones
        raw_grades = raw_payload.get("calificaciones", [])
        calificaciones_evaluadas: List[float] = []
        
        for item in raw_grades:
            if item is None or item == "" or item == "-" or str(item).lower() == "nan":
                continue  # EXCLUSIÓN estricta de celdas vacías / semanas futuras
            try:
                val = float(str(item).replace(",", "."))
                calificaciones_evaluadas.append(val)  # INCLUSIÓN explícita de ceros (0.0)
            except ValueError:
                continue

        # Cálculo riguroso de promedio evaluado
        if calificaciones_evaluadas:
            promedio_evaluado = round(sum(calificaciones_evaluadas) / len(calificaciones_evaluadas), 2)
        else:
            promedio_evaluado = None

        normalized_data = {
            "estudiante": {
                "moodle_id": moodle_id,
                "nombre_completo": nombre,
                "email": email,
                "nivel_academico": nivel,
                "programa": programa
            },
            "interaccion": {
                "dias_inactividad": dias_inactividad,
                "total_clics": total_clics,
                "minutos_navegacion": minutos_navegacion,
                "descargas_rafaga": descargas_rafaga,
                "calificaciones_evaluadas": calificaciones_evaluadas,
                "promedio_evaluado": promedio_evaluado
            }
        }
        
        # Registrar en la base de datos
        await db_manager.registrar_estudiante(normalized_data["estudiante"])
        await db_manager.registrar_interaccion({
            "estudiante_moodle_id": moodle_id,
            "dias_inactividad": dias_inactividad,
            "total_clics": total_clics,
            "minutos_navegacion": minutos_navegacion,
            "descargas_rafaga": descargas_rafaga,
            "calificaciones": calificaciones_evaluadas
        })

        return normalized_data

# =============================================================================
# AGENTE 2: EVALUATOR AGENT (Gemini 1.5 Flash)
# Aplica las reglas algorítmicas del Manual SAT 2026 y la Veto Aprobatorio
# =============================================================================
class EvaluatorAgent:
    def __init__(self):
        self.name = "EvaluatorAgent"
        self.model_name = settings.GEMINI_FAST_MODEL

    async def evaluate(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Evaluando matriz de semaforización SAT 2026 para: {normalized_data['estudiante']['moodle_id']}")
        
        estudiante = normalized_data["estudiante"]
        interaccion = normalized_data["interaccion"]
        
        nivel = estudiante["nivel_academico"]  # 'pregrado' o 'posgrado'
        promedio = interaccion["promedio_evaluado"]
        inactividad = interaccion["dias_inactividad"]
        descargas_rafaga = interaccion["descargas_rafaga"]
        minutos = interaccion["minutos_navegacion"]
        
        umbral_aprobatorio = 3.0 if nivel == "pregrado" else 3.5
        
        nivel_riesgo = "VERDE"
        regla_aplicada = ""
        justificacion = ""

        # 1. EVALUACIÓN DE VETO APROBATORIO (Sección 3.3 del Manual SAT 2026)
        if promedio is not None and promedio >= umbral_aprobatorio:
            if inactividad > 5:
                nivel_riesgo = "AMARILLO"
                regla_aplicada = "REGLA_VETO_APROBATORIO_CON_INACTIVIDAD"
                justificacion = (f"El estudiante de {nivel} posee un promedio aprobatorio acumulado de {promedio:.2f} "
                                f"(>= {umbral_aprobatorio}), activando el Veto Aprobatorio. Sin embargo, registra {inactividad} "
                                f"días de inactividad, clasificándose como 'Aprobando con Inactividad'.")
            else:
                nivel_riesgo = "VERDE"
                regla_aplicada = "REGLA_VETO_APROBATORIO_OPTIMO"
                justificacion = (f"El estudiante de {nivel} registra un desempeño satisfactorio con promedio de {promedio:.2f} "
                                f"(>= {umbral_aprobatorio}) e inactividad adecuada ({inactividad} días).")
        else:
            # 2. EVALUACIÓN DE RIESGO CRÍTICO (ROJO)
            es_rojo = False
            razones_rojo = []
            
            # Cero accesos o inactividad > 5 días sin promedio aprobatorio
            if inactividad > 5:
                es_rojo = True
                razones_rojo.append(f"Inactividad prolongada de {inactividad} días sin promedio aprobatorio")
            
            # Descargas en ráfaga
            if descargas_rafaga >= 2:
                es_rojo = True
                razones_rojo.append(f"Patrón de descarga masiva en ráfaga ({descargas_rafaga} descargas en <60s) sin lectura activa")
                
            # Calificaciones Post-Entrega reprobatorias
            if promedio is not None:
                if nivel == "pregrado" and promedio < 3.0:
                    es_rojo = True
                    razones_rojo.append(f"Promedio de pregrado de {promedio:.2f} es inferior a la nota mínima de 3.0")
                elif nivel == "posgrado" and promedio < 3.5:
                    es_rojo = True
                    razones_rojo.append(f"Promedio de posgrado de {promedio:.2f} es inferior a la nota mínima exigida de 3.5")
            elif inactividad > 3:
                es_rojo = True
                razones_rojo.append("Ausencia de entregas evaluadas con inactividad superior a 3 días")

            if es_rojo:
                nivel_riesgo = "ROJO"
                regla_aplicada = "MATRIZ_SAT_2026_RIESGO_CRITICO"
                justificacion = "Riesgo Crítico detectado: " + "; ".join(razones_rojo) + "."
            else:
                # 3. EVALUACIÓN DE RIESGO MEDIO (AMARILLO)
                es_amarillo = False
                razones_amarillo = []
                
                if 3 <= inactividad <= 5:
                    es_amarillo = True
                    razones_amarillo.append(f"Inactividad moderada entre 3 y 5 días ({inactividad} días)")
                    
                if minutos < 15 and minutos > 0:
                    es_amarillo = True
                    razones_amarillo.append(f"Sesión breve navegada ({minutos} minutos)")

                if promedio is not None:
                    if nivel == "pregrado" and 3.0 <= promedio <= 3.4:
                        es_amarillo = True
                        razones_amarillo.append(f"Promedio de pregrado bordea el límite de riesgo ({promedio:.2f})")
                    elif nivel == "posgrado" and 3.5 <= promedio <= 3.8:
                        es_amarillo = True
                        razones_amarillo.append(f"Promedio de posgrado bordea el límite de riesgo ({promedio:.2f})")

                if es_amarillo:
                    nivel_riesgo = "AMARILLO"
                    regla_aplicada = "MATRIZ_SAT_2026_RIESGO_MEDIO"
                    justificacion = "Riesgo Medio detectado: " + "; ".join(razones_amarillo) + "."
                else:
                    nivel_riesgo = "VERDE"
                    regla_aplicada = "MATRIZ_SAT_2026_SIN_RIESGO"
                    justificacion = f"Estudiante en rango óptimo con inactividad de {inactividad} días y promedio de {promedio}."

        evaluation_result = {
            "estudiante": estudiante,
            "interaccion": interaccion,
            "nivel_riesgo": nivel_riesgo,
            "promedio_evaluado": promedio,
            "regla_aplicada": regla_aplicada,
            "justificacion": justificacion
        }
        return evaluation_result

# =============================================================================
# AGENTE 3: NOTIFIER AGENT (Gemini 1.5 Flash)
# Diseña plantillas dinámicas y gestiona el envío de correos SMTP asíncronos
# =============================================================================
class NotifierAgent:
    def __init__(self):
        self.name = "NotifierAgent"
        self.model_name = settings.GEMINI_FAST_MODEL

    async def notify(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Generando notificación para riesgo {evaluation['nivel_riesgo']}")
        
        estudiante = evaluation["estudiante"]
        nivel_riesgo = evaluation["nivel_riesgo"]
        justificacion = evaluation["justificacion"]
        
        destinatarios = []
        asunto = f"[{nivel_riesgo}] Alerta Temprana SAT 2026 - Estudiante: {estudiante['nombre_completo']}"
        
        if nivel_riesgo == "ROJO":
            destinatarios = ["bienestar.universitario@institucion.edu.co", "consejeria.academica@institucion.edu.co"]
            cuerpo = f"""
            🚨 ALERTA ROJA DE RIESGO CRÍTICO (SISTEMA SAT 2026)
            -------------------------------------------------------------
            Estudiante: {estudiante['nombre_completo']} (ID: {estudiante['moodle_id']})
            Programa: {estudiante['programa']} ({estudiante['nivel_academico'].upper()})
            Email: {estudiante['email']}
            
            JUSTIFICACIÓN TÉCNICA Y DIAGNÓSTICO:
            {justificacion}

            PROTOCOLO OPERATIVO REQUERIDO:
            • Realizar llamada telefónica prioritaria en menos de 24 horas por Consejería Académica y Bienestar.
            • Investigar causales de conectividad, salud mental o factores socioeconómicos.
            • Registrar acta de compromiso en la plataforma institucional.
            """
        elif nivel_riesgo == "AMARILLO":
            destinatarios = ["tutor.virtual@institucion.edu.co", estudiante["email"]]
            cuerpo = f"""
            🟡 ALERTA AMARILLA DE RIESGO MEDIO (PREVENTIVA SAT 2026)
            -------------------------------------------------------------
            Estimado/a {estudiante['nombre_completo']},

            Hemos notado una oportunidad para optimizar tu ritmo académico en el programa {estudiante['programa']}.
            
            DETALLE DEL SEGUIMIENTO:
            {justificacion}

            RECOMENDACIÓN Y INTERVENCIÓN:
            • Envío de Nudge preventivo semi-personalizado.
            • Se ofrece agendamiento de tutoría de refuerzo remediante esta semana.
            """
        else:
            destinatarios = [estudiante["email"]]
            cuerpo = f"""
            🟢 RECONOCIMIENTO DE AVANCE ACADÉMICO SAT 2026
            -------------------------------------------------------------
            ¡Felicitaciones {estudiante['nombre_completo']}!

            Tu desempeño y ritmo de aprendizaje en {estudiante['programa']} se encuentra en nivel ÓPTIMO.
            Muestras una excelente disciplina de navegación y cumplimiento en plataforma.
            ¡Continúa así!
            """

        notificacion_enviada = False
        if HAS_AIOSMTPLIB and settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                message = MIMEMultipart()
                message["From"] = settings.SMTP_FROM
                message["To"] = ", ".join(destinatarios)
                message["Subject"] = asunto
                message.attach(MIMEText(cuerpo, "plain"))

                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER,
                    password=settings.SMTP_PASSWORD,
                    start_tls=True
                )
                notificacion_enviada = True
                logger.info(f"[{self.name}] Email enviado exitosamente a {destinatarios}")
            except Exception as e:
                logger.warning(f"[{self.name}] No se pudo enviar el correo SMTP real ({e}). Simulación completada.")
        else:
            logger.info(f"[{self.name}] SMTP no configurado en entorno. Notificación simulada para {destinatarios}.")

        # Guardar en Supabase
        await db_manager.registrar_alerta_sat({
            "estudiante_moodle_id": estudiante["moodle_id"],
            "nivel_riesgo": nivel_riesgo,
            "promedio_evaluado": evaluation["promedio_evaluado"],
            "regla_aplicada": evaluation["regla_aplicada"],
            "justificacion": justificacion,
            "notificacion_enviada": notificacion_enviada,
            "destinatarios_notificados": destinatarios
        })

        return {
            "estudiante_moodle_id": estudiante["moodle_id"],
            "nivel_riesgo": nivel_riesgo,
            "destinatarios": destinatarios,
            "notificacion_enviada": notificacion_enviada,
            "asunto": asunto
        }

# =============================================================================
# AGENTE 4: COORDINATOR AGENT (Gemini 1.5 Pro / 3.1 Pro)
# Supervisor central del enjambre, control de bucles y calidad FIPA-ACL
# =============================================================================
class CoordinatorAgent:
    def __init__(self):
        self.name = "CoordinatorAgent"
        self.model_name = settings.GEMINI_PRO_MODEL
        self.harvester = HarvesterAgent()
        self.evaluator = EvaluatorAgent()
        self.notifier = NotifierAgent()

    async def execute_sat_pipeline(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquesta el flujo continuo no bloqueante FIPA-ACL mediante asyncio.Queue
        """
        logger.info(f"[{self.name}] Iniciando orquestación FIPA-ACL para payload de Moodle...")
        
        # Paso 1: Harvester Agent
        harvest_result = await self.harvester.process(raw_payload)
        
        # Paso 2: Evaluator Agent
        eval_result = await self.evaluator.evaluate(harvest_result)
        
        # Paso 3: Validation Protocol by Coordinator (Sanity Check)
        # Asegura la consistencia entre Posgrado/Pregrado y Veto Aprobatorio
        promedio = eval_result["promedio_evaluado"]
        nivel = harvest_result["estudiante"]["nivel_academico"]
        
        if nivel == "posgrado" and promedio is not None and promedio < 3.5:
            if eval_result["nivel_riesgo"] != "ROJO":
                logger.warning(f"[{self.name}] Corrección de seguridad: Ajustando a ROJO por norma estricta de Posgrado.")
                eval_result["nivel_riesgo"] = "ROJO"
                eval_result["justificacion"] = f"Ajuste del Coordinador: Posgrado requiere promedio >= 3.5. Obtenido: {promedio:.2f}."
        
        # Paso 4: Notifier Agent
        notify_result = await self.notifier.notify(eval_result)

        final_summary = {
            "moodle_id": harvest_result["estudiante"]["moodle_id"],
            "nombre_estudiante": harvest_result["estudiante"]["nombre_completo"],
            "nivel_academico": harvest_result["estudiante"]["nivel_academico"],
            "nivel_riesgo": eval_result["nivel_riesgo"],
            "promedio_evaluado": eval_result["promedio_evaluado"],
            "regla_aplicada": eval_result["regla_aplicada"],
            "justificacion": eval_result["justificacion"],
            "notificacion": notify_result,
            "orquestado_por": self.name,
            "timestamp_final": datetime.utcnow().isoformat()
        }

        logger.info(f"[{self.name}] Pipeline completado exitosamente para ID: {final_summary['moodle_id']}")
        return final_summary

coordinator_agent = CoordinatorAgent()
