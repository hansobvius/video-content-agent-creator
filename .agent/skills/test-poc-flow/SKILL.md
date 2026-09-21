---
name: test-poc-flow
description: Guia iterativo para testar o fluxo de PoC (Proof of Concept) do Video Content Agent Creator como um agente Copilot.
---

# Test Proof of Concept (PoC) Flow

Este skill transforma o agente (você) em um **Entrevistador Copilot** que guia o usuário por todo o processo de criação de um `VIDEO_SPEC.yaml` de forma interativa, executa a orquestração e acompanha as revisões.

Sempre que o usuário solicitar para "testar a PoC", "rodar o fluxo de teste", ou acionar a skill `test-poc-flow`, você DEVE seguir estritamente as 4 etapas abaixo na ordem em que aparecem. Não pule etapas.

---

## Etapa 1: Entrevista Interativa (Criação do Briefing)

Você deve conversar com o usuário e fazer perguntas para preencher as seções de um arquivo de configuração yaml. 
**Regra:** Faça as perguntas de forma natural e encadeada. Você pode agrupar algumas (ex: perguntar os detalhes básicos do projeto de uma vez), mas não exija o YAML pronto.

Os campos que você precisa descobrir são:

1. **Projeto:**
   - ID do projeto (`project.id`, ex: "meu-projeto-legal")
   - Título (`project.title`)
2. **Vídeo:**
   - Objetivo (`video.objective`)
   - Público-alvo (`video.audience`)
   - Plataforma (`video.platform`)
   - Idioma (`video.language`)
   - Duração em segundos (`video.duration_seconds`)
   - Proporção/Aspect Ratio (`video.aspect_ratio`)
3. **Estilo:**
   - Tom (`style.tone`)
   - Estilo visual (`style.visual_style`)
   - Complexidade (`style.complexity`)
4. **Conteúdo:**
   - Tópicos obrigatórios (`content.mandatory_topics` - lista de strings)
5. **Restrições:**
   - O que evitar (`constraints.avoid` - lista de strings)

## Etapa 2: Criação do Arquivo

Após coletar todas as informações, avise o usuário que você vai gerar o arquivo.
Crie um arquivo YAML na pasta `api/examples/` (ou na raiz, se preferir) com o nome `{project.id}_spec.yaml`. Utilize exatamente a mesma estrutura do arquivo original `api/examples/VIDEO_SPEC_sample.yaml`.

## Etapa 3: Execução (Mock ou Real)

Pergunte ao usuário se ele deseja rodar no modo `--mock` (offline, sem consumo de tokens) ou modo real (consumindo a API do Gemini).
Uma vez decidido, execute o comando de orquestração via terminal:

```bash
# Exemplo se mock:
python -m api.cli.main run {project.id}_spec.yaml --mock

# Exemplo se real:
python -m api.cli.main run {project.id}_spec.yaml
```

Aguarde o comando finalizar.

## Etapa 4: Revisão e Aprovação

O projeto pausará no estado `AWAITING_APPROVAL`.
Guie o usuário ativamente:

1. Mostre os status dos artefatos:
   ```bash
   python -m api.cli.main status {project.id}
   ```
2. Pergunte ao usuário se ele deseja visualizar o Roteiro (`--type script`) ou o Storyboard (`--type storyboard`) gerados. Se sim, rode o comando:
   ```bash
   python -m api.cli.main show {project.id} --type script
   ```
3. Pergunte se ele gostaria de fazer uma revisão iterativa (ex: "Quer revisar o roteiro ou storyboard apontando alguma mudança de feedback?"). Se sim, rode o comando correspondente:
   ```bash
   python -m api.cli.main revise {project.id} --target [script ou storyboard] --feedback "O que ele pediu"
   ```
   *(Inclua o parâmetro `--mock` se estiver no fluxo de mock)*
4. Uma vez que o usuário estiver satisfeito com os resultados, pergunte se você pode aprovar. Se sim, execute:
   ```bash
   python -m api.cli.main approve {project.id}
   ```

Finalize informando que a PoC foi concluída e o projeto está aprovado!
