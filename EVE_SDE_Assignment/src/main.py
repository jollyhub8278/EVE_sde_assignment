from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "EVE Diagnostics API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}