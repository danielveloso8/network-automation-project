import yaml
import subprocess
import time

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

def deploy():
    iface_map = get_mapping()
    with open("ips.yml", "r") as f:
        ips_data = yaml.safe_load(f)

    print("🚀 Configurando interfaces via VTYSH (Modo Cisco)...")
    for entry in ips_data['ips']:
        device, cisco_int, ip_addr = entry['device'], entry['interface'], entry['address']
        linux_int = iface_map.get(device, {}).get(cisco_int)
        
        # Se for Loopback, usamos sempre 'lo'
        if "Loopback" in cisco_int: linux_int = "lo"
        if not linux_int: continue

        container = f"clab-projeto-ccna-{device}"
        print(f"⚙️  {device}: interface {linux_int} ip {ip_addr}")

        # Comandos estilo Cisco para forçar o Zebra a ver a interface
        cmd = (
            f"vtysh -c 'conf t' "
            f"-c 'interface {linux_int}' "
            f"-c 'ip address {ip_addr}' "
            f"-c 'no shutdown' -c 'exit' "
        )
        subprocess.run(f"docker exec {container} {cmd}", shell=True, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    deploy()