"""Dashboard Controller"""
from fastapi import Request
from fastapi.responses import HTMLResponse

async def index(request: Request):
    """Index page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enterprise Orchestrator</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #333; }
            .links { margin-top: 20px; }
            .links a { margin-right: 20px; text-decoration: none; color: #007bff; }
        </style>
    </head>
    <body>
        <h1>🎭 Enterprise Orchestrator</h1>
        <p>Sistema modular de microservicios</p>
        <div class="links">
            <a href="/docs">📚 API Docs</a>
            <a href="/api/v1/health">🏥 Health Check</a>
            <a href="/redoc">📖 ReDoc</a>
        </div>
    </body>
    </html>
    """)

async def main(request: Request):
    """Dashboard main"""
    return await index(request)
