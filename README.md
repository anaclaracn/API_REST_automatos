# API de Manipulação de Autômatos

## 📖 Sobre

Esta API permite criar, testar e visualizar **Autômatos Finitos**, **Autômatos com Pilha (PDA)** e **Máquinas de Turing**.  
Foi desenvolvida com **FastAPI** e utiliza a biblioteca **Automata** para manipulação dos autômatos.

**Nota:** Ao utilizar os endpoints, é necessário especificar o tipo de autômato desejado através do prefixo:  
- `/afd` para Autômatos Finitos  
- `/pilha` para Autômatos com Pilha (PDA)  
- `/turing` para Máquinas de Turing  

Exemplo: Para criar um AFD, utilize o endpoint `afd/create`.

## Configuração e Execução

### 1️⃣ **Pré-requisitos**
- **Python 3.9+** instalado
- **Pip** atualizado
- **Graphviz** instalado (para a visualização dos autômatos)

### 2️⃣ **Instalar dependências**

```bash
pip install -r requirements.txt
pip install fastapi uvicorn automata-lib graphviz
```

### 3️⃣ **Criar e Ativar um Ambiente Virtual**

- **No Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

- **No Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 4️⃣ **Executar o servidor**

```bash
uvicorn main:app --reload
```

### 5️⃣ **Acessar a documentação automática**

- **Swagger UI:** http://127.0.0.1:8000/docs
- **Redoc UI:** http://127.0.0.1:8000/redoc

## 📌 Endpoints da API

### 🔹 **Criar um Autômato**

```http
POST /{tipo}/create
```

Onde `{tipo}` deve ser substituído por `afd`, `pilha` ou `turing`.

Envie um JSON contendo a definição do autômato.

#### Exemplo de Autômato Finito (AFD)

```json
{
  "states": ["q0", "q1"],
  "input_symbols": ["0", "1"],
  "transitions": {
    "q0": { "0": "q0", "1": "q1" },
    "q1": { "0": "q0", "1": "q1" }
  },
  "initial_state": "q0",
  "final_states": ["q1"]
}
```

**Resposta esperada:**

```json
{
  "message": "AFD criado com sucesso!",
  "id": "abc123",
  "automata": {}
}
```

---

### 🔹 **Obter um Autômato pelo ID**

```http
GET /{tipo}/{automata_id}
```

Onde `{tipo}` deve ser substituído por `afd`, `pilha` ou `turing`.

Retorna os detalhes do autômato criado.

---

### 🔹 **Testar uma Entrada**

```http
POST /{tipo}/{automata_id}/test
```

Onde `{tipo}` deve ser substituído por `afd`, `pilha` ou `turing`.

Envie uma string para testar se o autômato a aceita.

#### Exemplo de entrada

```json
{ "input_string": "101" }
```

**Resposta esperada:**

```json
{ "input_string": "101", "accepted": true }
```

---

### 🔹 **Visualizar o Autômato (SVG/PNG)**

```http
GET /{tipo}/{automata_id}/visualize?format=svg
```

Onde `{tipo}` deve ser substituído por `afd`, `pilha` ou `turing`.

Gera um gráfico do autômato em SVG ou PNG.

---

## 📌 Exemplos de Autômatos

### 🔹 **Autômato Finito (AFD)**

_Aceita palavras que terminam em `1`_

```json
{
  "states": ["q0", "q1"],
  "input_symbols": ["0", "1"],
  "transitions": {
    "q0": { "0": "q0", "1": "q1" },
    "q1": { "0": "q0", "1": "q1" }
  },
  "initial_state": "q0",
  "final_states": ["q1"]
}
```

**Testes:**

- Entrada: `{ "input_string": "101" }` → true
- Entrada: `{ "input_string": "100" }` → false

---

### 🔹 **Autômato com Pilha (PDA)**

_Aceita palavras da forma `a^n b^m c^n`, onde `n, m ≥ 1`_

```json
{
  "states": ["q0", "q1", "q2", "q_accept"],
  "input_symbols": ["a", "b", "c"],
  "stack_symbols": ["a", "Z"],
  "transitions": {
    "q0": {
      "a,Z": [["q0", "aZ"]],
      "a,a": [["q0", "aa"]],
      "b,a": [["q1", "a"]],
      "b,Z": [["q1", "Z"]]
    },
    "q1": {
      "b,a": [["q1", "a"]],
      "b,Z": [["q1", "Z"]],
      "c,a": [["q2", ""]]
    },
    "q2": {
      "c,a": [["q2", ""]],
      ",Z": [["q_accept", "Z"]]
    }
  },
  "initial_state": "q0",
  "initial_stack_symbol": "Z",
  "final_states": ["q_accept"]
}
```

**Testes:**

- Entrada: `{ "input_string": "aabcc" }` → true
- Entrada: `{ "input_string": "aabbbc" }` → false

---

### 🔹 **Máquina de Turing**

_Aceita palavras da forma `0^n 1^n`, onde `n ≥ 1`_

```json
{
  "states": ["q0", "q1", "q2", "q3", "q_accept", "q_reject"],
  "input_symbols": ["0", "1"],
  "tape_symbols": ["0", "1", "X", "Y", "_"],
  "transitions": {
    "q0": {
      "X": [["q0", "X", "R"]],
      "Y": [["q0", "Y", "R"]],
      "0": [["q1", "X", "R"]],
      "1": [["q_reject", "1", "R"]],
      "_": [["q3", "_", "R"]]
    },
    "q1": {
      "1": [["q2", "Y", "L"]]
    },
    "q3": {
      "_": [["q_accept", "_", "R"]]
    }
  },
  "initial_state": "q0",
  "blank_symbol": "_",
  "final_states": ["q_accept"]
}
```

**Testes:**

- Entrada: `{ "input_string": "0011" }` → true
- Entrada: `{ "input_string": "000001111" }` → false

---

## 🛠 **Limitações e Pressupostos**

- Apenas autômatos determinísticos são suportados para AFDs.
- Autômatos com pilha e máquinas de Turing, são tratados como não determinísticos.
- A API suporta apenas entrada de texto JSON.
