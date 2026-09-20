# 🎬 Video Content Agent Creator (MVP 1)

Uma plataforma orientada a agentes de inteligência artificial projetada para transformar briefings estruturados de vídeo em **planos de produção audiovisual determinísticos, versionados e aprovados por humanos**.

---

## 📌 Visão Geral do MVP 1

O **MVP 1** foca na etapa de planejamento pré-produção, eliminando o trabalho manual de transformar uma ideia em cenas e diretrizes visuais. Ele gera contratos estruturados (JSON e Markdown) que servirão de insumo direto para os futuros agentes de geração de imagem, voz e renderização de vídeo.

### 🔄 Fluxo de Execução e Arquitetura:

```text
               ┌──────────────────────┐
               │   VIDEO_SPEC.yaml    │
               └──────────┬───────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │ VideoProductionAgent │
               │     Orquestrador     │
               └──────────┬───────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       ┌─────────────┐        ┌───────────────┐
       │ ScriptAgent │        │ State Manager │
       └──────┬──────┘        └───────────────┘
              │
              ▼
       ┌─────────────────┐
       │ StoryboardAgent │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Human Approval  │
       └───────┬─────────┘
               │
   ┌───────────┼──────────────────────┐
   │           │                      │
   ▼           ▼                      ▼
APPROVED   REVISÃO (Roteiro)     REVISÃO (Storyboard)
               │                      │
               ▼                      ▼
          ScriptAgent           StoryboardAgent
               │                      │
               ▼                      │
        StoryboardAgent               │
               │                      │
               └──────────┬───────────┘
                          │
                          ▼
                    Human Approval
```

---

## 🗂️ Estrutura do Repositório

```text
video-content-agent-creator/
├── api/                           # Código-fonte da aplicação
│   ├── agents/                    # Agentes de IA e Orquestrador
│   │   ├── orchestrator/          # VideoProductionAgent (controle de fluxo e revisão)
│   │   ├── script/                # ScriptAgent (geração e revisão de roteiro)
│   │   └── storyboard/            # StoryboardAgent (geração e direção visual)
│   ├── domain/                    # Modelos Pydantic v2 (contratos de dados estritos)
│   ├── services/                  # Serviços determinísticos (arquivos, estado, aprovação, LLM)
│   ├── prompts/                   # Templates de prompts desacoplados do código
│   ├── runtime/                   # Worker para execuções em segundo plano
│   ├── cli/                       # Interface de linha de comando (Typer + Rich)
│   ├── examples/                  # Briefings de exemplo (VIDEO_SPEC_sample.yaml)
│   └── tests/                     # Suíte de testes automatizados
├── docs/                          # Documentação técnica e plano arquitetural
├── projects/                      # Diretório de armazenamento persistente dos projetos gerados
├── pyproject.toml                 # Configurações do pacote Python
├── README.md                      # Este documento
└── .gitignore
```

---

## ⚙️ Pré-requisitos e Instalação

* **Python:** Versão 3.11 ou superior
* **Chave de API:** Google Gemini API Key (opcional caso queira executar apenas em modo `--mock`)

### 1. Clonar o repositório e criar o ambiente virtual

No terminal (PowerShell no Windows ou Bash no Linux/macOS):

```bash
# Criar o ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows PowerShell):
.venv\Scripts\Activate.ps1

# Ativar o ambiente virtual (Linux / macOS):
source .venv/bin/activate

# Instalar as dependências do projeto:
pip install -r api/requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo para `.env`:

```bash
cp api/.env.example api/.env
```

Edite o arquivo `api/.env` com a sua chave da Google Gemini:

```env
GEMINI_API_KEY=sua_chave_gemini_aqui
LLM_MODEL=gemini-2.5-flash
PROJECTS_DIR=projects
```

---

## 🚀 Como Executar

A plataforma possui uma CLI completa e intuitiva construída com **Typer** e **Rich**.

### 1. Iniciar a Produção a partir de um Briefing

Você pode rodar com a API do Gemini ou usar o flag `--mock` para testar offline sem consumir tokens:

```bash
# Execução com IA (Gemini):
python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml

# Execução em Modo Mock (Offline):
python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml --mock
```

O orquestrador executará a validação do briefing, gerará o roteiro `v1`, o storyboard `v1` e pausará no estado `AWAITING_APPROVAL`.

---

### 2. Inspecionar o Projeto Gerado

```bash
# Ver tabela com status, versões e caminhos dos artefatos:
python -m api.cli.main status hybrid-car-explainer

# Exibir o Roteiro formatado no terminal:
python -m api.cli.main show hybrid-car-explainer --type script

# Exibir o Storyboard com tabela de cenas e diretrizes de câmera:
python -m api.cli.main show hybrid-car-explainer --type storyboard
```

---

### 3. Solicitar Revisões Granulares (Human-in-the-Loop)

O sistema suporta dois tipos de revisão sem perda de histórico:

#### A) Revisão de Storyboard (Apenas Direção Visual):
Preserva o roteiro aprovado e regenera somente o storyboard com as novas diretrizes visuais:
```bash
python -m api.cli.main revise hybrid-car-explainer --target storyboard --feedback "Na cena 2, mude o tipo de asset para diagram e dê zoom no motor elétrico" --mock
```

#### B) Revisão de Roteiro (Texto / Conteúdo):
Altera a narração/estrutura narrativa e regenera automaticamente o storyboard correspondente:
```bash
python -m api.cli.main revise hybrid-car-explainer --target script --feedback "A explicação da cena 3 está muito complexa. Simplifique a linguagem." --mock
```

---

### 4. Aprovar o Plano de Produção

Após revisar os artefatos, aprove o projeto para finalizar a etapa do MVP 1:

```bash
python -m api.cli.main approve hybrid-car-explainer
```

---

### 5. Execução Direta via Worker

Caso deseje executar o orquestrador via script tradicional:

```bash
python -m api.runtime.worker api/examples/VIDEO_SPEC_sample.yaml --mock
```

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte de testes com cobertura para validação de esquemas Pydantic, isolamento de versionamento sem sobrescrita, transições de estado e fluxo de ponta a ponta:

```bash
pytest api/tests -v
```

---

## 🔮 Próximos Passos (Roadmap MVP 2)

Com os contratos estruturados e o plano aprovado no MVP 1, os próximos módulos consumirão diretamente os artefatos gerados:
* **Visual Agent:** Geração de imagens e vídeos via modelos generativos a partir das descrições do `storyboard.json`.
* **Voice Agent:** Síntese de voz neural (TTS) para narração a partir do `script.json`.
* **Assembly Agent:** Composição e sincronização audiovisual automatizada utilizando FFmpeg.
