# naina/api/server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from naina.api.routes import router
from naina.api.ws import ws_router
from naina.config import WEB_DIR

# Import tools so they register themselves into TOOL_REGISTRY
import naina.tools.system_control   # noqa
import naina.tools.productivity     # noqa

def create_app() -> FastAPI:
    app = FastAPI(title="Naina AI Assistant", version="1.0.0")

    app.add_middleware(CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(router, prefix="/api")
    app.include_router(ws_router)

    # Serve static PWA files — only if web dir exists
    if WEB_DIR.exists():
        app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="static")

    return app
