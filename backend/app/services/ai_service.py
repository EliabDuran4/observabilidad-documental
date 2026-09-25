from anthropic import Anthropic
from app.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

def analyze_document(filename: str, category: str) -> str:
    prompt = f"Documento legal '{filename}', categoría '{category}'. Da un análisis breve (máx 3 líneas): tipo probable de documento y qué debe revisar el equipo legal."
    msg = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=250,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text