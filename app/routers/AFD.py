from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from automata.fa.dfa import DFA
import json
import os
import uuid
import graphviz

router = APIRouter()
afd_store = {}
AFD_FILE = "afd_store.json"
IMAGES_DIR = "automata_images"

# Criar pasta para armazenar imagens dos autômatos, se não existir
os.makedirs(IMAGES_DIR, exist_ok=True)

def save_afd_store():
    """Salva os AFDs no arquivo JSON"""
    with open(AFD_FILE, "w") as f:
        json.dump({k: afd_to_dict(v) for k, v in afd_store.items()}, f)

def load_afd_store():
    """Carrega os AFDs do arquivo JSON"""
    global afd_store
    if os.path.exists(AFD_FILE):
        with open(AFD_FILE, "r") as f:
            try:
                data = json.load(f)
                for key, value in data.items():
                    afd_store[key] = afd_from_dict(value)
            except json.JSONDecodeError:
                afd_store = {}  # Se houver erro, reinicia o armazenamento

def afd_to_dict(afd: DFA) -> dict:
    """Converte um objeto AFD para um dicionário serializável."""
    return {
        "states": list(afd.states),
        "input_symbols": list(afd.input_symbols),
        "transitions": afd.transitions,
        "initial_state": afd.initial_state,
        "final_states": list(afd.final_states)
    }

def afd_from_dict(data: dict) -> DFA:
    """Reconstrói um objeto AFD a partir de um dicionário serializado."""
    return DFA(
        states=set(data["states"]),
        input_symbols=set(data["input_symbols"]),
        transitions=data["transitions"],
        initial_state=data["initial_state"],
        final_states=set(data["final_states"])
    )

# Chamada para carregar os AFDs ao iniciar o servidor
load_afd_store()

class AFDModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    transitions: dict
    initial_state: str
    final_states: list[str]

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
        automata_id = str(uuid.uuid4())
        afd_store[automata_id] = afd

        save_afd_store()

        return {
            "message": "AFD criado com sucesso!",
            "id": automata_id,
            "automata": afd_to_dict(afd)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{automata_id}", summary="Recupera informações do AFD")
def get_afd(automata_id: str):
    afd = afd_store.get(automata_id)
    if afd is None:
        raise HTTPException(status_code=404, detail="AFD não encontrado")
    return afd_to_dict(afd)

@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pelo AFD")
def test_afd(automata_id: str, payload: dict):
    afd = afd_store.get(automata_id)
    if afd is None:
        raise HTTPException(status_code=404, detail="AFD não encontrado")
    
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    
    try:
        result = afd.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Novo endpoint para visualizar o AFD como imagem
# @router.get("/{automata_id}/visualize", summary="Gera e retorna uma imagem do AFD")
# def visualize_afd(automata_id: str, format: str = "png"):
#     """
#     Gera e retorna uma imagem do autômato no formato especificado (PNG ou SVG).
#     """
#     afd = afd_store.get(automata_id)
#     if afd is None:
#         raise HTTPException(status_code=404, detail="AFD não encontrado")
    
#     if format not in ["png", "svg"]:
#         raise HTTPException(status_code=400, detail="Formato inválido. Escolha 'png' ou 'svg'.")

#     image_path = os.path.join(IMAGES_DIR, f"{automata_id}.{format}")
    
#     try:
#         # Criar o gráfico usando Graphviz
#         dot = afd.show_diagram()  # Retorna um objeto Graphviz
#         dot.format = format  # Define o formato do arquivo (png ou svg)
#         dot.render(image_path, format=format, cleanup=True)

#         return FileResponse(image_path, media_type=f"image/{format}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao gerar imagem: {str(e)}")