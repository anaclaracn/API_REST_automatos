from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from automata.fa.dfa import DFA  # Importando o Autômato Finito Determinístico
import json
import os
import uuid
import graphviz

# Criação do roteador para o AFD 
router = APIRouter()

# Armazenamento em memória dos AFDs criados
afd_store = {}

# Nome do arquivo para persistência dos AFDs
AFD_FILE = "afd_store.json"

# Diretório onde as imagens dos autômatos serão armazenadas
IMAGES_DIR = "automata_images"

# Criar pasta para armazenar imagens dos autômatos, se não existir
os.makedirs(IMAGES_DIR, exist_ok=True)

# Função para salvar o estado atual dos AFDs no arquivo JSON
def save_afd_store():
    """Salva os AFDs no arquivo JSON"""
    with open(AFD_FILE, "w") as f:
        json.dump({k: afd_to_dict(v) for k, v in afd_store.items()}, f)

# Função para carregar os AFDs armazenados no JSON ao iniciar o servidor
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

# Função para converter um AFD em um dicionário serializável
def afd_to_dict(afd: DFA) -> dict:
    """Converte um objeto AFD para um dicionário serializável."""
    return {
        "states": list(afd.states),
        "input_symbols": list(afd.input_symbols),
        "transitions": afd.transitions,
        "initial_state": afd.initial_state,
        "final_states": list(afd.final_states)
    }

# Função para reconstruir um AFD a partir de um dicionário
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

# Modelo de dados para definir um AFD na API
class AFDModel(BaseModel):
    states: list[str]  # Lista de estados
    input_symbols: list[str]  # Alfabeto de entrada
    transitions: dict  # Tabela de transições
    initial_state: str  # Estado inicial
    final_states: list[str]  # Estados finais

# Endpoint para criar um AFD e armazená-lo na memória
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
        automata_id = str(uuid.uuid4())   # Gera um identificador único
        afd_store[automata_id] = afd

        save_afd_store()   # Salva o novo AFD no arquivo JSON

        return {
            "message": "AFD criado com sucesso!",
            "id": automata_id,
            "automata": afd_to_dict(afd)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint para recuperar um AFD armazenado
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
        # método 'accepts_input' para verificar se a string é aceita
        result = afd.accepts_input(input_string)
        return {"input_string": input_string, "accepted": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Função para gerar um diagrama visual do AFD no formato DOT
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
    
    # Adiciona as transições (arestas)
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
