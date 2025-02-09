from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from automata.fa.dfa import DFA  

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
        afd = DFA(
            states=set(data.states),
            input_symbols=set(data.input_symbols),
            transitions=data.transitions,
            initial_state=data.initial_state,
            final_states=set(data.final_states)
        )
        # Aqui você pode armazenar o objeto 'afd' em memória ou persistir de outra forma.
        # Para este exemplo, retornaremos suas configurações.
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
