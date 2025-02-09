from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from automata.tm.ntm import NTM  # Importando a Máquina de Turing (NTM)
import json
import os
import uuid
import graphviz

router = APIRouter()
tm_store = {}  # Armazena as MTs em memória
NTM_FILE = "tm_store.json"

# Funções de persistência
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

# Funções de conversão para a Máquina de Turing
def tm_to_dict(tm: NTM) -> dict:
    """Converte um objeto MT para um dicionário serializável."""
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
    """Reconstrói um objeto MT a partir de um dicionário serializável."""
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

# Modelo de dados para a criação de uma Máquina de Turing
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

# Função para gerar uma representação DOT da Máquina de Turing
def tm_to_dot(tm: NTM) -> str:
    """
    Gera uma representação no formato DOT da Máquina de Turing.
    - Cria um nó inicial invisível que aponta para o estado inicial.
    - Desenha cada estado (estados finais com dupla borda).
    - Para cada transição, cria uma aresta com rótulo no formato:
          "read / write, move"
      onde:
          read: símbolo lido (usa "ε" se vazio),
          write: símbolo escrito (usa "ε" se vazio),
          move: direção (geralmente "L", "R" ou "S" para stay).
    """
    dot_lines = []
    dot_lines.append("digraph TuringMachine {")
    dot_lines.append("  rankdir=LR;")
    dot_lines.append("  size=\"8,5\";")
    dot_lines.append("  node [shape = circle];")
    # Nó inicial (invisível)
    dot_lines.append("  __start__ [shape = point];")
    dot_lines.append(f"  __start__ -> \"{tm.initial_state}\";")
    
    # Definir os estados (estados finais com dupla borda)
    for state in tm.states:
        if state in tm.final_states:
            dot_lines.append(f"  \"{state}\" [shape = doublecircle];")
        else:
            dot_lines.append(f"  \"{state}\" [shape = circle];")
    
    # Adicionar as arestas para as transições
    # Supondo que tm.transitions tenha a estrutura:
    # { state: { tape_symbol: {(new_state, write_symbol, move)} } }
    for state, trans_dict in tm.transitions.items():
        for tape_symbol, trans_set in trans_dict.items():
            for (new_state, write_symbol, move) in trans_set:
                # Se tape_symbol ou write_symbol estiverem vazios, use "ε"
                read = tape_symbol if tape_symbol != "" else "ε"
                write = write_symbol if write_symbol != "" else "ε"
                label = f"{read} / {write}, {move}"
                dot_lines.append(f"  \"{state}\" -> \"{new_state}\" [ label = \"{label}\" ];")
    
    dot_lines.append("}")
    return "\n".join(dot_lines)

# Endpoint para visualizar a Máquina de Turing em formato gráfico (SVG ou PNG)
@router.get("/{automata_id}/visualize", summary="Visualiza a MT em formato gráfico (SVG ou PNG)")
def visualize_tm(automata_id: str, format: str = "svg"):
    tm = tm_store.get(automata_id)
    if tm is None:
        raise HTTPException(status_code=404, detail="MT não encontrada")
    
    dot_str = tm_to_dot(tm)
    
    # Adicionar o caminho para o Graphviz, se necessário
    graphviz_path = r"C:\Program Files\Graphviz\bin"
    if graphviz_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + graphviz_path

    try:
        from graphviz import Source
    except ImportError:
        raise HTTPException(status_code=500, detail="O pacote graphviz não está instalado.")
    
    try:
        graph = Source(dot_str, format=format, engine="dot")
        output = graph.pipe(format=format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao renderizar o gráfico: {str(e)}")
    
    mime = "image/svg+xml" if format.lower() == "svg" else "image/png"
    return Response(content=output, media_type=mime)
