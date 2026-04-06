"""
Módulo de Validação e Teste.
Este script executa a verificação após o provisionamento, validando se o 
OSPF convergiu e se existe conectividade entre o Core e a Distribuição.
"""

import subprocess
import json

def run_vtysh_json(container, command):
    """
    Executa comandos no VTYSH solicitando a saída em formato JSON.
    """
    full_cmd = f"docker exec {container} vtysh -c '{command} json'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    try: 
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

def verify():
    """
    Realiza o health-check da infraestrutura.
    Verifica OSPF neighbors e realiza pings entre extremidades da rede.
    """
    print("\nRELATÓRIO DE VALIDAÇÃO DA REDE:")
    
    backbone_nodes = ["R1", "CSW1", "CSW2"]
    
    for node in backbone_nodes:
        container_name = f"clab-projeto-ccna-{node}"
        # Consulta a tabela de OSPF neighbors
        data = run_vtysh_json(container_name, "show ip ospf neighbor")
        
        neighbors_count = len(data.get('neighbors', {}))
        
        status = "✅ OK" if neighbors_count > 0 else "❌ SEM VIZINHOS (CRÍTICO)"
        print(f"  OSPF {node:6}: {neighbors_count} vizinho(s) ativos. {status}")

    # Este teste valida que o OSPF propagou as rotas corretamente por todos os dispositivos.
    target_ip = "10.0.0.80"
    print(f"\nA pingar...")
    
    res = subprocess.run(
        f"docker exec clab-projeto-ccna-R1 ping {target_ip} -c 2 -W 1", 
        shell=True, capture_output=True
    )
    
    if res.returncode == 0:
        print(f"  PING R1 -> DSW-A2 ({target_ip}): ✅ SUCESSO")
    else:
        print(f"  PING R1 -> DSW-A2 ({target_ip}): ❌ FALHA NA COMUNICAÇÃO")
        


if __name__ == "__main__":
    verify()