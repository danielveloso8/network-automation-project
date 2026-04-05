import yaml
import subprocess

def run_vtysh(container, commands):
    """Executa uma lista de comandos vtysh dentro de um container."""
    cmd_string = " ".join([f"-c '{c}'" for c in commands])
    full_cmd = f"docker exec {container} vtysh {cmd_string}"
    subprocess.run(full_cmd, shell=True, stderr=subprocess.DEVNULL)

def deploy_routing():
    with open("ips.yml", "r") as f:
        data = yaml.safe_load(f)

    print("🧠 Configurando Loopbacks e OSPF...")

    for entry in data['ips']:
        device = entry['device']
        ip_addr = entry['address']
        interface = entry['interface']
        container = f"clab-projeto-ccna-{device}"

        # 1. Configurar Loopbacks (IPs imortais)
        if "Loopback" in interface or "lo" in interface:
            print(f"📍 Loopback em {device}: {ip_addr}")
            run_vtysh(container, [
                "conf t",
                "interface lo",
                f"ip address {ip_addr}",
                "exit"
            ])

        # 2. Configurar OSPF (Apenas para R1, CSW e DSW)
        if any(prefix in device for prefix in ["R1", "CSW", "DSW"]):
            # Extraímos o IP sem a máscara para o Router-ID
            router_id = ip_addr.split('/')[0] if "Loopback" in interface else None
            
            ospf_cmds = ["conf t", "router ospf"]
            if router_id: ospf_cmds.append(f"ospf router-id {router_id}")
            
            # Anunciar as redes internas (10.0.0.0/8) na Area 0
            ospf_cmds.append("network 10.0.0.0/8 area 0")
            
            # No R1, redistribuir a rota default para a Internet
            if device == "R1":
                ospf_cmds.append("default-information originate always")
            
            ospf_cmds.extend(["exit"])
            run_vtysh(container, ospf_cmds)

    print("\n✅ Roteamento OSPF e Loopbacks ativos!")

if __name__ == "__main__":
    deploy_routing()