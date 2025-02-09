from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from automata.tm.tm import TM as TuringMachine  # Certifique-se da classe e do módulo corretos

router = APIRouter()
tm_store = {}  # Armazenamento em memória para as Máquinas de Turing

class TuringMachineModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    tape_symbols: list[str]
    transitions: dict
    initial_state: str
    blank_symbol: str
    final_states: list[str]

@router.post("/create", summary="Cria uma Máquina de Turing")
def create_tm(data: TuringMachineModel):
    try:
        tm = TuringMachine(
            states=set(data.states),
            input_symbols=set(data.input_symbols),
            tape_symbols=set(data.tape_symbols),
            transitions=data.transitions,
            initial_state=data.initial_state,
            blank_symbol=data.blank_symbol,
            final_states=set(data.final_states)
        )
        automata_id = str(uuid.uuid4())
        tm_store[automata_id] = tm
        return {
            "message": "Máquina de Turing criada com sucesso!",
            "id": automata_id,
            "automata": {
                "states": list(tm.states),
                "input_symbols": list(tm.input_symbols),
                "tape_symbols": list(tm.tape_symbols),
                "transitions": tm.transitions,
                "initial_state": tm.initial_state,
                "blank_symbol": tm.blank_symbol,
                "final_states": list(tm.final_states)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}", summary="Recupera informações da Máquina de Turing")
def get_tm(automata_id: str):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="Máquina de Turing não encontrada")
    return {
        "states": list(tm.states),
        "input_symbols": list(tm.input_symbols),
        "tape_symbols": list(tm.tape_symbols),
        "transitions": tm.transitions,
        "initial_state": tm.initial_state,
        "blank_symbol": tm.blank_symbol,
        "final_states": list(tm.final_states)
    }

@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pela Máquina de Turing")
def test_tm(automata_id: str, payload: dict):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="Máquina de Turing não encontrada")
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    try:
        # Supondo que a classe TuringMachine possua um método `accepts_input`
        result = tm.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}/visualize", summary="Visualiza a Máquina de Turing em formato gráfico")
def visualize_tm(automata_id: str):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="Máquina de Turing não encontrada")
    try:
        # Similar ao caso do PDA, aqui você chamaria o método de visualização
        return {"graph": "Visualização gráfica da Máquina de Turing (função não implementada)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
