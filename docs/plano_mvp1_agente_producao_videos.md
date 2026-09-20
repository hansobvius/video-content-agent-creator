# Plano de Desenvolvimento — MVP 1 do Agente de Produção de Vídeos

## 1. Objetivo

Construir o primeiro MVP de uma plataforma baseada em agentes de IA para apoiar a criação de vídeos a partir de um briefing estruturado.

O MVP 1 terá como objetivo transformar uma especificação inicial de vídeo em:

1. um roteiro estruturado por cenas;
2. um storyboard textual;
3. um plano de produção;
4. um ponto de aprovação humana antes da geração de imagens, áudio ou vídeo.

O fluxo principal será:

```text
VIDEO_SPEC
    ↓
VideoProductionAgent
    ↓
ScriptAgent
    ↓
StoryboardAgent
    ↓
Human Review
    ↓
APPROVED / REJECTED
```

Este MVP não realizará geração de imagens, vídeos, áudio, legendas ou renderização final.

---

## 2. Problema que o MVP resolve

Na produção tradicional de vídeos, uma ideia inicialmente pouco estruturada precisa ser convertida manualmente em roteiro, cenas e instruções visuais.

O MVP 1 automatizará essa transformação.

Entrada:

```text
"Quero um vídeo de cinco minutos explicando como funciona um veículo híbrido."
```

Saída esperada:

```text
VIDEO_SPEC
    ↓
roteiro
    ↓
cenas
    ↓
descrição visual
    ↓
duração estimada
    ↓
storyboard
```

O resultado será um pacote estruturado pronto para alimentar, futuramente, agentes de geração de imagem, vídeo, narração e edição.

---

## 3. Escopo do MVP 1

### Incluído

- definição de um `VIDEO_SPEC`;
- validação do briefing;
- agente orquestrador;
- geração de roteiro;
- divisão do roteiro em cenas;
- estimativa de duração;
- descrição visual de cada cena;
- criação do storyboard textual;
- criação de plano de produção;
- persistência dos artefatos;
- versionamento dos artefatos;
- etapa de aprovação humana;
- possibilidade de solicitar revisão do roteiro;
- logs básicos da execução.

### Fora do escopo

Neste MVP não serão implementados:

- geração de imagens;
- geração de vídeos;
- geração de voz;
- geração automática de legendas;
- edição automática;
- uso de FFmpeg;
- geração de trilha sonora;
- publicação em YouTube, TikTok ou Instagram;
- Quality Agent multimodal;
- renderização final.

Esses componentes serão adicionados nos MVPs posteriores.

---

# 4. Arquitetura conceitual

```text
                   ┌──────────────────────┐
                   │      VIDEO_SPEC      │
                   └──────────┬───────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ VideoProductionAgent │
                   │    Orchestrator      │
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
   APPROVED   REVISION (Script)      REVISION (Storyboard)
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

# 5. Componentes

## 5.1 VideoProductionAgent

Responsável pela orquestração do processo.

Principais responsabilidades:

- carregar o `VIDEO_SPEC`;
- validar se os dados obrigatórios existem;
- iniciar o `ScriptAgent`;
- persistir o roteiro;
- iniciar o `StoryboardAgent`;
- persistir o storyboard;
- atualizar o estado do projeto;
- interromper o pipeline na etapa de aprovação;
- rotear granularmente as revisões solicitadas:
  - se a revisão for de roteiro (`target: script`), re-executar `ScriptAgent` e subsequentemente o `StoryboardAgent`;
  - se a revisão for exclusivamente visual (`target: storyboard`), re-executar apenas o `StoryboardAgent`, preservando a versão do roteiro já aprovada.

O agente orquestrador não deverá escrever diretamente o roteiro ou storyboard.

Sua responsabilidade principal será controlar o workflow.

---

## 5.2 ScriptAgent

Responsável pela construção do roteiro.

Entradas:

```text
VIDEO_SPEC
```

Saídas:

```text
script.json
script.md
```

O roteiro deverá ser dividido em cenas.

Cada cena deverá possuir pelo menos:

```json
{
  "scene_id": "scene_001",
  "title": "Introdução",
  "duration_seconds": 10,
  "narration": "Texto da narração.",
  "objective": "Apresentar o assunto do vídeo.",
  "visual_intent": "Veículo em destaque enquanto os principais componentes aparecem."
}
```

Responsabilidades:

- interpretar o briefing;
- definir uma estrutura narrativa;
- dividir o conteúdo em cenas;
- gerar narração;
- estimar duração;
- manter coerência entre as cenas;
- respeitar público, objetivo e formato definidos no `VIDEO_SPEC`.

---

## 5.3 StoryboardAgent

Responsável por transformar o roteiro em um plano visual.

Entrada:

```text
script.json
```

Saídas:

```text
storyboard.json
storyboard.md
```

Exemplo de cena:

```json
{
  "scene_id": "scene_003",
  "duration_seconds": 15,
  "narration": "A bateria fornece energia para o motor elétrico.",
  "visual_description": "Diagrama lateral de um veículo mostrando o fluxo de energia da bateria para o motor.",
  "camera": "static",
  "transition": "fade",
  "asset_type": "illustration"
}
```

O `asset_type` será importante para os próximos MVPs.

Valores inicialmente suportados:

```text
illustration
image
video
diagram
text_animation
stock
```

Nenhum desses assets será gerado no MVP 1.

---

# 6. VIDEO_SPEC

O `VIDEO_SPEC` será a fonte de verdade da produção.

Formato recomendado:

```yaml
project:
  id: "hybrid-car-explainer"
  title: "Como funciona um carro híbrido"

video:
  objective: "Explicar o funcionamento básico de um veículo híbrido"
  audience: "Público geral sem conhecimento técnico"
  platform: "YouTube"
  language: "pt-BR"
  duration_seconds: 300
  aspect_ratio: "16:9"

style:
  tone: "educacional"
  visual_style: "moderno e didático"
  complexity: "iniciante"

content:
  mandatory_topics:
    - motor elétrico
    - motor a combustão
    - bateria
    - frenagem regenerativa
    - modo EV
    - modo híbrido

constraints:
  avoid:
    - linguagem excessivamente técnica
    - informações não verificadas
```

---

# 7. Validação do VIDEO_SPEC

Antes da geração do roteiro, o sistema deverá verificar:

```text
project.id
project.title
video.objective
video.audience
video.language
video.duration_seconds
style.tone
```

Caso algum campo obrigatório esteja ausente, o pipeline deverá retornar:

```json
{
  "status": "INVALID_SPEC",
  "missing_fields": [
    "video.audience"
  ]
}
```

Nenhum agente deverá ser executado enquanto o `VIDEO_SPEC` estiver inválido.

---

# 8. Estado do projeto

O pipeline deverá possuir um estado persistente.

Exemplo:

```json
{
  "project_id": "hybrid-car-explainer",
  "status": "AWAITING_APPROVAL",
  "current_stage": "storyboard",
  "versions": {
    "script": 2,
    "storyboard": 3
  },
  "artifacts": {
    "spec": "VIDEO_SPEC.yaml",
    "script": "scripts/script_v2.json",
    "storyboard": "storyboards/storyboard_v3.json"
  }
}
```

Estados sugeridos:

```text
CREATED
SPEC_VALIDATED
SCRIPT_GENERATING
SCRIPT_COMPLETED
STORYBOARD_GENERATING
STORYBOARD_COMPLETED
AWAITING_APPROVAL
REVISION_SCRIPT_REQUESTED
REVISION_STORYBOARD_REQUESTED
APPROVED
FAILED
```

---

# 9. Human in the Loop

O MVP deverá obrigatoriamente parar antes da etapa de produção audiovisual.

O usuário poderá executar ações de aprovação ou revisão granular:

## Aprovar

```text
approve
```

Resultado:

```json
{
  "status": "APPROVED"
}
```

---

## Solicitar revisão granular

O usuário poderá direcionar o feedback especificando o alvo da revisão (`target: script` ou `target: storyboard`):

### Cenário 1: Revisão de Roteiro (`target: script`)

Utilizado quando há necessidade de alterar o texto da narração, tom, divisão das cenas ou objetivos narrativos.

Exemplo de feedback:

```json
{
  "target": "script",
  "feedback": "A cena 4 está muito técnica. Simplifique a explicação."
}
```

O sistema deverá:

```text
1. registrar o feedback em feedback/revision_XXX.json;
2. incrementar a versão do roteiro (ex: script_v2);
3. executar novamente o ScriptAgent;
4. incrementar a versão do storyboard (ex: storyboard_v2);
5. executar o StoryboardAgent para refletir o novo roteiro;
6. retornar para o estado AWAITING_APPROVAL.
```

Fluxo:

```text
Storyboard v1 (Awaiting Approval)
      ↓
Revision Request (target: script)
      ↓
Script v2
      ↓
Storyboard v2
      ↓
Human Review (Awaiting Approval)
```

---

### Cenário 2: Revisão de Storyboard (`target: storyboard`)

Utilizado quando o texto narrativo do roteiro já está satisfatório, mas as instruções visuais (tipo de asset, enquadramento de câmera, transição ou descrição da cena) precisam ser corrigidas.

Exemplo de feedback:

```json
{
  "target": "storyboard",
  "feedback": "Na cena 3, mude o asset_type para 'diagram' e mostre um corte esquemático do motor."
}
```

O sistema deverá:

```text
1. registrar o feedback em feedback/revision_XXX.json;
2. preservar intacta a versão atual do roteiro (ex: mantém script_v1);
3. incrementar apenas a versão do storyboard (ex: storyboard_v2);
4. executar apenas o StoryboardAgent com o feedback visual aplicado;
5. retornar para o estado AWAITING_APPROVAL.
```

Fluxo:

```text
Storyboard v1 (Awaiting Approval)
      ↓
Revision Request (target: storyboard)
      ↓
(Script v1 preservado)
      ↓
Storyboard v2
      ↓
Human Review (Awaiting Approval)
```

Essa granularidade evita a perda de roteiros já aprovados e reduz o custo/tempo de re-execução do modelo desnecessariamente.

---

# 10. Versionamento

Todos os artefatos produzidos por IA devem ser versionados.

Exemplo:

```text
scripts/
    script_v1.json
    script_v1.md
    script_v2.json
    script_v2.md

storyboards/
    storyboard_v1.json
    storyboard_v1.md
    storyboard_v2.json
    storyboard_v2.md
```

Nunca sobrescrever diretamente o artefato anterior.

Isso permitirá:

- auditoria;
- comparação;
- rollback;
- análise de qualidade;
- reprodução de execuções.

---

# 11. Estrutura inicial do projeto

```text
ai-video-agent/
│
├── agents/
│   ├── orchestrator/
│   │   ├── agent.py
│   │   └── instructions.md
│   │
│   ├── script/
│   │   ├── agent.py
│   │   └── instructions.md
│   │
│   └── storyboard/
│       ├── agent.py
│       └── instructions.md
│
├── domain/
│   ├── video_spec.py
│   ├── script.py
│   ├── storyboard.py
│   └── project_state.py
│
├── services/
│   ├── project_service.py
│   ├── artifact_service.py
│   └── approval_service.py
│
├── runtime/
│   └── worker.py
│
├── projects/
│   └── .gitkeep
│
├── prompts/
│   ├── script_agent.md
│   └── storyboard_agent.md
│
├── tests/
│
├── pyproject.toml
├── .env.example
├── README.md
└── SPEC.md
```

---

# 12. Estrutura de um projeto de vídeo

Após criar um projeto:

```text
projects/
└── hybrid-car-explainer/
    │
    ├── VIDEO_SPEC.yaml
    │
    ├── state.json
    │
    ├── scripts/
    │   ├── script_v1.json
    │   └── script_v1.md
    │
    ├── storyboards/
    │   ├── storyboard_v1.json
    │   └── storyboard_v1.md
    │
    ├── feedback/
    │   └── revision_001.json
    │
    └── logs/
        └── execution.log
```

---

# 13. Separação entre Agent e Tool

O projeto deve manter agentes e operações determinísticas separados.

Exemplo:

```text
Agent
    ↓
"Preciso salvar a nova versão do roteiro."

Tool / Service
    ↓
ArtifactService.save_script()
```

O agente decide.

O serviço executa.

Exemplos de serviços:

```text
ArtifactService
ProjectService
ApprovalService
StateService
```

Isso facilitará a inclusão dos futuros componentes:

```text
ImageGenerationTool
VideoGenerationTool
VoiceGenerationTool
FFmpegTool
PublishingTool
```

---

# 14. Contratos estruturados

Sempre que possível, a comunicação entre agentes deverá utilizar objetos estruturados em vez de texto livre.

Exemplo:

```python
class Scene:
    id: str
    title: str
    duration_seconds: int
    narration: str
    objective: str
    visual_intent: str
```

Isso permitirá validar automaticamente a saída do modelo.

Sugestão para Python:

```text
Pydantic
```

Fluxo:

```text
LLM
 ↓
JSON
 ↓
Pydantic Validation
 ↓
Domain Object
```

Se a resposta não respeitar o schema:

```text
Retry / Correction
```

---

# 15. Estratégia de prompts

Os prompts dos agentes deverão ficar fora do código.

Exemplo:

```text
prompts/
    script_agent.md
    storyboard_agent.md
```

O prompt deverá definir:

```text
Role
Objective
Inputs
Rules
Output schema
Constraints
Examples
```

Isso permitirá modificar o comportamento do agente sem alterar código.

---

# 16. Observabilidade mínima

Cada execução deverá registrar:

```text
project_id
agent
timestamp
input_artifact
output_artifact
model
execution_status
duration
error
```

Exemplo:

```json
{
  "project_id": "hybrid-car-explainer",
  "agent": "ScriptAgent",
  "model": "MODEL_NAME",
  "status": "SUCCESS",
  "input": "VIDEO_SPEC.yaml",
  "output": "script_v1.json"
}
```

No MVP 1, logs em arquivo já são suficientes.

Posteriormente poderão ser enviados para:

```text
CloudWatch
OpenTelemetry
Langfuse
MLflow
ou outra plataforma de observabilidade.
```

---

# 17. Estratégia de testes

## Testes unitários

Testar principalmente componentes determinísticos.

Exemplos:

```text
VIDEO_SPEC validation
state transitions
artifact versioning
project creation
approval workflow
revision workflow
```

---

## Testes de contrato

Validar se as respostas dos agentes respeitam os schemas esperados.

Exemplo:

```text
ScriptAgentOutput
StoryboardAgentOutput
```

---

## Testes de integração

Fluxo mínimo:

```text
VIDEO_SPEC
    ↓
ScriptAgent
    ↓
StoryboardAgent
    ↓
AWAITING_APPROVAL
```

Critério:

```text
Todos os artefatos devem existir e possuir referências válidas no state.json.
```

---

# 18. Critérios de aceite do MVP 1

O MVP será considerado concluído quando for possível executar:

```bash
python runtime/worker.py VIDEO_SPEC.yaml
```

e obter:

```text
1. validação do VIDEO_SPEC;
2. roteiro estruturado;
3. roteiro salvo em JSON e Markdown;
4. storyboard estruturado;
5. storyboard salvo em JSON e Markdown;
6. state.json atualizado;
7. pipeline pausado em AWAITING_APPROVAL.
```

Também deverá ser possível executar as ações:

```text
approve
```

ou:

```text
revision (com target: script ou target: storyboard)
```

Uma revisão deverá produzir novas versões dos artefatos afetados sem excluir versões anteriores e sem re-executar etapas desnecessárias (ex: revisão de storyboard mantém o roteiro existente).

---

# 19. Roadmap de implementação

## Etapa 1 — Domínio

Criar:

```text
VideoSpec
Scene
Script
Storyboard
ProjectState
```

Objetivo:

ter contratos claros antes da implementação dos agentes.

---

## Etapa 2 — Project Runtime

Implementar:

```text
ProjectService
ArtifactService
StateService
```

Objetivo:

criar, salvar e versionar projetos.

---

## Etapa 3 — ScriptAgent

Implementar:

```text
VIDEO_SPEC
     ↓
ScriptAgent
     ↓
script.json
```

Validar a saída através do schema.

---

## Etapa 4 — StoryboardAgent

Implementar:

```text
script.json
     ↓
StoryboardAgent
     ↓
storyboard.json
```

Validar também através de schema.

---

## Etapa 5 — Orquestrador

Implementar:

```text
VideoProductionAgent
```

Responsável por executar:

```text
validate
   ↓
script
   ↓
storyboard
   ↓
approval
```

---

## Etapa 6 — Human Approval

Criar comandos:

```text
approve
revision (target: script | storyboard)
```

Persistir feedback.

---

## Etapa 7 — Testes

Adicionar:

```text
unit tests
contract tests
integration tests
```

---

# 20. Ordem recomendada de desenvolvimento

```text
1. VIDEO_SPEC schema
2. Domain models
3. State machine
4. Artifact versioning
5. ScriptAgent
6. StoryboardAgent
7. Orchestrator
8. Human approval (com suporte a target de revisão)
9. Revision workflow (granular)
10. Integration tests
```

Essa ordem reduz dependências entre componentes e evita começar pelo LLM antes de definir os contratos do sistema.

---

# 21. Definition of Done

O MVP 1 estará pronto quando:

- [ ] existir um `VIDEO_SPEC` validado;
- [ ] o projeto puder ser iniciado via CLI;
- [ ] o ScriptAgent gerar um roteiro estruturado;
- [ ] o StoryboardAgent gerar um storyboard estruturado;
- [ ] cada artefato tiver versão;
- [ ] o estado do projeto for persistido;
- [ ] o pipeline parar aguardando aprovação;
- [ ] for possível aprovar;
- [ ] for possível solicitar revisão granular (revisar roteiro + storyboard ou apenas storyboard);
- [ ] revisões gerarem novas versões mantendo o histórico;
- [ ] existirem testes básicos;
- [ ] existirem logs de execução;
- [ ] nenhuma etapa dependa de geração audiovisual.

---

# 22. Resultado esperado do MVP 1

Ao final do MVP, a plataforma deverá transformar:

```text
Ideia
```

em:

```text
Briefing estruturado
        ↓
Roteiro estruturado
        ↓
Storyboard estruturado
        ↓
Plano de produção aprovado
```

O produto principal do MVP não será um vídeo.

Será um **plano de produção audiovisual estruturado, versionado e pronto para execução por agentes especializados**.

---

# 23. Evolução para o MVP 2

O MVP 2 poderá consumir diretamente os artefatos produzidos neste MVP.

Arquitetura futura:

```text
MVP 1
────────────────────────

VIDEO_SPEC
    ↓
ScriptAgent
    ↓
StoryboardAgent
    ↓
Human Approval

────────────────────────
            ↓
          MVP 2
────────────────────────

    ┌───────┼────────┐
    ▼       ▼        ▼
 Visual   Voice    Assets
 Agent    Agent     Agent
```

Por esse motivo, os contratos definidos no MVP 1 deverão ser tratados como uma API interna do pipeline de produção.
