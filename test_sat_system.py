import asyncio
import logging
from agents import coordinator_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SAT_TestRunner")

async def run_tests():
    logger.info("======================================================================")
    logger.info("🚀 INICIANDO BATERÍA DE PRUEBAS DE INTEGRACIÓN SAT 2026")
    logger.info("======================================================================")

    # Caso 1: Posgrado con Promedio 3.2 (Debe ser ROJO según asimetría de posgrado >= 3.5)
    estudiante_1 = {
        "moodle_id": "EST-POS-001",
        "nombre_completo": "Dra. Laura Gómez",
        "email": "laura.gomez@institucion.edu.co",
        "nivel_academico": "posgrado",
        "programa": "Maestría en Educación Virtual",
        "dias_inactividad": 2,
        "total_clics": 80,
        "minutos_navegacion": 60.0,
        "descargas_rafaga": 0,
        "calificaciones": [3.2, 3.2, None]  # Promedio: 3.2
    }

    # Caso 2: Pregrado con Promedio 3.8 e Inactividad 6 días (Debe ser AMARILLO por Veto Aprobatorio con Inactividad)
    estudiante_2 = {
        "moodle_id": "EST-PRE-002",
        "nombre_completo": "Juan David Martínez",
        "email": "juan.martinez@institucion.edu.co",
        "nivel_academico": "pregrado",
        "programa": "Ingeniería de Software Virtual",
        "dias_inactividad": 6,
        "total_clics": 150,
        "minutos_navegacion": 120.0,
        "descargas_rafaga": 0,
        "calificaciones": [4.0, 3.6, 0.0, 4.0, None]  # 4.0 + 3.6 + 0.0 + 4.0 = 11.6 / 4 = 2.9? Espera: ceros incluidos
        # Queremos promedio 3.8: [4.0, 4.0, 3.4, None] -> 11.4 / 3 = 3.8
    }
    estudiante_2["calificaciones"] = [4.0, 4.0, 3.4, None]

    # Caso 3: Pregrado con Promedio 4.5 e Inactividad 1 día (Debe ser VERDE)
    estudiante_3 = {
        "moodle_id": "EST-PRE-003",
        "nombre_completo": "María Camila Torres",
        "email": "maria.torres@institucion.edu.co",
        "nivel_academico": "pregrado",
        "programa": "Licenciatura en Pedagogía Virtual",
        "dias_inactividad": 1,
        "total_clics": 210,
        "minutos_navegacion": 180.0,
        "descargas_rafaga": 0,
        "calificaciones": [4.5, 5.0, 4.0, None]  # Promedio: 4.5
    }

    test_cases = [
        ("Caso 1: Posgrado < 3.5 (Esperado ROJO)", estudiante_1, "ROJO"),
        ("Caso 2: Pregrado Aprobatorio con Inactividad > 5d (Esperado AMARILLO)", estudiante_2, "AMARILLO"),
        ("Caso 3: Pregrado Óptimo (Esperado VERDE)", estudiante_3, "VERDE")
    ]

    passed_count = 0

    for title, payload, expected_risk in test_cases:
        logger.info(f"\n--- Ejecutando: {title} ---")
        result = await coordinator_agent.execute_sat_pipeline(payload)
        
        obtained_risk = result["nivel_riesgo"]
        promedio = result["promedio_evaluado"]
        justificacion = result["justificacion"]

        logger.info(f"-> Moodle ID: {result['moodle_id']}")
        logger.info(f"-> Promedio Evaluado: {promedio}")
        logger.info(f"-> Riesgo Obtenido: {obtained_risk} | Esperado: {expected_risk}")
        logger.info(f"-> Regla Aplicada: {result['regla_aplicada']}")
        logger.info(f"-> Justificación: {justificacion}")

        if obtained_risk == expected_risk:
            logger.info(f"✅ PASÓ: {title}")
            passed_count += 1
        else:
            logger.error(f"❌ FALLÓ: {title}. Obtenido {obtained_risk} vs Esperado {expected_risk}")

    logger.info("======================================================================")
    logger.info(f"📊 RESUMEN PRUEBAS: {passed_count}/{len(test_cases)} CASOS EXITOSOS")
    logger.info("======================================================================")
    
    return passed_count == len(test_cases)

if __name__ == "__main__":
    asyncio.run(run_tests())
