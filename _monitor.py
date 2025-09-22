import docker
import time
import signal
import sys
import logging
import argparse
from datetime import datetime
# lightweight monitoring output (no progress bars)

# Global variable to control monitoring loop
running = True
client = None

def check_docker_connection():
    """Verifica se o Docker daemon está rodando e acessível"""
    global client
    try:
        client = docker.from_env()
        # Testa a conexão
        client.ping()
        return True
    except docker.errors.DockerException as e:
        print(f"❌ Erro de conexão com Docker: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Certifique-se de que o Docker Desktop está rodando")
        print("2. No macOS, inicie o Docker Desktop pela aplicação")
        print("3. Verifique se o serviço Docker está ativo:")
        print("   - Docker Desktop: Abra a aplicação Docker")
        print("   - Docker Engine: sudo systemctl start docker (Linux)")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao conectar com Docker: {e}")
        return False

def signal_handler(signum, frame):
    global running
    print("\nParando monitoramento...")
    running = False

# Limites aproximados para normalizar as barras
MAX_CPU = 100.0  # %
#!/usr/bin/env python3
import os
import json
import docker
import time
import signal
import sys
import logging
import argparse
from datetime import datetime
from tqdm import tqdm

# Global variable to control monitoring loop
running = True
client = None


def load_config():
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(cfg_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def check_docker_connection():
    """Verifica se o Docker daemon está rodando e acessível"""
    global client
    try:
        client = docker.from_env()
        # Testa a conexão
        client.ping()
        return True
    except docker.errors.DockerException as e:
        print(f"❌ Erro de conexão com Docker: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Certifique-se de que o Docker Desktop está rodando")
        print("2. No macOS, inicie o Docker Desktop pela aplicação")
        print("3. Verifique se o serviço Docker está ativo:")
        print("   - Docker Desktop: Abra a aplicação Docker")
        print("   - Docker Engine: sudo systemctl start docker (Linux)")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao conectar com Docker: {e}")
        return False


def signal_handler(signum, frame):
    global running
    print("\nParando monitoramento...")
    running = False


# Limites aproximados para normalizar as barras (valores vizualização)
MAX_CPU = 100.0  # %
MAX_MEM = 8.0    # GB
MAX_NET = 10 * 1024 * 1024    # bytes (10MB)


def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
    except Exception as e:
        print(f"Erro ao obter stats do container {container.name}: {e}")
        return 0.0, 0.0, 0

    cpu_percent = 0.0
    mem_usage_gb = 0.0
    net_total = 0

    try:
        # Memory usage calculation
        mem_bytes = stats.get('memory_stats', {}).get('usage', 0)
        mem_usage_gb = mem_bytes / (1024 ** 3)
    except Exception:
        mem_usage_gb = 0.0

    try:
        # CPU usage calculation
        cpu_stats = stats.get('cpu_stats', {})
        precpu = stats.get('precpu_stats', {})
        cpu_total = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
        precpu_total = precpu.get('cpu_usage', {}).get('total_usage', 0)
        sys_total = cpu_stats.get('system_cpu_usage', 0)
        presys_total = precpu.get('system_cpu_usage', 0)
        cpu_delta = cpu_total - precpu_total
        sys_delta = sys_total - presys_total
        if sys_delta > 0 and cpu_delta > 0:
            num_cpus = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [1]))
            cpu_percent = (cpu_delta / sys_delta) * num_cpus * 100.0
    except Exception:
        cpu_percent = 0.0

    try:
        networks = stats.get('networks') or {}
        for iface in networks.values():
            net_total += int(iface.get('rx_bytes', 0)) + int(iface.get('tx_bytes', 0))
    except Exception:
        net_total = 0

    return cpu_percent, mem_usage_gb, net_total


def monitor_containers(interval=2):
    global running, client

    cfg = load_config()
    thresholds = cfg.get('thresholds', {})
    cpu_threshold = float(thresholds.get('cpu', 50.0))
    mem_threshold = float(thresholds.get('memory_gb', 4.0))
    net_threshold = float(thresholds.get('network_mbps', 5.0))
    monitoring_cfg = cfg.get('monitoring', {})
    cfg_interval = int(monitoring_cfg.get('interval_seconds', interval))
    if cfg_interval and cfg_interval > 0:
        interval = cfg_interval
    cooldown_min = float(monitoring_cfg.get('alert_cooldown_minutes', 5.0))
    sustained_seconds = float(monitoring_cfg.get('sustained_seconds', 20.0))

    telegram_cfg = cfg.get('telegram', {})

    # Verifica conexão com Docker antes de iniciar
    if not check_docker_connection():
        return

    bars = {}
    prev_net = {}

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    def cleanup_bars():
        # No visual resources to cleanup when not using tqdm bars
        return

    def update_container_positions():
        """Reordena os containers por uso de CPU (maior para menor)"""
        # Bars removed; ordering will be handled when printing the table
        return

    def refresh_containers():
        try:
            current_containers = client.containers.list()
            current_names = {c.name for c in current_containers}
            existing_names = set(bars.keys())

            # Remove bars for stopped containers
            for name in existing_names - current_names:
                if name in bars:
                    # No progress bars to close in lightweight mode; just remove entries
                    try:
                        del bars[name]
                        if name in prev_net:
                            del prev_net[name]
                    except Exception:
                        pass

            # Add bars for new containers
            for container in current_containers:
                if container.name not in bars:
                    bars[container.name] = {
                        'cpu_value': 0.0,
                        'mem_value': 0.0,
                        'net_value': 0,
                    }
                    prev_net[container.name] = 0

            return current_containers
        except docker.errors.DockerException as e:
            print(f"❌ Erro de conexão com Docker: {e}")
            return []
        except Exception as e:
            print(f"Erro ao atualizar lista de containers: {e}")
            return []

    # Alert state and helpers
    alert_state = {}
    # track when a metric first exceeded the threshold; structure: { '<container>:<metric>': datetime }
    sustained_start = {}

    def can_alert(key: str) -> bool:
        last = alert_state.get(key)
        if not last:
            return True
        diff_min = (datetime.now() - last).total_seconds() / 60.0
        return diff_min >= cooldown_min

    def send_telegram_message(text: str) -> bool:
        if not telegram_cfg.get('enabled'):
            return False
        token = telegram_cfg.get('bot_token')
        chat_id = telegram_cfg.get('chat_id')
        if not token or not chat_id:
            print('Telegram configurado mas bot_token/chat_id faltando')
            return False
        try:
            from urllib import request, parse
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': text}
            data_encoded = parse.urlencode(data).encode()
            req = request.Request(url, data=data_encoded)
            with request.urlopen(req, timeout=10) as resp:
                resp.read()
            return True
        except Exception as e:
            print(f"Falha ao enviar Telegram: {e}")
            return False

    def check_and_alert(container_name: str, cpu: float, mem_gb: float, net_bytes_delta: int):
        triggered = []
        now = datetime.now()

        # CPU sustained check
        key_cpu = f"{container_name}:cpu"
        if cpu > cpu_threshold:
            if key_cpu not in sustained_start:
                sustained_start[key_cpu] = now
            else:
                elapsed = (now - sustained_start[key_cpu]).total_seconds()
                if elapsed >= sustained_seconds and can_alert(key_cpu):
                    triggered.append(f"CPU {cpu:.1f}% (sustained {int(elapsed)}s)")
                    alert_state[key_cpu] = now
                    # reset start to avoid duplicate alerts until cooldown passes
                    sustained_start.pop(key_cpu, None)
        else:
            sustained_start.pop(key_cpu, None)

        # Memory sustained check
        key_mem = f"{container_name}:mem"
        if mem_gb > mem_threshold:
            if key_mem not in sustained_start:
                sustained_start[key_mem] = now
            else:
                elapsed = (now - sustained_start[key_mem]).total_seconds()
                if elapsed >= sustained_seconds and can_alert(key_mem):
                    triggered.append(f"MEM {mem_gb:.2f}GB (sustained {int(elapsed)}s)")
                    alert_state[key_mem] = now
                    sustained_start.pop(key_mem, None)
        else:
            sustained_start.pop(key_mem, None)

        # Network sustained check: convert to MB/s
        net_mbps = (net_bytes_delta / float(interval)) / (1024.0 * 1024.0)
        key_net = f"{container_name}:net"
        if net_mbps > net_threshold:
            if key_net not in sustained_start:
                sustained_start[key_net] = now
            else:
                elapsed = (now - sustained_start[key_net]).total_seconds()
                if elapsed >= sustained_seconds and can_alert(key_net):
                    triggered.append(f"NET {net_mbps:.2f}MB/s (sustained {int(elapsed)}s)")
                    alert_state[key_net] = now
                    sustained_start.pop(key_net, None)
        else:
            sustained_start.pop(key_net, None)

        if triggered:
            short = ', '.join(triggered)
            header = "### DOCKER-MONITOR ###"
            status = f"ALERT {container_name}: {short}"
            message = f"{header}\n{status}"
            # Print with header on its own line for console visibility
            try:
                print(header)
                print(status)
            except Exception:
                # fallback to single-line print
                print(message)
            # send concise telegram message (header + status on next line)
            if telegram_cfg.get('enabled'):
                send_telegram_message(message)
            return True
        return False

    try:
        containers = refresh_containers()

        if not containers:
            print("⚠️  Nenhum container rodando encontrado.")
            print("💡 Inicie alguns containers e execute o script novamente.")
            return

        print(f"📊 Monitorando {len(containers)} container(s)...")
        print("🛑 Pressione Ctrl+C para parar o monitoramento")
        print("📈 Containers ordenados por uso de CPU (maior → menor)\n")

        iteration_count = 0
        while running:
            # Refresh container list periodically
            if len(containers) == 0 or time.time() % 10 < interval:
                new_containers = refresh_containers()
                if new_containers:
                    containers = new_containers

            for container in containers:
                if not running:
                    break
                try:
                    # Check if container is still running
                    container.reload()
                    if container.status != 'running':
                        continue

                    cpu, mem, net_total = get_container_stats(container)

                    prev = prev_net.get(container.name, None)
                    net_delta = 0
                    if prev is not None:
                        net_delta = max(0, net_total - prev)
                    prev_net[container.name] = net_total

                    # Check and send alerts (concise)
                    check_and_alert(container.name, cpu, mem, net_delta)

                    if container.name in bars:
                        # Atualizar valores para ordenação e exibição em colunas
                        bars[container.name]['cpu_value'] = cpu
                        bars[container.name]['mem_value'] = mem
                        bars[container.name]['net_value'] = net_delta
                except docker.errors.DockerException as e:
                    print(f"❌ Erro de conexão Docker no container {container.name}: {e}")
                    running = False
                    break
                except Exception as e:
                    print(f"⚠️  Erro no container {container.name}: {e}")
                    continue

            # After processing this iteration of containers, print a lightweight table
            try:
                # Clear screen and print header
                print('\033[H\033[J', end='')
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"DOCKER MONITOR — {now}")
                print(f"{'CONTAINER':<30} {'CPU%':>7} {'MEM(GB)':>9} {'NET(B/s)':>12}")
                # sort containers by cpu desc and display
                sorted_containers = sorted(bars.items(), key=lambda x: x[1].get('cpu_value', 0.0), reverse=True)
                for name, info in sorted_containers:
                    cpuv = info.get('cpu_value', 0.0) or 0.0
                    memv = info.get('mem_value', 0.0) or 0.0
                    netv = info.get('net_value', 0) or 0
                    print(f"{name:<30} {cpuv:7.2f} {memv:9.2f} {int(netv):12d}")
                print('\nPress Ctrl+C or use S to stop (if available).')
            except Exception:
                # If printing fails for any reason, silently continue
                pass

            # Reordenar containers a cada 5 iterações (aproximadamente 10 segundos)
            iteration_count += 1
            if iteration_count % 5 == 0:
                update_container_positions()

            if running:
                time.sleep(interval)

    except KeyboardInterrupt:
        running = False
    except docker.errors.DockerException as e:
        print(f"❌ Erro de conexão com Docker durante monitoramento: {e}")
    finally:
        cleanup_bars()
        print("\n✅ Monitoramento finalizado.")


if __name__ == "__main__":
    monitor_containers()
