from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from automata.pda.pda import PDA  

router = APIRouter()
pda_store = {}  # Armazenamento em memória: chave (ID) -> objeto PDA

class PDAModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    stack_symbols: list[str]
    transitions: dict
    initial_state: str
    initial_stack_symbol: str
    final_states: list[str]

@router.post("/create", summary="Cria um Autômato com Pilha (PDA)")
def create_pda(data: PDAModel):
    try:
        pda = PDA(
            states=set(data.states),
            input_symbols=set(data.input_symbols),
            stack_symbols=set(data.stack_symbols),
            transitions=data.transitions,
            initial_state=data.initial_state,
            initial_stack_symbol=data.initial_stack_symbol,
            final_states=set(data.final_states)
        )
        automata_id = str(uuid.uuid4())
        pda_store[automata_id] = pda
        return {
            "message": "PDA criado com sucesso!",
            "id": automata_id,
            "automata": {
                "states": list(pda.states),
                "input_symbols": list(pda.input_symbols),
                "stack_symbols": list(pda.stack_symbols),
                "transitions": pda.transitions,
                "initial_state": pda.initial_state,
                "initial_stack_symbol": pda.initial_stack_symbol,
                "final_states": list(pda.final_states)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}", summary="Recupera informações do PDA")
def get_pda(automata_id: str):
    pda = pda_store.get(automata_id)
    if pda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    return {
        "states": list(pda.states),
        "input_symbols": list(pda.input_symbols),
        "stack_symbols": list(pda.stack_symbols),
        "transitions": pda.transitions,
        "initial_state": pda.initial_state,
        "initial_stack_symbol": pda.initial_stack_symbol,
        "final_states": list(pda.final_states)
    }

@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pelo PDA")
def test_pda(automata_id: str, payload: dict):
    pda = pda_store.get(automata_id)
    if pda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    try:
        result = pda.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}/visualize", summary="Visualiza o PDA em formato gráfico")
def visualize_pda(automata_id: str):
    pda = pda_store.get(automata_id)
    if pda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    try:
        # Aqui você deve chamar o método que gera a visualização.
        # Exemplo: se a biblioteca oferecer um método para retornar um DOT ou imagem,
        # você pode processá-lo e retornar o arquivo (PNG/SVG) ou um link para download.
        # Neste exemplo, retornaremos uma mensagem de placeholder.
        return {"graph": "Visualização gráfica do PDA (função não implementada)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
