from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.routers import (
    auth,
    busqueda,
    consultas,
    pacientes,
    profesionales,
    valoraciones,
)
from app.api.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
)

app = FastAPI(
    title="ATHomeRed API",
    version="0.1",
    description="API para la gestion de profesionales de la salud, pacientes y consultas",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(BusinessRuleException)
async def business_rule_exception_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(
    request: Request, exc: ResourceNotFoundException
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


app.include_router(auth.router, tags=["Autenticación"])
app.include_router(busqueda.router, prefix="/busqueda", tags=["Búsqueda"])
app.include_router(consultas.router, prefix="/consultas", tags=["Consultas"])
app.include_router(pacientes.router, prefix="/pacientes", tags=["Pacientes"])
app.include_router(
    profesionales.router, prefix="/profesionales", tags=["Profesionales"]
)
app.include_router(valoraciones.router, prefix="/valoraciones", tags=["Valoraciones"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
def index():
    return FileResponse("app/static/index.html")
