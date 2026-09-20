# Video Content Agent Creator (MVP 1)

Plataforma baseada em agentes de IA para transformar especificações de vídeo estruturadas (`VIDEO_SPEC.yaml`) em roteiros e storyboards textuais versionados, com Human-in-the-Loop e suporte a revisões granulares.

---

## 🚀 Instalação e Configuração

### 1. Criar ambiente virtual e instalar dependências

```bash
# Na pasta raiz do projeto ou em api/
python -m venv .venv

# No Windows PowerShell:
.venv\Scripts\Activate.ps1

# Instalar dependências:
pip install -r api/requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo:

```bash
cp api/.env.example api/.env
```

Edite o arquivo `.env` e preencha sua `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=sua_chave_gemini_aqui
LLM_MODEL=gemini-2.5-flash
PROJECTS_DIR=projects
```

---

## 💻 Uso via CLI

A CLI `video-agent` oferece comandos interativos para todo o ciclo de vida da produção:

### 1. Executar o Pipeline a partir do Briefing

```bash
# Com API do Gemini
python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml

# Ou em modo offline/mock (sem consumir créditos de API)
python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml --mock
```

### 2. Inspecionar Status e Artefatos Gerados

```bash
# Ver tabela com status atual do projeto
python -m api.cli.main status hybrid-car-explainer

# Visualizar o roteiro formatado
python -m api.cli.main show hybrid-car-explainer --type script

# Visualizar o storyboard formatado
python -m api.cli.main show hybrid-car-explainer --type storyboard
```

### 3. Solicitar Revisão Granular (Human-in-the-Loop)

#### Revisão de Roteiro (altera texto e regenera storyboard):
```bash
python -m api.cli.main revise hybrid-car-explainer --target script --feedback "A cena 3 está muito longa. Simplifique a narração." --mock
```

#### Revisão de Storyboard (preserva o roteiro e ajusta apenas a direção visual):
```bash
python -m api.cli.main revise hybrid-car-explainer --target storyboard --feedback "Na cena 2, mude o tipo de asset para diagram e aplique zoom no motor." --mock
```

### 4. Aprovar o Projeto

```bash
python -m api.cli.main approve hybrid-car-explainer
```

---

## 🧪 Testes Automatizados

Para rodar todos os testes unitários e de integração:

```bash
pytest api/tests -v
```
