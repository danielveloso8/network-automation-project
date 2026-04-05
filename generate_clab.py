import yaml

def generate_frr_lab():
    with open("connections.yml", "r") as f:
        data = yaml.safe_load(f)
    
    connections = data.get('connections', [])
    
    # 1. Descobrir todos os nós que aparecem nas conexões
    all_nodes = set()
    for conn in connections:
        if len(conn) >= 3:
            all_nodes.add(conn[0]) # Primeiro nó (ex: R1)
            all_nodes.add(conn[2]) # Segundo nó (ex: ISPA)

    clab_config = {
        "name": "projeto-ccna",
        "topology": {
            "nodes": {node: {"kind": "linux", "image": "frrouting/frr:latest"} for node in all_nodes},
            "links": []
        }
    }

    # 2. Gerar os links (mapeando automaticamente para eth1, eth2...)
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
    
    print(f"✅ Lab gerado com {len(all_nodes)} dispositivos e {len(clab_config['topology']['links'])} links!")

if __name__ == "__main__":
    generate_frr_lab()