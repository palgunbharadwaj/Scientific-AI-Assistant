from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import APP_NAME, APP_VERSION
from backend.routers import auth_router, admin_router, query_router, chem_router

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Multi-Agent Scientific Assistant with CRA, DDRA & DPEA",
)

# ─── CORS (allow frontend on port 3000) ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(query_router.router)
app.include_router(admin_router.router)
app.include_router(chem_router.router)

# ─── Frontend Static Files ──────────────────────────────────────────────────
# Mount frontend with no-cache headers for development fluidity
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


from fastapi.responses import RedirectResponse

@app.get("/", tags=["Health"])
async def root():
    return RedirectResponse(url="/app/")
