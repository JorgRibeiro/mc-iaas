# MC-IaaS Control Hub

Frontend React, TanStack Router e React Query do MC-IaaS Control Plane. Preserva o cliente mock para desenvolvimento visual e usa o backend real por padrão. Todas as chamadas HTTP ficam em `src/services/httpClient.ts`; os adapters traduzem os contratos do backend para os modelos da interface.

## Executar

Use Node.js 22.12+ e npm (validação desta integração feita com Node.js 26.8.1).

```sh
cd control-plane/frontend
npm ci
cp .env.example .env.local
npm run dev -- --host 127.0.0.1 --port 8080
```

Abra `http://127.0.0.1:8080`. O backend deve estar disponível separadamente em `http://127.0.0.1:8001`, com banco, runner e reconciler configurados conforme a documentação do backend.

## Selecionar o cliente

Em `.env.local`:

```dotenv
VITE_CONTROL_PLANE_MODE=http
VITE_CONTROL_PLANE_API_URL=http://127.0.0.1:8001
```

HTTP é o padrão mesmo sem essas variáveis. Para trabalhar sem backend, altere `VITE_CONTROL_PLANE_MODE=mock`. Reinicie o servidor Vite após alterações; em produção, refaça o build. A URL deve apontar para a raiz do Control Plane, sem `/api/v1` no final. O navegador precisa conseguir acessá-la; `127.0.0.1` refere-se à máquina onde o navegador está aberto.

O backend permite CORS explicitamente para `http://localhost:8080` e `http://127.0.0.1:8080`. Para outras origens, ajuste `CORS_ORIGINS` no ambiente do backend como lista JSON e reinicie-o. Não coloque tokens do Compute Agent ou outras credenciais nas variáveis `VITE_*`: elas são públicas no bundle do navegador.

## Comportamento da integração

- Overview, nodes, instances, events e monitoring consultam o Control Plane, com atualização a cada 3 segundos enquanto as respectivas queries estão ativas.
- Refresh Node solicita uma observação pelo Control Plane. O frontend não acessa o Compute Agent diretamente.
- CREATE, START, STOP, RESTART e DELETE aguardam a Operation. As queries são invalidadas na aceitação e ao terminar o acompanhamento. O polling consulta a cada segundo, limitado a 120 tentativas e aproximadamente 2 minutos, com timeout de 10 segundos por requisição.
- `succeeded` confirma a ação; `failed` mostra o erro; `uncertain`, perda de acompanhamento ou prazo excedido mostram aviso sem repetir a mutação automaticamente. O backend pode continuar trabalhando após o fim do acompanhamento.
- CREATE envia apenas nome, memória, vCPU, versão Minecraft, usuário da VM e aceite explícito da EULA. O Scheduler escolhe o node; não há manipulação de passwords.
- Campos não fornecidos pelo backend aparecem como indisponíveis. CPU, memória, disco MC-IaaS, uptime e health por componente usam a última observação persistida. Memória converte bytes para MiB/GiB (base 1024); storage usa GB (base 1000). Root disk, load averages e métricas por Instance continuam indisponíveis nesta projeção. Não há histórico nem console remoto.
- Overview agrega apenas nodes online com observações recentes: média simples de CPU e soma de pares used/total de memória e storage. Sem observações válidas, retorna null. Nodes offline preservam as últimas métricas e exibem o status offline e a idade da observação.
- Activity consulta os últimos 100 eventos, com filtro de nível na API. Não há paginação nesta interface.
- Settings mantém preferências apenas em memória, sem persistência e sem reconfigurar o backend ou os intervalos das queries. O card de conexão consulta `/health` e `/ready`.

## Verificação

```sh
npx tsc --noEmit
npm run lint
npm test
npm run build
```

Os testes usam o runner nativo do Node.js e cobrem adapters, contratos HTTP, erros e acompanhamento limitado de Operations. Eles não criam workloads reais. Para testar lifecycle manualmente, use o modo HTTP com um Compute Node pronto e acompanhe as confirmações na interface.
