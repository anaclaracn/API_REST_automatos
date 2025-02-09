from fastapi import FastAPI
from app.routers import afd, pda, turing  # importe os módulos de rotas que você criará

app = FastAPI(
    title="API de Autômatos",
    description="API para manipular e analisar autômatos utilizando a biblioteca Automata",
    version="1.0.0"
)

# Inclua as rotas (endpoints)
app.include_router(afd.router, prefix="/afd", tags=["AFD"])
app.include_router(pda.router, prefix="/pda", tags=["Autômato com Pilha"])
app.include_router(turing.router, prefix="/turing", tags=["Máquina de Turing"])

@app.get("/")
def read_root():
    return {"message": "Página de API de Autômatos"}

# Para rodar via 'python app/main.py'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
