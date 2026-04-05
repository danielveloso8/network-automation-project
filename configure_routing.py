import yaml
import subprocess
import time

def run_vtysh(container, commands):
    """Executa comandos no vtysh ignorando erros de saída."""
    cmd_string = " ".join([f"-c '{c}'" for c in commands])
    full_cmd = f"docker exec {container} vtysh {cmd_string}"
    subprocess.run(full_cmd, shell=True, stderr=subprocess.DEVNULL)

def enable_vrrp_daemon(container):
    """Garante que o serviço VRRP está ativo no Linux do container."""
    # Ativa no ficheiro de daemons
    subprocess.run(f"docker exec {container} sed -i 's/vrrpd=no/vrrpd=yes/g' /etc/frr/daemons", shell=True)
    # Tenta arrancar o binário se não estiver a correr
    subprocess.run(f"docker exec {container} /usr/lib/frr/vrrpd -d -F traditional", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(1)

def get_mapping():
    with open("connections.yml", "r") as f:
        data = yaml.safe_load(f)
    mapping = {}
    counters = {}
    for conn in data.get('connections', []):
        if len(conn) < 4: continue
        for node, intf in [(conn[0], conn[1]), (conn[2], conn[3])]:
            counters[node] = counters.get(node, 0) + 1
            if node not in mapping: mapping[node] = {}
            mapping[node][intf] = f"eth{counters[node]}"
    return mapping

def deploy_routing():
    iface_map = get_mapping()
    with open("ips.yml", "r") as f:
        data = yaml.safe_load(f)

    print("🧠 Configurando OSPF (Sintaxe Moderna) e VRRP (Sintaxe Validada)...")

    # 1. Configuração OSPF
    for entry in data['ips']:
        device = entry['device']
        cisco_int = entry['interface']
        container = f"clab-projeto-ccna-{device}"
        
        if any(prefix in device for prefix in ["R1", "CSW", "DSW"]):
            linux_int = iface_map.get(device, {}).get(cisco_int)
            # Global
            run_vtysh(container, ["conf t", "router ospf", "passive-interface default", "network 10.0.0.0/8 area 0"])
            # Interface level (Sintaxe moderna para evitar deprecation)
            if linux_int and "Loopback" not in cisco_int and "Vlan" not in cisco_int:
                run_vtysh(container, ["conf t", f"interface {linux_int}", "no ip ospf passive"])

    # 2. Configuração VRRP nos DSWs
    vrrp_configs = [
        {"node": "DSW-A1", "int": "Vlan10", "vip": "10.1.0.1", "prio": 110},
        {"node": "DSW-A2", "int": "Vlan10", "vip": "10.1.0.1", "prio": 100},
    ]

    for v in vrrp_configs:
        container = f"clab-projeto-ccna-{v['node']}"
        print(f"🛡️ Configurando VRRP em {v['node']} ({v['int']})")
        
        enable_vrrp_daemon(container)
        
        # A sintaxe que tu descobriste!
        run_vtysh(container, [
            "conf t", 
            f"interface {v['int']}",
            f"vrrp 10 ip {v['vip']}", 
            f"vrrp 10 priority {v['prio']}", 
            "exit"
        ])

if __name__ == "__main__":
    deploy_routing()