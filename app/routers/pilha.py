from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from automata.pda.npda import NPDA  # Utilize a classe NPDA, que é a implementação concreta
import json
import os

router = APIRouter()
pda_store = {}  # Armazenamento em memória: chave (ID) -> objeto NPDA

def npda_to_dict(npda: NPDA) -> dict:
    """Converte um objeto NPDA para um dicionário serializável."""
    return {
        "states": list(npda.states),  # Convertendo set para list
        "input_symbols": list(npda.input_symbols),
        "stack_symbols": list(npda.stack_symbols),
        "transitions": {
            state: {
                input_symbol: {
                    stack_symbol: [list(item) for item in trans_set]  # Convertendo frozenset para list
                }
                for input_symbol, stack_trans in input_dict.items()
                for stack_symbol, trans_set in stack_trans.items()
            }
            for state, input_dict in npda.transitions.items()
        },
        "initial_state": npda.initial_state,
        "initial_stack_symbol": npda.initial_stack_symbol,
        "final_states": list(npda.final_states)
    }


def npda_from_dict(data: dict) -> NPDA:
    """Reconstrói um objeto NPDA a partir de um dicionário serializado."""
    return NPDA(
        states=set(data["states"]),
        input_symbols=set(data["input_symbols"]),
        stack_symbols=set(data["stack_symbols"]),
        transitions={
            state: {
                input_symbol: {
                    stack_symbol: frozenset(tuple(item) for item in trans_list)  # Convertendo list para frozenset
                    for stack_symbol, trans_list in stack_trans.items()
                }
                for input_symbol, stack_trans in input_dict.items()
            }
            for state, input_dict in data["transitions"].items()
        },
        initial_state=data["initial_state"],
        initial_stack_symbol=data["initial_stack_symbol"],
        final_states=set(data["final_states"])
    )

pda_store = {}
PDA_FILE = "pda_store.json"

def save_pda_store():
    """Salva os PDAs no arquivo JSON"""
    with open(PDA_FILE, "w") as f:
        json.dump({k: npda_to_dict(v) for k, v in pda_store.items()}, f)

def load_pda_store():
    """Carrega os PDAs do arquivo JSON"""
    global pda_store
    if os.path.exists(PDA_FILE):
        with open(PDA_FILE, "r") as f:
            try:
                data = json.load(f)
                for key, value in data.items():
                    pda_store[key] = npda_from_dict(value)  # Reconstrói os PDAs
            except json.JSONDecodeError:
                pda_store = {}  # Se houver erro, reinicia o armazenamento

# Chamada para carregar os PDAs ao iniciar o servidor
load_pda_store()


class PDAModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    stack_symbols: list[str]
    transitions: dict
    initial_state: str
    initial_stack_symbol: str
    final_states: list[str]

def convert_transitions(transitions: dict) -> dict:
    """
    Converte o dicionário de transições recebido no seguinte formato:
    
    {
        "q0": {
            "a,Z": [["q1", "AZ"]],
            "b,Z": [["q0", "BZ"]],
            "a,A": [["q1", ""]],
            "b,B": [["q1", ""]]
        },
        "q1": {
            "a,A": [["q1", ""]],
            "b,B": [["q1", ""]],
            "": [["q2", ""]]
        }
    }
    
    Para um formato aninhado, onde o símbolo de entrada vazio é representado como `""`.
    """
    converted = {}
    for state, trans in transitions.items():
        new_trans = {}
        for key, value in trans.items():
            if ',' in key:
                input_symbol, stack_symbol = key.split(",")
            else:
                input_symbol = ""
                stack_symbol = key.strip()
            
            input_symbol = input_symbol.strip()
            stack_symbol = stack_symbol.strip()

            if not stack_symbol:
                raise HTTPException(
                    status_code=400,
                    detail=f"Símbolo da pilha inválido na transição '{key}' para o estado '{state}'."
                )

            if input_symbol not in new_trans:
                new_trans[input_symbol] = {}

            try:
                new_transitions = {tuple(item) for item in value}
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato inválido no valor das transições para a chave '{key}'."
                )

            new_trans[input_symbol][stack_symbol] = new_transitions
        converted[state] = new_trans
    return converted



@router.post("/create", summary="Cria um Autômato com Pilha (PDA)")
def create_pda(data: PDAModel):
    try:
        converted_transitions = convert_transitions(data.transitions)

        # 🔹 Adicionar "ε" como símbolo de entrada, se houver epsilon-movimentos
        all_input_symbols = set(data.input_symbols)
        for state in converted_transitions:
            for input_symbol in converted_transitions[state]:
                if input_symbol == "ε":
                    all_input_symbols.add("ε")

        npda = NPDA(
            states=set(data.states),
            input_symbols=all_input_symbols,
            stack_symbols=set(data.stack_symbols),
            transitions=converted_transitions,
            initial_state=data.initial_state,
            initial_stack_symbol=data.initial_stack_symbol,
            final_states=set(data.final_states)
        )

        automata_id = str(uuid.uuid4())
        pda_store[automata_id] = npda

        # 🔹 Salvar no arquivo para persistência
        save_pda_store()

        return {
            "message": "PDA criado com sucesso!",
            "id": automata_id,
            "automata": {
                "states": list(npda.states),
                "input_symbols": list(all_input_symbols),  # Agora inclui "ε" se necessário
                "stack_symbols": list(npda.stack_symbols),
                "transitions": data.transitions,  # Retorna o JSON enviado originalmente
                "initial_state": npda.initial_state,
                "initial_stack_symbol": npda.initial_stack_symbol,
                "final_states": list(npda.final_states)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{automata_id}", summary="Recupera informações do PDA")
def get_pda(automata_id: str):
    npda = pda_store.get(automata_id)
    if npda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    return {
        "states": list(npda.states),
        "input_symbols": list(npda.input_symbols),
        "stack_symbols": list(npda.stack_symbols),
        "transitions": npda.transitions,
        "initial_state": npda.initial_state,
        "initial_stack_symbol": npda.initial_stack_symbol,
        "final_states": list(npda.final_states)
    }

@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pelo PDA")
def test_pda(automata_id: str, payload: dict):
    npda = pda_store.get(automata_id)
    if npda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    
    try:
        result = npda.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{automata_id}/visualize", summary="Visualiza o PDA em formato gráfico")
def visualize_pda(automata_id: str):
    npda = pda_store.get(automata_id)
    if npda is None:
        raise HTTPException(status_code=404, detail="PDA não encontrado")
    try:
        return {"graph": "Visualização gráfica do PDA (função não implementada)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
