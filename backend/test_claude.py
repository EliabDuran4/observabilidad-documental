from app.services.ai_service import analyze_document

resultado = analyze_document("contrato_arrendamiento_2026.pdf")
print("✅ Respuesta de Claude:")
print(resultado)