from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# === PREP SECITON ===
app = FastAPI(
    title="Movie Programming Demo",
    version="0.0.1"
)

app.mount("/styles", StaticFiles(directory="app/styles"), name="styles")
app.mount("/javascript", StaticFiles(directory="app/javascript", name="javascript"))

templates = Jinja2Templates(
    directory="app/templates"
)

# === MAIN SECTION ===
@app.get("/", response_class=HTMLResponse)
@app.get("/database", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )
