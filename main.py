from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile, os
from generar_propuesta import generar_pdf

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("cotizador.html", encoding="utf-8") as f:
        return f.read()

@app.get("/logo.png")
async def logo():
    return FileResponse("logo.png", media_type="image/png")

@app.post("/generar-pdf")
async def api_generar_pdf(request: Request):
    datos = await request.json()
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    generar_pdf(datos, tmp.name)
    placa = datos.get('placa','cotizacion').replace('-','').replace(' ','')
    nombre = f"propuesta_{placa}.pdf"
    return FileResponse(tmp.name, media_type="application/pdf", filename=nombre)
