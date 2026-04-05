import subprocess
import json

def run_vtysh_json(container, command):
    full_cmd = f"docker exec {container} vtysh -c '{command} json'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    try: return json.loads(result.stdout)
    except: return {}

def verify():
    print("\n🔍 VALIDAÇÃO DA REDE")
    print("="*45)
    
    # OSPF Check
    for node in ["R1", "CSW1", "CSW2"]:
        data = run_vtysh_json(f"clab-projeto-ccna-{node}", "show ip ospf neighbor")
        count = len(data.get('neighbors', {}))
        status = "✅ OK" if count > 0 else "❌ SEM VIZINHOS"
        print(f"  OSPF {node}: {count} vizinhos. {status}")

    # Ping Check (E2E)
    res = subprocess.run("docker exec clab-projeto-ccna-R1 ping 10.0.0.80 -c 2 -W 1", shell=True, capture_output=True)
    print(f"  PING R1 -> DSW-A2: {'✅ SUCESSO' if res.returncode == 0 else '❌ FALHA'}")
    print("="*45)

if __name__ == "__main__":
    verify()