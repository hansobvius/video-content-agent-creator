# Sync API Flow Changes to Skills

Quando você (o agente) fizer modificações ou adições no fluxo de processo, na arquitetura ou nos scripts localizados no diretório `api/`, é OBRIGATÓRIO revisar e atualizar as instruções das seguintes skills para garantir que elas reflitam as mudanças recentes:

1. `run-video-agent` (localizada em `.agent/skills/run-video-agent/SKILL.md`)
2. `test-poc-flow` (localizada em `.agent/skills/test-poc-flow/SKILL.md`)

## Por que isso é importante?
As skills `run-video-agent` e `test-poc-flow` contêm o passo-a-passo interativo para testar e executar a PoC. Se a API for alterada (ex: novos endpoints, mudança no formato do payload, novos passos no workflow de geração de vídeo), as skills que descrevem como usar e testar o sistema quebrarão.

## Ação Esperada
Toda vez que você concluir edições no código dentro de `api/` que afetem a lógica de negócios ou a forma como a aplicação é invocada:
1. Abra e leia o arquivo `SKILL.md` das duas skills mencionadas.
2. Atualize os comandos, payloads de exemplo e passos de verificação documentados nas skills para corresponderem ao novo código da API.
3. Se necessário, informe ao usuário sobre as alterações realizadas na documentação dessas skills.
