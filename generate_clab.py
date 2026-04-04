import pynetbox
import yaml
import re

NETBOX_URL = "http://localhost:8000"
NETBOX_TOKEN = "d09g7LUzFUKHmfGu03ckK9GCPQMT9M2Sx9V9uQMo"

nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

def generate_containerlab_topology():
    print("A gerar topologia do Containerlab...")
    
    port_counters = {} 
    
    topology = {
        "name": "projeto-v2",
        "topology": {
            "nodes": {},
            "links": []
        }
    }

    kind_mapping = {
        "ISR4331": "nokia_srlinux",
        "C9300-24T": "nokia_srlinux",
        "C9800-CL": "nokia_srlinux",
        "Desktop PC": "linux"
    }

    all_devices = list(nb.dcim.devices.all())
    
# No teu loop de dispositivos em generate_clab.py:
    for device in all_devices:
        # FILTRO DE SEGURANÇA: Só R1, Cores e ISPs
        if device.name not in ["R1", "CSW1", "CSW2", "ISPA", "ISPB"]:
            continue 
            
        kind = kind_mapping.get(device.device_type.model)
        if kind:
            mgmt_id = 100 + all_devices.index(device)
            
            image_name = "ghcr.io/nokia/srlinux:latest" if kind == "nokia_srlinux" else "alpine:latest"
            
            topology["topology"]["nodes"][device.name] = {
                "kind": kind,
                "image": image_name,
                "mgmt-ipv4": f"172.20.20.{mgmt_id}"
            }

    cables = nb.dcim.cables.all()
    for cable in cables:
        if not cable.a_terminations or not cable.b_terminations:
            continue
            
        a_side = cable.a_terminations[0]
        b_side = cable.b_terminations[0]

        if a_side.object_type == "dcim.interface" and b_side.object_type == "dcim.interface":
            dev_a = a_side.object.device.name
            dev_b = b_side.object.device.name

            if dev_a in topology["topology"]["nodes"] and dev_b in topology["topology"]["nodes"]:
            
                def get_unique_port(device_name):
                    if device_name not in port_counters:
                        port_counters[device_name] = 1
                
                    p_num = port_counters[device_name]
                    port_counters[device_name] += 1
                
                    d_obj = nb.dcim.devices.get(name=device_name)
                    d_kind = kind_mapping.get(d_obj.device_type.model)
                
                    if d_kind == "nokia_srlinux":
                        return f"e1-{p_num}"
                    return f"eth{p_num}"

                topology["topology"]["links"].append({
                    "endpoints": [f"{dev_a}:{get_unique_port(dev_a)}", 
                             f"{dev_b}:{get_unique_port(dev_b)}"]
                })

    with open("projeto.clab.yml", "w") as f:
        yaml.dump(topology, f, default_flow_style=False, sort_keys=False)
    
    print("Ficheiro 'projeto.clab.yml' gerado com sucesso e sem duplicados!")

if __name__ == "__main__":
    generate_containerlab_topology()