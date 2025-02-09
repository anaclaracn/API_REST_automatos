from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from automata.fa.dfa import DFA
import json
import os
import uuid
import graphviz

router = APIRouter()

# Armazenamento em memória para os AFDs
afd_store = {}
AFD_FILE = "afd_store.json"
IMAGES_DIR = "automata_images"

# Criar pasta para armazenar imagens dos autômatos, se não existir
os.makedirs(IMAGES_DIR, exist_ok=True)

# Funções de persistência
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

# Funções de conversão para o AFD
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
    """Reconstrói um objeto AFD a partir de um dicionário serializável."""
    return DFA(
        states=set(data["states"]),
        input_symbols=set(data["input_symbols"]),
        transitions=data["transitions"],
        initial_state=data["initial_state"],
        final_states=set(data["final_states"])
    )

# Carregar os AFDs ao iniciar o servidor
load_afd_store()

# Modelo de dados para a criação de um AFD
class AFDModel(BaseModel):
    states: list[str]
    input_symbols: list[str]
    transitions: dict
    initial_state: str
    final_states: list[str]

# Endpoint para criar um AFD (mantendo a lógica atual)
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

# Endpoint para recuperar informações do AFD
@router.get("/{automata_id}", summary="Recupera informações do AFD")
def get_afd(automata_id: str):
    afd = afd_store.get(automata_id)
    if afd is None:
        raise HTTPException(status_code=404, detail="AFD não encontrado")
    return afd_to_dict(afd)

# Endpoint para testar a aceitação de uma string pelo AFD
@router.post("/{automata_id}/test", summary="Testa a aceitação de uma string pelo AFD")
def test_afd(automata_id: str, payload: dict):
    afd = afd_store.get(automata_id)
    if afd is None:
        raise HTTPException(status_code=404, detail="AFD não encontrado")
    
    input_string = payload.get("input_string")
    if input_string is None:
        raise HTTPException(status_code=400, detail="Campo 'input_string' é necessário")
    
    try:
        # O método da classe DFA é "accepts" para verificar se a string é aceita
        result = afd.accepts(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Função para gerar uma representação DOT do AFD
def afd_to_dot(afd: DFA) -> str:
    """
    Gera uma representação no formato DOT do AFD.
      - Cria um nó inicial invisível que aponta para o estado inicial.
      - Desenha cada estado (estados finais com dupla borda).
      - Para cada transição, cria uma aresta com rótulo indicando o símbolo de entrada.
    """
    dot_lines = []
    dot_lines.append("digraph DFA {")
    dot_lines.append("  rankdir=LR;")
    dot_lines.append("  size=\"8,5\";")
    dot_lines.append("  node [shape = circle];")
    # Nó inicial (invisível)
    dot_lines.append("  __start__ [shape = point];")
    dot_lines.append(f"  __start__ -> \"{afd.initial_state}\";")
    
    # Estados (estados finais com dupla borda)
    for state in afd.states:
        if state in afd.final_states:
            dot_lines.append(f"  \"{state}\" [shape = doublecircle];")
        else:
            dot_lines.append(f"  \"{state}\" [shape = circle];")
    
    # Adiciona as arestas (transições)
    for state, trans in afd.transitions.items():
        for input_symbol, next_state in trans.items():
            # Se o input_symbol estiver vazio, usa "ε"
            label = input_symbol if input_symbol != "" else "ε"
            dot_lines.append(f"  \"{state}\" -> \"{next_state}\" [ label = \"{label}\" ];")
    
    dot_lines.append("}")
    return "\n".join(dot_lines)

# Endpoint para visualizar o AFD em formato gráfico (SVG ou PNG)
@router.get("/{automata_id}/visualize", summary="Visualiza o AFD em formato gráfico (SVG ou PNG)")
def visualize_afd(automata_id: str, format: str = "svg"):
    afd = afd_store.get(automata_id)
    if afd is None:
        raise HTTPException(status_code=404, detail="AFD não encontrado")
    
    dot_str = afd_to_dot(afd)
    
    # Adiciona explicitamente o caminho para o Graphviz, se necessário
    graphviz_path = r"C:\Program Files\Graphviz\bin"
    if graphviz_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + graphviz_path

    try:
        from graphviz import Source
    except ImportError:
        raise HTTPException(status_code=500, detail="O pacote graphviz não está instalado.")
    
    try:
        # Cria o objeto Source e gera o gráfico no formato especificado
        graph = Source(dot_str, format=format, engine="dot")
        output = graph.pipe(format=format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao renderizar o gráfico: {str(e)}")
    
    mime = "image/svg+xml" if format.lower() == "svg" else "image/png"
    return Response(content=output, media_type=mime)
