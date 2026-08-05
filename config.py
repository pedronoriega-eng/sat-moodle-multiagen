import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Configuración global del servicio Backend SAT Moodle 2026.
    Carga variables desde el entorno o valores predeterminados seguros para fallback local.
    """
    PROJECT_NAME: str = "Sistema de Alertas Tempranas SAT-V Moodle"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1/sat"
    DEBUG: bool = False

    # Key de Gemini (Google AI Studio)
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    
    # Modelos Gemini requeridos por el manual multiagente
    GEMINI_FAST_MODEL: str = "gemini-1.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-1.5-pro"

    # Supabase Free Tier Credentials
    SUPABASE_URL: str = Field(default="https://qkpvumvvcxoqdfuzaome.supabase.co", env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(default="", env="SUPABASE_KEY")

    # SMTP Configuration para notificaciones por correo
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="alertas.sat.institucional@gmail.com", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_FROM: str = Field(default="alertas.sat.institucional@gmail.com", env="SMTP_FROM")

    # Moodle Integration Configuration (Tecnológico del Oriente - Curso ID 956)
    MOODLE_URL: str = Field(default="https://campusvirtual.tecnologicadeloriente.edu.co", env="MOODLE_URL")
    MOODLE_COURSE_ID: int = Field(default=956, env="MOODLE_COURSE_ID")
    MOODLE_WS_TOKEN: str = Field(default="", env="MOODLE_WS_TOKEN")

    # GitHub Credentials
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")
    GITHUB_REPO_NAME: str = "sat-moodle-multiagen"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
