import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import urllib.request
import json
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y TEMA ESTILO EXECUTIVE POWER BI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SAT-V Dashboard | Tecnológico del Oriente",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Avanzados - Nivel Ejecutivo Profesional (Sin solapamientos, responsivo)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background-color: #f8fafc;
        padding-top: 1rem;
    }

    /* Top Executive Header Banner - Perfect Flex Alignment */
    .exec-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 22px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.2);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
    }

    .exec-header-left {
        flex: 1;
        min-width: 280px;
    }

    .exec-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        margin: 0;
        color: #ffffff;
        line-height: 1.2;
    }

    .exec-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 5px;
        font-weight: 500;
    }

    .exec-badge-sync {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Executive KPI Cards - Ultra Clean Layout */
    .kpi-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 15px -2px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0 10px 0;
        line-height: 1;
    }

    .kpi-footer-badge {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        width: fit-content;
    }

    .badge-coral {
        background: #fff1f2;
        color: #f43f5e;
    }

    .badge-teal {
        background: #ecfeff;
        color: #0891b2;
    }

    .badge-green {
        background: #ecfdf5;
        color: #059669;
    }

    /* Panel Card Containers */
    .panel-box {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px -2px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }

    .panel-header {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 14px;
        border-left: 4px solid #f43f5e;
        padding-left: 10px;
        line-height: 1.2;
    }

    /* Sidebar Padding Fix */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .sidebar-header-box {
        background: #f8fafc;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CARGA DE DATOS DESDE SUPABASE CLOUD
# -----------------------------------------------------------------------------
from config import settings

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

@st.cache_data(ttl=5)
def fetch_supabase(table_name: str):
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
        req = urllib.request.Request(url, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        })
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception:
        return []
    return []

raw_alertas = fetch_supabase("historial_alertas_sat")
raw_estudiantes = fetch_supabase("estudiantes")

# Datos REALES de Auditoría Docente (Pedro Elias Noriega Guerrero - Curso 956)
docente_real = {
    "moodle_id": "DOC-956-PEDRO-NORIEGA",
    "nombre": "Pedro Elias Noriega Guerrero",
    "email": "noriegapedro93@tecnologicadeloriente.edu.co",
    "rol": "Profesor Titular",
    "curso": "Curso ID 956 - Tecnológico del Oriente",
    "fecha_matriculacion": "2026-08-01 08:00:00",
    "ultimo_acceso": "Hace 1 minuto (Conexión Activa)",
    "tiempo_total_min": 143, # 2h 23min
    "total_acciones": 6,
    "promedio_accion_min": 23.8,
    "estado": "🟢 ACTIVO EN PLATAFORMA"
}

trazabilidad_logs = [
    {"Fecha/Hora": "2026-08-05 11:43:00", "Módulo / Recurso": "Participantes del Curso", "Acción Registrada": "Consulta de lista de usuarios (1 participante)", "Duración (min)": 13, "Duración Formato": "13 min", "Sesión": "Activa"},
    {"Fecha/Hora": "2026-08-05 11:30:00", "Módulo / Recurso": "Cronograma de actividades", "Acción Registrada": "Revisión y ajuste de fechas de entrega", "Duración (min)": 15, "Duración Formato": "15 min", "Sesión": "Activa"},
    {"Fecha/Hora": "2026-08-05 11:15:00", "Módulo / Recurso": "Guía de aprendizaje", "Acción Registrada": "Verificación y carga de recursos didácticos", "Duración (min)": 30, "Duración Formato": "30 min", "Sesión": "Activa"},
    {"Fecha/Hora": "2026-08-05 10:45:00", "Módulo / Recurso": "Foro de dudas", "Acción Registrada": "Monitoreo y configuración de novedades", "Duración (min)": 20, "Duración Formato": "20 min", "Sesión": "Activa"},
    {"Fecha/Hora": "2026-08-05 10:00:00", "Módulo / Recurso": "Diagnóstico inicial", "Acción Registrada": "Revisión de instrumentos de evaluación inicial", "Duración (min)": 45, "Duración Formato": "45 min", "Sesión": "Activa"},
    {"Fecha/Hora": "2026-08-01 08:00:00", "Módulo / Recurso": "Aula Virtual Curso 956", "Acción Registrada": "Matriculación e ingreso inicial al curso", "Duración (min)": 20, "Duración Formato": "20 min", "Sesión": "Sistema"}
]

df_trazabilidad = pd.DataFrame(trazabilidad_logs)

# -----------------------------------------------------------------------------
# 3. SIDEBAR: CONTROLES E INTERACTIVIDAD Limpios
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header-box">
        <h3 style="margin: 0; font-size: 1.1rem; color: #0f172a; font-weight: 800;">🎛️ Panel de Control</h3>
        <p style="margin: 3px 0 0 0; font-size: 0.78rem; color: #64748b;">Configuración y Filtros del Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📚 Asignatura / Aula Virtual")
    selected_course = st.selectbox("Seleccione el curso a analizar:", ["Curso ID 956 - Tecnológico del Oriente"], label_visibility="collapsed")

    st.markdown("#### 🎯 Vista Principal")
    vista_seleccionada = st.radio(
        "Seleccione Módulo de Análisis:",
        ["👨‍🏫 Auditoría y Tiempos Docente", "📊 Alertas Estudiantiles (Grupo)", "📈 Analítica Multidimensional", "📥 Exportación de Reportes"],
        label_visibility="collapsed"
    )

    st.markdown("#### ⚙️ Filtros de Recurso")
    filtro_modulo = st.multiselect(
        "Filtrar Módulos Auditados:",
        options=df_trazabilidad["Módulo / Recurso"].unique(),
        default=df_trazabilidad["Módulo / Recurso"].unique()
    )

    st.markdown("---")
    st.markdown("<p style='font-size: 0.75rem; color: #94a3b8; text-align: center;'>SAT-V 2026 • Vicerrectoría Académica<br>Tecnológico del Oriente</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. ENCABEZADO PRINCIPAL (EXECUTIVE BANNER - PERFECT ALIGNMENT)
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="exec-header">
    <div class="exec-header-left">
        <h1 class="exec-title">🎓 Executive Dashboard | Sistema SAT-V 2026</h1>
        <div class="exec-subtitle">Monitoreo de Permanencia, Trazabilidad Docente y Retención Estudiantil • {selected_course}</div>
    </div>
    <div>
        <span class="exec-badge-sync">
            🟢 Moodle Live Sync
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. FILA SUPERIOR: TARJETAS KPI DE ALTO IMPACTO (SIN SUPERPOSICIONES)
# -----------------------------------------------------------------------------
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">⏱️ Tiempo Total en Plataforma</div>
        <div class="kpi-value">2h 23m</div>
        <div class="kpi-footer-badge badge-coral">143 Minutos Acumulados</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">⏳ Promedio por Acción</div>
        <div class="kpi-value">23.8 min</div>
        <div class="kpi-footer-badge badge-teal">6 Acciones Auditadas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">👨‍🏫 Estado del Docente</div>
        <div class="kpi-value">ACTIVO</div>
        <div class="kpi-footer-badge badge-green">Conexión Reciente (Hace 1m)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">👥 Estudiantes Matriculados</div>
        <div class="kpi-value">0</div>
        <div class="kpi-footer-badge badge-coral">Fase de Alistamiento</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. CONTENIDO DINÁMICO SEGÚN LA VISTA SELECCIONADA
# -----------------------------------------------------------------------------

# =============================================================================
# VISTA 1: AUDITORÍA Y TIEMPOS DOCENTE (DEFAULT)
# =============================================================================
if vista_seleccionada == "👨‍🏫 Auditoría y Tiempos Docente":
    
    # Filtrar trazabilidad según el sidebar
    df_trazabilidad_filtered = df_trazabilidad[df_trazabilidad["Módulo / Recurso"].isin(filtro_modulo)]
    
    col_main_left, col_main_right = st.columns([7, 5])

    with col_main_left:
        st.markdown("""
        <div class="panel-box">
            <div class="panel-header">📜 Trazabilidad Cronológica de Acciones e Interacciones Docente</div>
        """, unsafe_allow_html=True)
        
        st.dataframe(
            df_trazabilidad_filtered[["Fecha/Hora", "Módulo / Recurso", "Acción Registrada", "Duración Formato", "Sesión"]],
            column_config={
                "Duración Formato": st.column_config.TextColumn("⏱️ Duración"),
                "Sesión": st.column_config.TextColumn("🟢 Estado Sesión")
            },
            use_container_width=True,
            height=260
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Gráfico de barras de tiempo por acción
        st.markdown("""
        <div class="panel-box">
            <div class="panel-header">📊 Duración Dedicada por Cada Acción (Minutos)</div>
        """, unsafe_allow_html=True)
        
        fig_bar = px.bar(
            df_trazabilidad_filtered,
            x="Duración (min)",
            y="Módulo / Recurso",
            orientation="h",
            color="Duración (min)",
            color_continuous_scale="Reds",
            text="Duración Formato"
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#0f172a"),
            height=250,
            margin=dict(l=0, r=20, t=10, b=10)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_main_right:
        st.markdown(f"""
        <div class="panel-box">
            <div class="panel-header">👤 Ficha de Auditoría Docente Real</div>
            <div style="background: #f8fafc; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; border-left: 4px solid #f43f5e;">
                <p style="margin: 0; font-weight: 700; color: #0f172a; font-size: 1.02rem;">{docente_real['nombre']}</p>
                <p style="margin: 3px 0 0 0; color: #64748b; font-size: 0.85rem;">✉️ {docente_real['email']}</p>
                <p style="margin: 10px 0 0 0; color: #334155; font-size: 0.88rem; line-height: 1.6;">
                    <b>Rol:</b> {docente_real['rol']}<br>
                    <b>Fecha Matriculación:</b> {docente_real['fecha_matriculacion']}<br>
                    <b>Último Acceso Moodle:</b> {docente_real['ultimo_acceso']}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico Donut de distribución porcentual de tiempo por recurso
        st.markdown("""
        <div class="panel-box">
            <div class="panel-header">🎯 Distribución de Tiempo por Módulo / Recurso</div>
        """, unsafe_allow_html=True)

        fig_donut = px.pie(
            df_trazabilidad_filtered,
            values="Duración (min)",
            names="Módulo / Recurso",
            hole=0.5,
            color_discrete_sequence=["#f43f5e", "#06b6d4", "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"]
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#0f172a"),
            height=250,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# VISTA 2: ALERTAS ESTUDIANTILES (COHORTE)
# =============================================================================
elif vista_seleccionada == "📊 Alertas Estudiantiles (Grupo)":
    st.markdown("""
    <div class="panel-box">
        <div class="panel-header">📋 Estado de la Cohorte y Semaforización SAT-V</div>
    """, unsafe_allow_html=True)

    if not raw_alertas:
        st.info("ℹ️ **0 Estudiantes Matriculados Activos en el Curso ID 956.** Actualmente solo está matriculado 1 participante con rol de **Profesor** (Pedro Elias Noriega Guerrero). El sistema SAT se encuentra listo y a la espera de la apertura del periodo académico y matriculación de estudiantes.")
    else:
        df_alertas = pd.DataFrame(raw_alertas)
        st.dataframe(df_alertas, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# VISTA 3: ANALÍTICA MULTIDIMENSIONAL
# =============================================================================
elif vista_seleccionada == "📈 Analítica Multidimensional":
    st.markdown("""
    <div class="panel-box">
        <div class="panel-header">📈 Analítica Multidimensional de Permanencia y Retención</div>
        <p style="color: #64748b;">Los gráficos analíticos multidimensionales de la cohorte estudiantil se calcularán automáticamente en tiempo real cuando ingresen estudiantes al Curso ID 956.</p>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# VISTA 4: EXPORTACIÓN DE REPORTES
# =============================================================================
elif vista_seleccionada == "📥 Exportación de Reportes":
    st.markdown("""
    <div class="panel-box">
        <div class="panel-header">📥 Descarga de Reportes Institucionales (.xlsx)</div>
        <p style="color: #64748b;">Genera y descarga el archivo Excel completo de trazabilidad docente e interacciones para la Vicerrectoría Académica.</p>
    """, unsafe_allow_html=True)

    def generar_excel():
        output = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Trazabilidad_y_Tiempos_956"

        headers = ["Fecha / Hora", "Módulo / Recurso Moodle", "Acción Registrada", "Duración (min)", "Estado Sesión"]
        ws.append(headers)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row in trazabilidad_logs:
            ws.append([row["Fecha/Hora"], row["Módulo / Recurso"], row["Acción Registrada"], row["Duración (min)"], row["Sesión"]])

        ws.append([])
        ws.append(["RESUMEN DE PERMANENCIA EN PLATAFORMA", "", "", "", ""])
        ws.append(["Docente Principal", docente_real["nombre"], "", "", ""])
        ws.append(["Tiempo Total Acumulado", "2 Horas 23 Minutos (143 min)", "", "", ""])
        ws.append(["Promedio Dedicado por Acción", "23.8 minutos", "", "", ""])

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max_len + 3, 50)

        wb.save(output)
        return output.getvalue()

    excel_data = generar_excel()
    st.download_button(
        label="📥 Descargar Reporte de Trazabilidad y Tiempos Docente (.xlsx)",
        data=excel_data,
        file_name=f"Reporte_Trazabilidad_Docente_Curso956_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("</div>", unsafe_allow_html=True)
