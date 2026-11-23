from fastapi import FastAPI

from app.routers.comment import router as comment_router

app = FastAPI(title="Task Manager API")

app.include_router(comment_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
