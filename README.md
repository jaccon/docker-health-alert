# Docker Monitor

Simples e objetivo: monitor para containers Docker que registra uso de CPU, memória e rede e dispara alertas (opcionalmente via Telegram).

## Onde fica a configuração
- Coloque as configurações em `config.json` na mesma pasta do script `_monitor.py`.
- Campos importantes:
  - `thresholds`: limites para `cpu` (em %), `memory_gb`, `network_mbps`.
  - `monitoring.interval_seconds`: intervalo entre leituras.
  - `monitoring.alert_cooldown_minutes`: tempo mínimo entre alertas para o mesmo recurso/container.
  - `logging`: `log_file`, `log_level`, `max_bytes_mb`, `backup_count`.
  - `daemon.pid_file`: caminho do arquivo PID quando em modo daemon.
  - `telegram`: `{ "enabled": false, "bot_token": "", "chat_id": "" }` — habilite e preencha para receber alertas.

## Uso rápido
Na pasta do projeto execute:

```bash
# executar uma iteração e sair (ver saída em console)
python3 _monitor.py --once

# rodar em background (daemon)
python3 _monitor.py --daemon-mode

# parar o daemon (usa o pid do arquivo configurado em config.json)
python3 _monitor.py --stop

# checar status do daemon
python3 _monitor.py --status
```

## Alertas por Telegram
- No `config.json` defina:

```json
"telegram": {
  "enabled": true,
  "bot_token": "123456:ABC-DEF",
  "chat_id": "-1001234567890"
}
```

- Quando um container exceder thresholds e cooldown permitir, o daemon enviará uma mensagem simples ao chat configurado.

## Logs
- Se `logging.log_file` estiver configurado, o monitor escreve logs rotativos nesse arquivo.
- As mensagens de alerta também vão para o log.

## Requisitos
- Python 3.8+ e o pacote `docker` instalado no ambiente que executa o script.

Instale dependências (ex.):

```bash
python3 -m pip install -r requirements.txt
# ou
python3 -m pip install docker
```

## Observações
- O script lê sempre `config.json` ao lado de `_monitor.py` (não é preciso passar caminho).
- `--daemon-mode` é a flag principal para rodar em background; `--stop` e `--status` permitem controle do processo.

---
Feito para ser minimalista — se quiser, atualizo com exemplos de `config.json` ou unit tests.
# Docker Monitor

Um monitor avançado de recursos Docker em tempo real com alertas e logging.

## Versões Disponíveis

### Docker Monitor Completo (`_monitor.py`)
- 📊 Interface visual rica com barras de progresso animadas
- 🎨 Separadores visuais entre containers
- 📈 Atualização visual em tempo real
- **Uso recomendado**: Desenvolvimento local e monitoramento interativo

### Docker Monitor Lite (`_monitor_lite.py`) 
- ⚡ **Otimizado para servidor** - baixo consumo de CPU e memória
- 📝 Saída em texto simples (opcional)
- 🚀 Intervalo padrão maior (5s vs 2s)
- 💾 Sem barras de progresso que consomem recursos
- **Uso recomendado**: Produção, servidores, monitoramento contínuo

### Script Unificado (`monitor.py`)
- 🔄 Permite escolher entre as versões facilmente
- 📋 Interface única para ambas as versões

## Funcionalidades

- 📊 Monitoramento em tempo real de CPU, Memória e Rede
- 🚨 Sistema de alertas para recursos > 50%
- 📝 Logging para arquivo
- 📈 Ordenação automática por uso de CPU
- 🎯 Interface visual com barras de progresso
- ⏱️ Cooldown de alertas para evitar spam

## Instalação

```bash
# Instalar dependências
pip install docker tqdm

# Ou usar o ambiente virtual já configurado
source .venv/bin/activate
```

## Uso

### Versão Lite (Recomendada para Servidor)

#### Monitoramento silencioso (apenas alertas)
```bash
python _monitor_lite.py --alerts --log-file /var/log/docker_monitor.log
```

#### Monitoramento com saída visual simples
```bash
python _monitor_lite.py --alerts --visual --log-file monitor.log
```

#### Personalizar intervalo (10s para servidor)
```bash
python _monitor_lite.py --alerts --interval 10 --log-file monitor.log
```

### Versão Completa (Para desenvolvimento local)

#### Monitoramento visual completo
```bash
python _monitor.py
```

#### Com alertas e logging
```bash
python _monitor.py --alerts --log-file monitor.log
```

### Script Unificado

#### Versão lite
```bash
python monitor.py --lite --alerts --log-file monitor.log
```

#### Versão completa
```bash
python monitor.py --alerts --log-file monitor.log
```

### Executar em background (para servidor)
```bash
# Versão lite para servidor (recomendado)
nohup python _monitor_lite.py --alerts --log-file /var/log/docker_monitor.log --interval 10 &

# Com systemd (criar service)
sudo systemctl enable docker-monitor.service
sudo systemctl start docker-monitor.service
```

## Configuração de Alertas

### Thresholds padrão:
- **CPU**: > 50%
- **Memória**: > 4GB (50% de 8GB)
- **Rede**: > 5MB/s (50% de 10MB/s)

### Cooldown:
- **5 minutos** entre alertas do mesmo tipo para o mesmo container

## Parâmetros da linha de comando

```
--alerts          Habilitar sistema de alertas
--log-file FILE   Arquivo para salvar logs
--interval N      Intervalo de atualização (segundos, padrão: 2)
--help           Mostrar ajuda
```

## Formato dos Logs

```
2025-09-21 14:30:15 - INFO - 🚀 Docker Monitor iniciado com alertas habilitados
2025-09-21 14:30:15 - INFO - ⚙️  Thresholds: CPU>50.0%, MEM>4.0GB, NET>5.0MB/s
# Docker Monitor

Monitor leve para containers Docker com alertas e saída em colunas (baixo consumo de CPU).

Este projeto fornece dois scripts principais:

- `_monitor.py` — monitor em tempo real de containers Docker que exibe consumo em colunas e envia alertas via Telegram quando um recurso fica acima do threshold por um período sustentado.
- `_stressTest.py` — utilitário para gerar carga HTTP; possui modo `--paranoid` (usa todos os núcleos) e permite parar com a tecla `S`.

## Requisitos

- Python 3.8+
- Pacotes Python: `docker`, `requests`. (`tqdm` é usado pelo stress test se desejar progress bar)

Instalação rápida
-----------------

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install docker requests tqdm
```

## Configuração (`config.json`)

As configurações ficam no arquivo `config.json` ao lado de `_monitor.py`.

Chaves importantes:

- `thresholds`:
  - `cpu`: % de CPU que inicia a observação (ex.: `50.0`)
  - `memory_gb`: GB de memória que inicia a observação (ex.: `4.0`)
  - `network_mbps`: MB/s que inicia a observação (ex.: `5.0`)

- `monitoring`:
  - `interval_seconds`: intervalo entre leituras (recomendado 2–10s)
  - `alert_cooldown_minutes`: minutos de cooldown entre alertas do mesmo tipo
  - `sustained_seconds`: segundos que o recurso precisa se manter acima do threshold antes de disparar o alerta (evita falsos positivos). Padrão: `20`.

- `telegram`:
  - `enabled`: `true`/`false`
  - `bot_token`: token do bot Telegram
  - `chat_id`: id do chat para receber mensagens

Exemplo (trecho):

```json
"monitoring": {
  "interval_seconds": 10,
  "alert_cooldown_minutes": 5,
  "sustained_seconds": 20
}
```

## Uso do monitor (`_monitor.py`)

Executar o monitor interativo:

```bash
python3 _monitor.py
```

O monitor imprimirá uma tabela limpa (clear screen) com as colunas:

```
CONTAINER                       CPU%   MEM(GB)     NET(B/s)
my_service                      72.50    1.23         12345
another_service                 12.00    0.50          5432
```

Ordenação: por CPU decrescente (containers que mais consomem aparecem primeiro).

Alertas
-------

- Um alerta é enviado apenas quando uma métrica permanece acima do threshold por pelo menos `sustained_seconds` consecutivos.
- Mensagem do Telegram (header + status):

```
### DOCKER-MONITOR ###
ALERT <container>: <METRIC> (sustained <Ns>)
```

Exemplo: `ALERT webapp: CPU 75.4% (sustained 22s)`.

Parar o monitor
---------------

- O monitor principal é interrompido com `Ctrl+C`.

## Stress test (`_stressTest.py`)

Uso básico:

```bash
python3 _stressTest.py --url https://httpbin.org/get --requests 200 --concurrency 20
```

Modo paranoid (usa todos os núcleos de CPU):

```bash
python3 _stressTest.py --paranoid --max-requests 100 --url https://httpbin.org/get
```

Parar com tecla `S`:

- Durante a execução do stress test (ou em execuções normais deste script), pressione `S` ou `s` na janela do terminal para interromper o envio de novas requisições de forma imediata (sem precisar de Ctrl+C).

## Boas práticas

- Ajuste `sustained_seconds` de acordo com `interval_seconds`. Se `interval_seconds` for alto (ex.: 10s), escolha `sustained_seconds` >= 2 * `interval_seconds` para reduzir ruído.
- Teste `--paranoid` apenas em ambientes controlados.

## Troubleshooting

- "Nenhum container rodando": verifique se o Docker daemon está rodando e o usuário tem permissão para acessar o socket do Docker.
- Telegram não envia: verifique `telegram.bot_token` e `telegram.chat_id` em `config.json`. Use `https://api.telegram.org/bot<token>/getUpdates` para descobrir o `chat_id`.

## Próximas melhorias (opcionais)

- `sustained_seconds` por métrica (cpu/mem/net) para regras mais finas.
- Média móvel para rede ao invés de checagem pontual por amostra.
- Exportar histórico para CSV/JSON para análise posterior.

---

Se quiser que eu adicione exemplos concretos de `config.json` ou um `requirements.txt`, eu atualizo em seguida.