---
name: run-video-agent
description: Instruções e procedimentos para executar, testar e operar a plataforma Video Content Agent Creator via CLI ou scripts.
---

# Run Video Content Agent Creator

Este guia contém o passo a passo e referências operacionais para executar os agentes de produção de vídeo, gerenciar revisões (Human-in-the-Loop) e rodar testes.

---

## 1. Preparação do Ambiente

### 1.1 Ativação do Ambiente Virtual
Certifique-se de que o ambiente virtual está ativo antes de executar os comandos:

- **Windows PowerShell:**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 1.2 Instalação das Dependências
```bash
pip install -r api/requirements.txt
```

### 1.3 Configuração de Variáveis de Ambiente
Copie o arquivo `.env.example` para `api/.env`:
```powershell
copy api\.env.example api\.env
```

Configurações disponíveis em `api/.env`:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
LLM_MODEL=gemini-2.5-flash
PROJECTS_DIR=projects
```

> **Nota:** Caso execute em modo `--mock`, a chave de API não é obrigatória.

---

## 2. Comandos de Execução (CLI)

A interface CLI principal é acessada através do módulo `api.cli.main`.

### 2.1 Iniciar a Produção de um Vídeo a partir de Briefing (YAML)

- **Modo Mock (Offline / Sem consumo de tokens):**
  ```bash
  python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml --mock
  ```

- **Modo Real (com Google Gemini):**
  ```bash
  python -m api.cli.main run api/examples/VIDEO_SPEC_sample.yaml
  ```

### 2.2 Inspecionar Status e Artefatos Gerados

- **Ver status geral e versões atuais do projeto:**
  ```bash
  python -m api.cli.main status hybrid-car-explainer
  ```

- **Visualizar o Roteiro (Script) formatado:**
  ```bash
  python -m api.cli.main show hybrid-car-explainer --type script
  ```

- **Visualizar o Storyboard com cenas e direção visual:**
  ```bash
  python -m api.cli.main show hybrid-car-explainer --type storyboard
  ```

### 2.3 Solicitar Revisão (Human-in-the-Loop)

- **Revisão de Storyboard (Apenas Direção Visual):**
  *Preserva o roteiro e regenera apenas o storyboard com os ajustes visuais solicitados.*
  ```bash
  python -m api.cli.main revise hybrid-car-explainer --target storyboard --feedback "Na cena 2, mude o tipo de asset para diagram e dê zoom no motor." --mock
  ```

- **Revisão de Roteiro (Texto / Narração):**
  *Atualiza o roteiro e automaticamente regenera o storyboard correspondente.*
  ```bash
  python -m api.cli.main revise hybrid-car-explainer --target script --feedback "A cena 3 está muito longa. Simplifique a narração." --mock
  ```

### 2.4 Aprovar o Projeto

Quando os artefatos estiverem validados e aprovados:
```bash
python -m api.cli.main approve hybrid-car-explainer
```

---

## 3. Execução Direta via Worker (Runtime)

Para rodar o orquestrador diretamente em segundo plano ou via script:

```bash
python -m api.runtime.worker api/examples/VIDEO_SPEC_sample.yaml --mock
```

---

## 4. Testes Automatizados

Para rodar a suíte completa de testes unitários e de integração:

```bash
pytest api/tests -v
```
