from fastapi import FastAPI

app = FastAPI(
    title="Ameru Cultural Library API",
    version="0.1.0",
    description="Content and cultural knowledge API for the Ameru Cultural Library.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1", tags=["system"])
def api_root() -> dict[str, str]:
    return {"version": "v1", "status": "available"}
