"""
Módulo de Sincronização e Configuração Dinâmica (NetBox -> Lab).
Este script é o motor de provisionamento do projeto. Ele usa a API do 
NetBox para extrair o estado desejado da rede e injeta as 
configurações nos nós via VTYSH.

Funcionalidades principais:
- Mapeamento dinâmico de interfaces Cisco (NetBox) para Linux (Lab).
- Provisionamento de Sub-interfaces VLAN 802.1Q no Kernel Linux.
- Configuração automatizada de OSPF com Router-ID e Áreas dinâmicas.
"""

import pynetbox, subprocess, yaml, time, os, sys

NETBOX_URL = os.getenv("NETBOX_URL")
TOKEN = os.getenv("NETBOX_TOKEN")

if not TOKEN or not NETBOX_URL:
    print("Erro: Variáveis de ambiente de API (NETBOX_URL/TOKEN) não encontradas.")
    sys.exit(1)

nb = pynetbox.api(NETBOX_URL, token=TOKEN)

def get_mapping():
    """
    Cria um dicionário de tradução entre o inventário do NetBox e o Containerlab.
    Como o Containerlab utiliza nomes sequenciais (eth1, eth2...), este método 
    garante que o IP da 'GigabitEthernet0/0' no NetBox se traduza na 'ethX' correta
    """
    try:
        with open("connections.yml", "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print("Erro: Ficheiro de conexões não encontrado para mapeamento.")
        return {}

    mapping = {}
    counters = {}
    for conn in data.get('connections', []):
        for node, intf in [(conn[0], conn[1]), (conn[2], conn[3])]:
            counters[node] = counters.get(node, 0) + 1
            if node not in mapping: mapping[node] = {}
            mapping[node][intf] = f"eth{counters[node]}"
    return mapping

def run_vtysh(container, cmds):
    """
    Ajuda na execução de comandos dentro da CLI do FRRouting (VTYSH).
    Abstrai a complexidade do 'docker exec' e permite o envio de listas de comandos.
    """
    cmd_str = " ".join([f"-c '{c}'" for c in cmds])
    subprocess.run(f"docker exec {container} vtysh {cmd_str}", shell=True, stderr=subprocess.DEVNULL)

def sync_lab():
    """
    Workflow principal de sincronização.
    Garante que cada dispositivo no laboratório reflita exatamente o que está no NetBox.
    """
    iface_map = get_mapping()
    devices = ["R1", "CSW1", "CSW2", "DSW-A1", "DSW-A2"]
    
    print("A sincronizar Lab com o NetBox")

    for name in devices:
        container = f"clab-projeto-ccna-{name}"
        print(f"\nA configurar {name}...")

        # Gestão de Daemons, devido a problemas de salvar configurações.
        subprocess.run(f"docker exec {container} touch /etc/frr/vtysh.conf", shell=True)
        subprocess.run(f"docker exec {container} sh -c 'pgrep zebra > /dev/null || /usr/lib/frr/zebra -d'", shell=True)
        subprocess.run(f"docker exec {container} sh -c 'pgrep ospfd > /dev/null || /usr/lib/frr/ospfd -d'", shell=True)
        
        # O Router-ID é extraído dinamicamente da Loopback0 configurada no NetBox.
        lb = nb.ipam.ip_addresses.get(device=name, interface='Loopback0')
        router_id = lb.address.split('/')[0] if lb else "1.1.1.1"
        
        run_vtysh(container, [
            "conf t", 
            "router ospf", 
            f"ospf router-id {router_id}", 
            "passive-interface default", 
            "exit"
        ])

        # Filtra apenas os IPs ativos no NetBox para o dispositivo específico.
        interfaces = nb.ipam.ip_addresses.filter(device=name, status="active")
        for ip_obj in interfaces:
            cisco_int = ip_obj.assigned_object.name
            ip_addr = ip_obj.address
            
            if "Po" in cisco_int: continue 

            if "Vlan" in cisco_int:
                v_id = cisco_int.replace("Vlan", "")
                subprocess.run(f"docker exec {container} ip link add link eth1 name {cisco_int} type vlan id {v_id} 2>/dev/null", shell=True)
                subprocess.run(f"docker exec {container} ip link set {cisco_int} up", shell=True)
                linux_int = cisco_int
            elif "Loopback" in cisco_int:
                linux_int = "lo"
            else:
                linux_int = iface_map.get(name, {}).get(cisco_int)

            if linux_int:
                print(f"  A aplicar: {linux_int} ({cisco_int}) -> {ip_addr}")
                # COnfiguração de IP + Ativação OSPF por interface
                run_vtysh(container, [
                    "conf t", 
                    f"interface {linux_int}", 
                    f"ip address {ip_addr}", 
                    "ip ospf area 0", 
                    "no ip ospf passive", 
                    "exit"
                ])

    print("\nSincronização concluída")

if __name__ == "__main__":
    sync_lab()