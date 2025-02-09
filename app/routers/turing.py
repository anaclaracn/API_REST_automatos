from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import json
import os
from automata.tm.ntm import NTM  # Importando a Máquina de Turing

router = APIRouter()
tm_store = {}  # Armazena as MTs em memória

NTM_FILE = "tm_store.json"

def save_tm_store():
    """Salva as MTs no arquivo JSON"""
    with open(NTM_FILE, "w") as f:
        json.dump({k: tm_to_dict(v) for k, v in tm_store.items()}, f)

def load_tm_store():
    """Carrega as MTs do arquivo JSON"""
    global tm_store
    if os.path.exists(NTM_FILE):
        with open(NTM_FILE, "r") as f:
            try:
                data = json.load(f)
                for key, value in data.items():
                    tm_store[key] = tm_from_dict(value)
            except json.JSONDecodeError:
                tm_store = {}  # Se houver erro, reinicia o armazenamento

def tm_to_dict(tm: NTM) -> dict:
    """Converte um objeto TM para um dicionário serializável."""
    return {
        "states": list(tm.states),
        "input_symbols": list(tm.input_symbols),
        "tape_symbols": list(tm.tape_symbols),
        "transitions": tm.transitions,
        "initial_state": tm.initial_state,
        "blank_symbol": tm.blank_symbol,
        "final_states": list(tm.final_states)
    }

def tm_from_dict(data: dict) -> NTM:
    """Reconstrói um objeto TM a partir de um dicionário serializado."""
    return NTM(
        states=set(data["states"]),
        input_symbols=set(data["input_symbols"]),
        tape_symbols=set(data["tape_symbols"]),
        transitions=data["transitions"],
        initial_state=data["initial_state"],
        blank_symbol=data["blank_symbol"],
        final_states=set(data["final_states"])
    )

# Carregar as MTs ao iniciar o servidor
load_tm_store()

class TMModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    tape_symbols: list[str]
    transitions: dict
    initial_state: str
    blank_symbol: str
    final_states: list[str]

@router.post("/create", summary="Cria uma Máquina de Turing")
def create_tm(data: TMModel):
    try:
        tm = NTM(
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
        save_tm_store()

        return {
            "message": "MT criada com sucesso!",
            "id": automata_id,
            "automata": tm_to_dict(tm)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}", summary="Recupera informações da Máquina de Turing")
def get_tm(automata_id: str):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="MT não encontrada")
    return tm_to_dict(tm)

@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pela MT")
def test_tm(automata_id: str, payload: dict):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="MT não encontrada")
    
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    
    try:
        result = tm.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
