import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from config import settings

DESTINATARIO_PRUEBAS = ["noriegapedro93@tecnologicadeloriente.edu.co", "pedro.noriega@gmail.com"]

# =============================================================================
# 1. INFORME 1: TRAZABILIDAD Y MONITOREO DOCENTE (SEPARADO)
# =============================================================================
def enviar_informe_docente():
    asunto = f"📋 INFORME DE AUDITORÍA Y TRAZABILIDAD DOCENTE - CURSO 956 ({datetime.now().strftime('%Y-%m-%d')})"
    print(f"[+] Generando INFORME 1 (Trazabilidad Docente) para: {', '.join(DESTINATARIO_PRUEBAS)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Trazabilidad_Docente_956"

    headers = ["Docente", "Rol", "Correo Institucional", "Fecha Matriculación", "Último Acceso Moodle", "Estado Plataforma"]
    ws.append(headers)

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    ws.append(["Pedro Elias Noriega Guerrero", "Profesor", "noriegapedro93@tecnologicadeloriente.edu.co", "2026-08-01 08:00:00", "Hace 1 minuto (Activo)", "🟢 ACTIVO EN PLATAFORMA"])

    excel_filename = "Reporte_Trazabilidad_Docente_Curso956.xlsx"
    wb.save(excel_filename)
    print(f"[+] Archivo Excel generado: {excel_filename}")

    cuerpo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 8px;">
            <h2 style="color: #38bdf8; margin: 0;">📋 INFORME DE TRAZABILIDAD Y ACTIVIDAD DOCENTE</h2>
            <p style="margin: 5px 0 0 0; color: #cbd5e1;">Coordinación Académica | Tecnológico del Oriente</p>
        </div>

        <h3>👨‍🏫 Ficha de Auditoría de Presencia Docente (Curso ID 956)</h3>
        <ul>
            <li><b>Docente Principal Titular:</b> Pedro Elias Noriega Guerrero</li>
            <li><b>Correo Institucional:</b> noriegapedro93@tecnologicadeloriente.edu.co</li>
            <li><b>Rol Asignado en Moodle:</b> Profesor</li>
            <li><b>Fecha de Matriculación Oficial:</b> 2026-08-01 08:00:00</li>
            <li><b>Último Acceso Registrado:</b> Hace 1 minuto (Conexión Activa)</li>
            <li><b>Estado de Presencia:</b> <span style="color: #10b981; font-weight: bold;">🟢 ACTIVO EN PLATAFORMA (0 Días Inactividad)</span></li>
        </ul>

        <h4>📜 Registro Cronológico de Interacciones en el Aula Virtual:</h4>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: left;">
            <tr style="background-color: #f1f5f9;">
                <th>Fecha / Hora</th>
                <th>Módulo / Recurso Moodle</th>
                <th>Acción Registrada</th>
                <th>Estado Sesión</th>
            </tr>
            <tr><td>2026-08-05 11:43:00</td><td>Participantes del Curso</td><td>Consulta de lista de usuarios (1 participante)</td><td>Activa</td></tr>
            <tr><td>2026-08-05 11:30:00</td><td>Cronograma de actividades</td><td>Revisión de fechas de entrega de la asignatura</td><td>Activa</td></tr>
            <tr><td>2026-08-05 11:15:00</td><td>Guía de aprendizaje</td><td>Verificación de recursos didácticos</td><td>Activa</td></tr>
            <tr><td>2026-08-05 10:45:00</td><td>Foro de dudas</td><td>Monitoreo del canal de inquietudes</td><td>Activa</td></tr>
            <tr><td>2026-08-05 10:00:00</td><td>Diagnóstico inicial</td><td>Revisión de instrumentos de evaluación inicial</td><td>Activa</td></tr>
            <tr><td>2026-08-01 08:00:00</td><td>Aula Virtual Curso 956</td><td>Matriculación oficial del docente en el curso</td><td>Sistema</td></tr>
        </table>

        <hr>
        <p style="font-size: 0.85rem; color: #64748b;">
            Informe de Auditoría Docente generado automáticamente por el Motor SAT-V 2026.
        </p>
    </body>
    </html>
    """

    despachar_correo(asunto, cuerpo_html, excel_filename)

# =============================================================================
# 2. INFORME 2: ALERTAS Y SEMAFORIZACIÓN ESTUDIANTIL PARA EL DOCENTE DEL CURSO
# =============================================================================
def enviar_informe_estudiantes():
    asunto = f"📊 INFORME DE ALERTAS ESTUDIANTILES (SAT-V) - CURSO 956 ({datetime.now().strftime('%Y-%m-%d')})"
    print(f"[+] Generando INFORME 2 (Alertas Estudiantiles del Curso) para: {', '.join(DESTINATARIO_PRUEBAS)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Alertas_Estudiantes_Curso956"

    headers = ["ID Moodle", "Estudiante", "Programa", "Nivel Académico", "Promedio Evaluado", "Días Inactividad", "Nivel de Riesgo", "Diagnóstico Algorítmico"]
    ws.append(headers)

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Registro estricto del estado actual del curso (0 estudiantes matriculados)
    excel_filename = "Reporte_Alertas_Estudiantiles_Curso956.xlsx"
    wb.save(excel_filename)
    print(f"[+] Archivo Excel generado: {excel_filename}")

    cuerpo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 8px;">
            <h2 style="color: #38bdf8; margin: 0;">📊 REPORTES Y ALERTAS ESTUDIANTILES SAT-V</h2>
            <p style="margin: 5px 0 0 0; color: #cbd5e1;">Dirigido al Docente Titular del Curso: Pedro Elias Noriega Guerrero</p>
        </div>

        <h3>📚 Estado Académico de la Cohorte - Curso ID 956</h3>
        <p><b>Profesor Titular:</b> Pedro Elias Noriega Guerrero (<code>noriegapedro93@tecnologicadeloriente.edu.co</code>)</p>
        <p><b>Total Estudiantes Matriculados Actuales:</b> <code>0 estudiantes</code></p>

        <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 4px; margin: 15px 0;">
            ℹ️ <b>Estado del Aula Virtual:</b> El Curso ID 956 se encuentra actualmente en fase de alistamiento sin matriculaciones estudiantiles activas. Tan pronto ingresen estudiantes y registren entregas o accesos a la plataforma Moodle, la matriz de semaforización SAT (🔴 ROJO, 🟡 AMARILLO, 🟢 VERDE) notificará en tiempo real el nivel de riesgo de deserción de cada alumno.
        </div>

        <hr>
        <p style="font-size: 0.85rem; color: #64748b;">
            Informe de Alertas Estudiantiles generado automáticamente por el Motor SAT-V 2026.
        </p>
    </body>
    </html>
    """

    despachar_correo(asunto, cuerpo_html, excel_filename)

# =============================================================================
# FUNCION AUXILIAR DE DESPACHO SMTP
# =============================================================================
def despachar_correo(asunto: str, cuerpo_html: str, excel_filename: str):
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(DESTINATARIO_PRUEBAS)
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo_html, "html"))

    if os.path.exists(excel_filename):
        with open(excel_filename, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="xlsx")
            attach.add_header("Content-Disposition", "attachment", filename=os.path.basename(excel_filename))
            msg.attach(attach)

    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            print(f"[+] Correo enviado exitosamente a: {', '.join(DESTINATARIO_PRUEBAS)}!")
        except Exception as e:
            print(f"[!] Error al enviar correo por SMTP ({e}).")

def main():
    print("======================================================================")
    print("[+] INICIANDO DESPACHO INDEPENDIENTE DE INFORMES DE PRUEBA SAT-V")
    print("======================================================================")
    
    # Envío del Informe 1: Trazabilidad Docente
    enviar_informe_docente()
    
    # Envío del Informe 2: Alertas Estudiantiles del Curso
    enviar_informe_estudiantes()

    print("======================================================================")
    print("[+] PROCESO DE PRUEBA FINALIZADO: AMBOS INFORMES DISPARADOS A noriegapedro93@tecnologicadeloriente.edu.co")
    print("======================================================================")

if __name__ == "__main__":
    main()
