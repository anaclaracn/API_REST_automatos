from fastapi import FastAPI
from app.routers import afd, pilha, turing

app = FastAPI(
    title="API de Autômatos",
    description="API para manipular e analisar autômatos utilizando a biblioteca Automata",
    version="1.0.0"
)

# Routers das diferentes implementações de autômatos
app.include_router(afd.router, prefix="/afd", tags=["AFD"])
app.include_router(pilha.router, prefix="/pilha", tags=["pilha"])
app.include_router(turing.router, prefix="/turing", tags=["Máquina de Turing"])

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Autômatos!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
