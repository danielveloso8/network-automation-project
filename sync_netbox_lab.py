import pynetbox, subprocess, yaml, time, os, sys

NETBOX_URL = os.getenv("NETBOX_URL")
TOKEN = os.getenv("NETBOX_TOKEN")

if not TOKEN or not NETBOX_URL:
    print("❌ Erro: Variáveis de ambiente de API não encontradas.")
    sys.exit(1)

nb = pynetbox.api(NETBOX_URL, token=TOKEN)

"""
Script de Sincronização NetBox-to-Lab.
Este módulo automatiza a configuração de interfaces, IPs e protocolos 
de roteamento (OSPF) nos nós FRRouting, garantindo a paridade entre 
o estado pretendido (NetBox) e o estado real (Laboratório).
"""

def get_mapping():
    with open("connections.yml", "r") as f:
        data = yaml.safe_load(f)
    mapping = {}
    counters = {}
    for conn in data.get('connections', []):
        for node, intf in [(conn[0], conn[1]), (conn[2], conn[3])]:
            counters[node] = counters.get(node, 0) + 1
            if node not in mapping: mapping[node] = {}
            mapping[node][intf] = f"eth{counters[node]}"
    return mapping

def run_vtysh(container, cmds):
    # Syntax corrigida para evitar o erro de NameError
    cmd_str = " ".join([f"-c '{c}'" for c in cmds])
    subprocess.run(f"docker exec {container} vtysh {cmd_str}", shell=True, stderr=subprocess.DEVNULL)

def sync_lab():
    iface_map = get_mapping()
    devices = ["R1", "CSW1", "CSW2", "DSW-A1", "DSW-A2"]
    
    print("🚀 Sincronizando Lab com NetBox (Modo OSPF Estável)...")

    for name in devices:
        container = f"clab-projeto-ccna-{name}"
        print(f"\n📦 Configurando {name}...")

        # Iniciar daemons de forma segura
        subprocess.run(f"docker exec {container} touch /etc/frr/vtysh.conf", shell=True)
        subprocess.run(f"docker exec {container} sh -c 'pgrep zebra > /dev/null || /usr/lib/frr/zebra -d'", shell=True)
        subprocess.run(f"docker exec {container} sh -c 'pgrep ospfd > /dev/null || /usr/lib/frr/ospfd -d'", shell=True)
        
        # Router-ID dinâmico do NetBox
        lb = nb.ipam.ip_addresses.get(device=name, interface='Loopback0')
        router_id = lb.address.split('/')[0] if lb else "1.1.1.1"
        
        run_vtysh(container, ["conf t", "router ospf", f"ospf router-id {router_id}", "passive-interface default", "exit"])

        # Configurar interfaces baseadas no NetBox
        interfaces = nb.ipam.ip_addresses.filter(device=name, status="active")
        for ip_obj in interfaces:
            cisco_int = ip_obj.assigned_object.name
            ip_addr = ip_obj.address
            
            if "Po" in cisco_int: continue # Salta Port-Channels lógicos

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
                print(f"  ⚙️  Configurando {linux_int} ({cisco_int}) -> {ip_addr}")
                run_vtysh(container, [
                    "conf t", 
                    f"interface {linux_int}", 
                    f"ip address {ip_addr}", 
                    "ip ospf area 0", 
                    "no ip ospf passive", 
                    "exit"
                ])

    print("\n✅ Configuração concluída!")

if __name__ == "__main__":
    sync_lab()