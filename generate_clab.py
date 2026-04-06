"""
Módulo Gerador da Topologia (Containerlab)
Este script automatiza a criação do ficheiro de definição (.clab.yml) do Containerlab.
A sua principal função é garantir que a topologia física virtualizada seja 
fiel às conexões definidas no connections.yml.
"""

import yaml

def generate_frr_lab():
    """
    Processa as definições de conectividade e gera o ficheiro do Containerlab.
    Implementa uma lógica de auto-incremento para interfaces Linux a partir 
    das interfaces como a G1/0/1 (ethX).
    """

    try:
        with open("connections.yml", "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print("Ficheiro connections.yml não encontrado.")
        return

    connections = data.get('connections', [])
    
    # Extrai todos os nomes únicos de dispositivos para definir os nós
    all_nodes = set()
    for conn in connections:
        if len(conn) >= 3:
            all_nodes.add(conn[0]) # Origem (ex: R1)
            all_nodes.add(conn[2]) # Destino (ex: ISPA)

    # Definição do dicionário que será o nosso ficheiro YAML final
    clab_config = {
        "name": "projeto-ccna",
        "topology": {
            # Todos os nós utilizam a imagem oficial do FRRouting 
            "nodes": {node: {"kind": "linux", "image": "frrouting/frr:latest"} for node in all_nodes},
            "links": []
        }
    }

    # Como o Linux não usa nomes como 'GigabitEthernet', mapeei sequencialmente para eth1, eth2, etc., conforme a ordem das conexões.
    iface_counters = {}

    for conn in connections:
        if len(conn) < 3: continue
        
        node_a, node_b = conn[0], conn[2]
        
        iface_counters[node_a] = iface_counters.get(node_a, 0) + 1
        iface_counters[node_b] = iface_counters.get(node_b, 0) + 1
        
        clab_config['topology']['links'].append({
            "endpoints": [
                f"{node_a}:eth{iface_counters[node_a]}", 
                f"{node_b}:eth{iface_counters[node_b]}"
            ]
        })

    with open("projeto.clab.yml", "w") as f:
        yaml.dump(clab_config, f, default_flow_style=False)
    
    print(f"Ficheiro .clab.yml gerado com sucesso!")
    print(f"Resumo: {len(all_nodes)} nós e {len(clab_config['topology']['links'])} links físicos.")

if __name__ == "__main__":
    generate_frr_lab()