from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import plans, auth, payments

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NakshaAI - AI-Powered Architectural Floor Plan & Building Map Generator with 2D/3D, Material Estimation, DXF/PDF Export, Auth, Credits & Monetization"
)

# Enable CORS for Web and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "NakshaAI Core API is running",
        "docs_url": "/docs",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
