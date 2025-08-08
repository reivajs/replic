"""
EJEMPLO DE INTEGRACIÓN PARA TU MAIN.PY
====================================

Copia este código a tu main.py existente para añadir watermarks:

# 1. Al inicio de tu main.py, después de los imports existentes:

from services.watermark_client import watermark_client

# 2. En tu handler de mensajes, ANTES de enviar a Discord:

async def tu_handler_de_mensajes(event):
    chat_id = event.chat_id
    message = event.message
    
    # Tu lógica existente...
    
    # NUEVO: Procesar con watermarks si el servicio está disponible
    service_available = await watermark_client.is_service_available()
    
    if service_available and message.text:
        # Procesar texto
        processed_text, was_modified = await watermark_client.process_text(chat_id, message.text)
        if was_modified:
            print(f"📝 Texto procesado para grupo {chat_id}")
            # Usar processed_text en lugar de message.text
            texto_a_enviar = processed_text
        else:
            texto_a_enviar = message.text
    else:
        texto_a_enviar = message.text
    
    if service_available and message.photo:
        # Procesar imagen
        image_bytes = await message.download_media(bytes)
        processed_bytes, was_processed = await watermark_client.process_image(chat_id, image_bytes)
        if was_processed:
            print(f"🖼️ Imagen procesada para grupo {chat_id}")
            # Usar processed_bytes en lugar de image_bytes
            imagen_a_enviar = processed_bytes
        else:
            imagen_a_enviar = image_bytes
    
    # Tu lógica de envío a Discord continúa igual...

# 3. Para configurar watermarks por grupo:
#    - Ejecuta: python watermark_service.py (en terminal separada)
#    - Ve a: http://localhost:8081/dashboard
#    - Configura cada grupo con sus watermarks

# ¡LISTO! Tu sistema funcionará con watermarks sin romper nada.
"""