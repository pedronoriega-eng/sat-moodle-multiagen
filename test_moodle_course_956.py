import asyncio
import logging
from agents import coordinator_agent
from moodle_connector import moodle_connector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SAT_Course956TestRunner")

async def run_moodle_course_956_test():
    logger.info("======================================================================")
    logger.info("🎓 SIMULACIÓN Y EVALUACIÓN MULTIAGENTE DE ALERTAS TEMPRANAS SAT 2026")
    logger.info("🏫 INSTITUCIÓN: Tecnológico del Oriente - Campus Virtual")
    logger.info("📚 AULA VIRTUAL OBJETIVO: Curso ID 956")
    logger.info("🌐 URL: https://campusvirtual.tecnologicadeloriente.edu.co/course/view.php?id=956")
    logger.info("======================================================================")

    # Simulación de cohorte de 5 estudiantes matriculados en el Curso 956
    estudiantes_curso_956 = [
        {
            "moodle_id": "EST-M956-101",
            "nombre_completo": "Andrés Felipe Mendoza",
            "email": "andres.mendoza@tecnologicadeloriente.edu.co",
            "nivel_academico": "pregrado",
            "programa": "Curso 956 - Licenciatura Virtual",
            "dias_inactividad": 1,
            "total_clics": 240,
            "minutos_navegacion": 150.0,
            "descargas_rafaga": 0,
            "calificaciones": [4.2, 4.5, 0.0, None]  # Promedio: 2.9 (Cero incluido) -> Promedio evaluado: (4.2+4.5+0.0)/3 = 2.9 (Pregrado < 3.0 = ROJO)
        },
        {
            "moodle_id": "EST-M956-102",
            "nombre_completo": "Camila Andrea Rivera",
            "email": "camila.rivera@tecnologicadeloriente.edu.co",
            "nivel_academico": "posgrado",
            "programa": "Curso 956 - Especialización Virtual",
            "dias_inactividad": 2,
            "total_clics": 180,
            "minutos_navegacion": 90.0,
            "descargas_rafaga": 0,
            "calificaciones": [3.4, 3.4, None]  # Promedio: 3.4 (Posgrado < 3.5 = ROJO)
        },
        {
            "moodle_id": "EST-M956-103",
            "nombre_completo": "Mateo Sebastián Silva",
            "email": "mateo.silva@tecnologicadeloriente.edu.co",
            "nivel_academico": "pregrado",
            "programa": "Curso 956 - Ingeniería Virtual",
            "dias_inactividad": 6,
            "total_clics": 95,
            "minutos_navegacion": 40.0,
            "descargas_rafaga": 0,
            "calificaciones": [4.0, 4.0, 3.6, None]  # Promedio: 3.86 (Veto Aprobatorio + Inactividad 6d = AMARILLO)
        },
        {
            "moodle_id": "EST-M956-104",
            "nombre_completo": "Valentina Ortiz Reyes",
            "email": "valentina.ortiz@tecnologicadeloriente.edu.co",
            "nivel_academico": "pregrado",
            "programa": "Curso 956 - Administración Virtual",
            "dias_inactividad": 4,
            "total_clics": 60,
            "minutos_navegacion": 12.0,
            "descargas_rafaga": 0,
            "calificaciones": [3.2, 3.0, None]  # Promedio: 3.1 (Pregrado entre 3.0 y 3.4 = AMARILLO)
        },
        {
            "moodle_id": "EST-M956-105",
            "nombre_completo": "Santiago Hernán López",
            "email": "santiago.lopez@tecnologicadeloriente.edu.co",
            "nivel_academico": "pregrado",
            "programa": "Curso 956 - Diseño Digital Virtual",
            "dias_inactividad": 1,
            "total_clics": 310,
            "minutos_navegacion": 210.0,
            "descargas_rafaga": 0,
            "calificaciones": [4.8, 5.0, 4.5, None]  # Promedio: 4.77 (Promedio >= 3.0 e Inactividad <= 3d = VERDE)
        }
    ]

    for est in estudiantes_curso_956:
        logger.info(f"\n⚡ Procesando con el enjambre FIPA-ACL a: {est['nombre_completo']} ({est['moodle_id']})")
        res = await coordinator_agent.execute_sat_pipeline(est)
        
        logger.info(f"   📊 Promedio: {res['promedio_evaluado']} | Riesgo: {res['nivel_riesgo']}")
        logger.info(f"   📜 Regla: {res['regla_aplicada']}")
        logger.info(f"   💬 Diagnóstico: {res['justificacion']}")

    logger.info("\n======================================================================")
    logger.info("✅ EVALUACIÓN DEL CURSO 956 COMPLETADA Y REGISTRADA EN SUPABASE CLOUD")
    logger.info("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_moodle_course_956_test())
