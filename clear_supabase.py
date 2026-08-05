import httpx
from config import settings

def clear_tables():
    url = settings.SUPABASE_URL.rstrip('/')
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    tables = ["historial_alertas_sat", "moodle_interacciones", "estudiantes"]
    with httpx.Client(timeout=10.0) as client:
        for t in tables:
            res = client.delete(f"{url}/rest/v1/{t}?id=neq.00000000-0000-0000-0000-000000000000", headers=headers)
            print(f"[+] Tabla {t} limpiada: HTTP {res.status_code} - {res.text}")

if __name__ == "__main__":
    clear_tables()
