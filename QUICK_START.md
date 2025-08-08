# 🚀 Guía de Inicio Rápido

## ✅ Sistema Arreglado

Todos los errores han sido solucionados. Tu sistema ahora:

- ✅ **Replica mensajes REALMENTE** entre Telegram y Discord
- ✅ **Integra watermarks** automáticamente (si el servicio está activo)
- ✅ **Procesa imágenes y videos** con descarga y reenvío
- ✅ **Maneja errores** gracefully con fallbacks
- ✅ **Dashboard funcional** con estadísticas en tiempo real

## 🎯 Opciones de Ejecución

### Opción 1: Solo Main.py (Más Simple)
```bash
python run.py
```
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs

### Opción 2: Sistema Completo (Con Watermarks)
```bash
python start_system.py
```
- Dashboard principal: http://localhost:8000/dashboard
- Dashboard watermarks: http://localhost:8081/dashboard

### Opción 3: Test de Configuración
```bash
python test_system.py
```

## ⚙️ Configuración Requerida

Asegúrate de que tu `.env` tenga:

```env
# Telegram (REQUERIDO)
TELEGRAM_API_ID=tu_api_id
TELEGRAM_API_HASH=tu_api_hash  
TELEGRAM_PHONE=+1234567890

# Discord (REQUERIDO)
WEBHOOK_-1001234567890=https://discord.com/api/webhooks/tu_webhook

# Opcional
DEBUG=false
WATERMARKS_ENABLED=true
```

## 🎨 Watermarks (Opcional)

Para activar watermarks:

1. Crea `watermark_service.py` con el contenido del microservicio
2. Ejecuta: `python start_system.py`
3. Configura en: http://localhost:8081/dashboard

## 📊 Características del Sistema

### Replicación Automática:
- ✅ **Texto** → Con watermarks de texto
- ✅ **Imágenes** → Descarga, procesa y reenvía  
- ✅ **Videos** → Maneja límites de tamaño de Discord
- ✅ **Documentos** → Notifica de archivos compartidos
- ✅ **Otros medios** → Stickers, audios, etc.

### Microservicios:
- 🎨 **Watermark Service** → Puerto 8081 (opcional)
- 📤 **Discord Sender** → Con retry logic
- 📊 **Stats Service** → Métricas en tiempo real

### Dashboard Features:
- 📈 **Estadísticas en vivo** → Mensajes procesados, errores, uptime
- 👥 **Gestión de grupos** → Ver configuración por grupo
- 🔧 **Health checks** → Estado de todos los servicios
- 📡 **WebSocket** → Updates en tiempo real

## 🔧 Troubleshooting

### Si no replica mensajes:
1. Verificar `.env` configurado correctamente
2. Comprobar que los webhooks de Discord funcionan
3. Revisar logs en la consola
4. Usar `python test_system.py` para diagnosticar

### Si hay errores:
1. Verificar dependencias: `pip install -r requirements.txt`
2. Comprobar permisos de archivos
3. Revisar configuración de Telegram (API_ID, API_HASH)

## 🎯 Próximos Pasos

1. **Probar replicación** → Envía un mensaje de prueba
2. **Configurar watermarks** → Si quieres personalización
3. **Monitorear dashboard** → Ver estadísticas y actividad
4. **Escalar si necesitas** → Deploy con Docker

¡Tu sistema está listo para producción! 🚀
