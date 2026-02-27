from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)