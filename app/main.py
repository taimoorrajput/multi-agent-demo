from fastapi import FastAPI

from app.routers.tag import router as tag_router

app = FastAPI(title="Task Manager API")

app.include_router(tag_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
