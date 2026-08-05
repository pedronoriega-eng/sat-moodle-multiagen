-- =============================================================================
-- MIGRACIÓN DE BASE DE DATOS SUPABASE FREE TIER: SISTEMA SAT-V 2026 (v2.0)
-- Incluye Monitoreo de Estudiantes y Tiempos de Interacción Docente
-- Autor: Sistema de Alertas Tempranas Institucional
-- =============================================================================

-- 1. Tabla de Estudiantes
CREATE TABLE IF NOT EXISTS estudiantes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    moodle_id VARCHAR(50) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    nivel_academico VARCHAR(20) CHECK (nivel_academico IN ('pregrado', 'posgrado')) NOT NULL,
    programa VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabla de Interacciones Moodle Estudiantes (Logs y Metadatos)
CREATE TABLE IF NOT EXISTS moodle_interacciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estudiante_moodle_id VARCHAR(50) REFERENCES estudiantes(moodle_id) ON DELETE CASCADE,
    dias_inactividad INT DEFAULT 0,
    total_clics INT DEFAULT 0,
    minutos_navegacion FLOAT DEFAULT 0.0,
    descargas_rafaga INT DEFAULT 0,
    calificaciones JSONB DEFAULT '[]'::jsonb,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla de Historial de Alertas SAT Estudiantes
CREATE TABLE IF NOT EXISTS historial_alertas_sat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estudiante_moodle_id VARCHAR(50) REFERENCES estudiantes(moodle_id) ON DELETE CASCADE,
    nivel_riesgo VARCHAR(20) CHECK (nivel_riesgo IN ('ROJO', 'AMARILLO', 'VERDE')) NOT NULL,
    promedio_evaluado FLOAT,
    regla_aplicada TEXT NOT NULL,
    justificacion TEXT NOT NULL,
    notificacion_enviada BOOLEAN DEFAULT FALSE,
    destinatarios_notificados JSONB DEFAULT '[]'::jsonb,
    evaluado_por_agente VARCHAR(50) DEFAULT 'EvaluatorAgent',
    coordinado_por_agente VARCHAR(50) DEFAULT 'CoordinatorAgent',
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabla de Docentes de Aula / Tutores Virtuales
CREATE TABLE IF NOT EXISTS docentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docente_moodle_id VARCHAR(50) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    curso_moodle_id INT NOT NULL DEFAULT 956,
    nombre_curso VARCHAR(150) NOT NULL DEFAULT 'Curso 956 - Tecnológico del Oriente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Tabla de Interacciones y Tiempos de Respuesta Docente
CREATE TABLE IF NOT EXISTS docente_interacciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docente_moodle_id VARCHAR(50) REFERENCES docentes(docente_moodle_id) ON DELETE CASCADE,
    curso_moodle_id INT NOT NULL DEFAULT 956,
    dias_inactividad_docente INT DEFAULT 0,
    horas_respuesta_foros FLOAT DEFAULT 0.0, -- Tiempo promedio en responder foros (horas)
    horas_calificacion_tareas FLOAT DEFAULT 0.0, -- Tiempo promedio en calificar entregas (horas)
    total_interacciones INT DEFAULT 0,
    estado_interaccion VARCHAR(30) DEFAULT 'OPTIMO', -- OPTIMO, ALERTA_DEMORA, RIESGO_INACTIVIDAD
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices de optimización Free Tier
CREATE INDEX IF NOT EXISTS idx_moodle_interacciones_estudiante ON moodle_interacciones(estudiante_moodle_id);
CREATE INDEX IF NOT EXISTS idx_historial_alertas_estudiante ON historial_alertas_sat(estudiante_moodle_id);
CREATE INDEX IF NOT EXISTS idx_historial_alertas_fecha ON historial_alertas_sat(fecha_evaluacion DESC);
CREATE INDEX IF NOT EXISTS idx_docentes_curso ON docentes(curso_moodle_id);
CREATE INDEX IF NOT EXISTS idx_docente_interacciones_docente ON docente_interacciones(docente_moodle_id);
