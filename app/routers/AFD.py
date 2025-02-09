from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from automata.fa.dfa import DFA
from fastapi.responses import FileResponse
import os

router = APIRouter()

# Definindo um modelo de dados para a criação de um AFD
class AFDModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    transitions: dict
    initial_state: str
    final_states: list[str]

# Endpoint para criar um AFD
@router.post("/create", summary="Cria um AFD")
def create_afd(data: AFDModel):
    try:
        # Verificando se os dados são válidos antes de criar o AFD
        if not data.states or not data.input_symbols or not data.transitions:
            raise HTTPException(status_code=400, detail="Dados incompletos ou inválidos")

        # Tentando criar o AFD
        afd = DFA(
            states=set(data.states),
            input_symbols=set(data.input_symbols),
            transitions=data.transitions,
            initial_state=data.initial_state,
            final_states=set(data.final_states)
        )

        # Retornando o AFD criado
        return {
            "message": "AFD criado com sucesso!",
            "automata": {
                "states": list(afd.states),
                "input_symbols": list(afd.input_symbols),
                "transitions": afd.transitions,
                "initial_state": afd.initial_state,
                "final_states": list(afd.final_states)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class TesteAFDModel(BaseModel):
    automata: AFDModel
    input_string: str

@router.post("/testar", summary="Testa a aceitação de uma string em um AFD")
def testar_afd(test_data: TesteAFDModel):
    try:
        data = test_data.automata
        afd = DFA(
            states=set(data.states),
            input_symbols=set(data.input_symbols),
            transitions=data.transitions,
            initial_state=data.initial_state,
            final_states=set(data.final_states)
        )
        # Testa se o AFD aceita a string
        is_accepted = afd.accepts_input(test_data.input_string)
        return {"accepted": is_accepted}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.get("/visualizar/{name}", summary="Visualiza o AFD como imagem")
# def visualizar_afd(name: str):
#     # O nome do arquivo do autômato seria passado via parâmetro
#     image_path = f"afd_{name}.png"
#     if not os.path.exists(image_path):
#         raise HTTPException(status_code=404, detail="Imagem não encontrada.")
#     return FileResponse(image_path)