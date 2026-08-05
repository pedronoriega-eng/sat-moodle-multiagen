-- =============================================================================
-- MIGRACIÓN DE BASE DE DATOS SUPABASE FREE TIER: SISTEMA SAT-V 2026
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

-- 2. Tabla de Interacciones Moodle (Logs y Metadatos de Actividad)
CREATE TABLE IF NOT EXISTS moodle_interacciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estudiante_moodle_id VARCHAR(50) REFERENCES estudiantes(moodle_id) ON DELETE CASCADE,
    dias_inactividad INT DEFAULT 0,
    total_clics INT DEFAULT 0,
    minutos_navegacion FLOAT DEFAULT 0.0,
    descargas_rafaga INT DEFAULT 0, -- descargas en <60s
    calificaciones JSONB DEFAULT '[]'::jsonb, -- arreglo de notas [3.5, 0.0, None]
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla de Historial de Alertas SAT
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

-- Indices de optimización para Free Tier
CREATE INDEX IF NOT EXISTS idx_moodle_interacciones_estudiante ON moodle_interacciones(estudiante_moodle_id);
CREATE INDEX IF NOT EXISTS idx_historial_alertas_estudiante ON historial_alertas_sat(estudiante_moodle_id);
CREATE INDEX IF NOT EXISTS idx_historial_alertas_fecha ON historial_alertas_sat(fecha_evaluacion DESC);
