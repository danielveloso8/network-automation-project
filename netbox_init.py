import pynetbox
import yaml

NETBOX_URL = "http://localhost:8000/"
TOKEN = "d09g7LUzFUKHmfGu03ckK9GCPQMT9M2Sx9V9uQMo"
nb = pynetbox.api(NETBOX_URL, token=TOKEN)

sites = ["Office A", "Office B"]

roles = [
    "Edge Router", "Core Switch", "Distribution Switch", "Access Switch", 
    "Wireless Controller", "Server", "Access Point", "IP Phone", "Workstation"
]

manufacturer = ["Cisco", "Dell", "Generic"]

device_models = [
    {"name": "ISR4331", "manufacturer": "Cisco"}, 
    {"name": "C9300-24T", "manufacturer": "Cisco"},
    {"name": "C9800-CL", "manufacturer": "Cisco"}, 
    {"name": "C9120AXI", "manufacturer": "Cisco"},
    {"name": "CP-7841", "manufacturer": "Cisco"},    # Telefone IP
    {"name": "PowerEdge R740", "manufacturer": "Dell"}, # Servidor
    {"name": "Desktop PC", "manufacturer": "Generic"},
    {"name": "Laptop", "manufacturer": "Generic"}
]

def create_sites(sites_list):
    for site in sites_list:
        if not nb.dcim.sites.get(name=site):
            nb.dcim.sites.create(name=site, slug=site.lower().replace(" ","-"))
            print(f"Site {site} criado com sucesso.")
        else:
            print(f"O site {site} já existe. Criação de site ignorada.")

def create_device_roles(roles_list):
    for role in roles_list:
        if not nb.dcim.device_roles.get(name=role):
            nb.dcim.device_roles.create(name=role, slug=role.lower().replace(" ","-"))
            print(f"Role {role} criada com sucesso.")
        else:
            print(f"A role {role} já existe. Criação de role ignorada.")

def create_manufacturers(manufacturer_list):
    for manu in manufacturer_list:
        if not nb.dcim.manufacturers.get(name=manu):
            nb.dcim.manufacturers.create(name=manu, slug=manu.lower().replace(" ","-"))
            print(f"Fabricante {manu} criado com sucesso.")
        else:
            print(f"O fabricante {manu} já existe. Criação de fabricante ignorada.")        

def create_device_models(devmodels_list):
    for model in devmodels_list:
        obj_manufacturer = nb.dcim.manufacturers.get(name=model["manufacturer"])
        if obj_manufacturer:
            if not nb.dcim.device_types.get(model=model["name"]):
                nb.dcim.device_types.create(
                    model=model["name"], 
                    slug=model["name"].lower().replace(" ","-"), 
                    manufacturer=obj_manufacturer.id
                )
                print(f"Modelo {model['manufacturer']} {model['name']} criado com sucesso.")
            else:
                print(f"O modelo {model['name']} já existe. Criação de modelo ignorada.")  
        else:
            print(f"Erro: O fabricante {model['manufacturer']} não foi encontrado.") 


def load_devices_yaml(fpath):
    with open(fpath) as f:
        data = yaml.safe_load(f)
    return data['devices']

devices_list = load_devices_yaml("devices.yml")

def import_devices_to_netbox(device_list):
    for d in device_list:
        site_obj = nb.dcim.sites.get(name=d['site'])
        role_obj = nb.dcim.device_roles.get(name=d['role'])
        type_obj = nb.dcim.device_types.get(model=d['model'])

        if not all([site_obj, role_obj, type_obj]):
            print(f"Erro no dispositivo {d['name']}: Uma das informações não existe no Netbox.")
            continue

        if not nb.dcim.devices.get(name=d['name']):
            nb.dcim.devices.create(
                name=d['name'],
                role=role_obj.id,
                device_type=type_obj.id,
                site=site_obj.id,
                status="active"
            )
            print(f"Dispositivo {d['name']} criado com sucesso!")
        else:
            print(f"ℹDispositivo {d['name']} já existe.")


vlans = [
    # Office A
    {"name": "PCs A", "vid": 10, "site": "Office A"},
    {"name": "Phones A", "vid": 20, "site": "Office A"},
    {"name": "Wi-Fi A", "vid": 40, "site": "Office A"},
    {"name": "Mgmt A", "vid": 99, "site": "Office A"},
    
    # Office B
    {"name": "PCs B", "vid": 10, "site": "Office B"},
    {"name": "Phones B", "vid": 20, "site": "Office B"},
    {"name": "Servers B", "vid": 30, "site": "Office B"},
    {"name": "Mgmt B", "vid": 99, "site": "Office B"}
]

def create_vlans(vlan_list):
    for v in vlan_list:
        site_obj = nb.dcim.sites.get(name=v['site'])
        
        if site_obj:
            if not nb.ipam.vlans.get(vid=v['vid'], site_id=site_obj.id):
                nb.ipam.vlans.create(
                    name=v['name'],
                    vid=v['vid'],
                    site=site_obj.id,
                    status="active"
                )
                print(f"VLAN {v['vid']} ({v['name']}) criada no {v['site']}.")
            else:
                print(f"ℹVLAN {v['vid']} já existe no {v['site']}. A saltar...")
        else:
            print(f"Erro: Site {v['site']} não encontrado para a VLAN {v['name']}.")


def load_prefixes_from_yaml(filepath):
    try:
        with open(filepath) as file:
            data = yaml.safe_load(file)
            return data.get('prefixes', [])
    except FileNotFoundError:
        print(f"Erro: O ficheiro {filepath} não foi encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao processar o YAML: {e}")
        return []
    
prefixes = load_prefixes_from_yaml("prefixes.yml")

def create_prefixes(prefix_list):
    for p in prefix_list:
        site_obj = nb.dcim.sites.get(name=p['site'])
        
        if not site_obj:
            print(f"Erro: Site '{p['site']}' não encontrado. A saltar prefixo {p['prefix']}.")
            continue

        vlan_obj = None
        if p.get('vlan_vid'):
            vlan_obj = nb.ipam.vlans.get(vid=p['vlan_vid'], site_id=site_obj.id)
            if not vlan_obj:
                print(f"Aviso: VLAN {p['vlan_vid']} não encontrada no {p['site']}. Criando sem associação.")

        if not nb.ipam.prefixes.get(prefix=p['prefix']):
            nb.ipam.prefixes.create(
                prefix=p['prefix'],
                site=site_obj.id,
                vlan=vlan_obj.id if vlan_obj else None,
                status="active",
                description=p.get('description', "")
            )
            print(f"Prefixo {p['prefix']} criado com sucesso.")
        else:
            print(f"Prefixo {p['prefix']} já existe. A saltar...")


def import_connections_from_yaml(path):
    with open(path) as file:
        data = yaml.safe_load(file)

    for vi in data['virtual_interfaces']:
        device = nb.dcim.devices.get(name=vi['device'])
        if device:
            if not nb.dcim.interfaces.get(device_id=device.id, name=vi['name']):
                nb.dcim.interfaces.create(
                    device=device.id,
                    name=vi['name'],
                    type=vi['type']
                )
                print(f"Interface Virtual {vi['name']} criada em {vi['device']}")

    for conn in data['connections']:
        dev_a_name, int_a_name, dev_b_name, int_b_name = conn

        dev_a = nb.dcim.devices.get(name=dev_a_name)
        dev_b = nb.dcim.devices.get(name=dev_b_name)

        if not dev_a or not dev_b:
            print(f"Erro: Um dos dispositivos não existe.")
            continue

        def get_or_create_int(device, int_name):
                interface = nb.dcim.interfaces.get(device_id=device.id, name=int_name)
                if not interface:
                    int_type = 'lag' if 'Po' in int_name else '1000base-t'
                    interface = nb.dcim.interfaces.create(device=device.id, name=int_name, type=int_type)
                return interface

        if_a = get_or_create_int(dev_a, int_a_name)
        if_b = get_or_create_int(dev_b, int_b_name)

        if not if_a.cable and not if_b.cable:
            nb.dcim.cables.create(
                a_terminations=[{'object_type': 'dcim.interface', 'object_id': if_a.id}],
                b_terminations=[{'object_type': 'dcim.interface', 'object_id': if_b.id}],
                status='connected'
                )
            print(f"Cabo ligado: {dev_a_name} [{int_a_name}] <---> {dev_b_name} [{int_b_name}]")
        else:
            print(f"Ligação {dev_a_name} <-> {dev_b_name} já existe.")


def import_ips_from_yaml(filepath):
    with open(filepath) as file:
        data = yaml.safe_load(file)

    for entry in data['ips']:
        device = nb.dcim.devices.get(name=entry['device'])
        if not device:
            print(f"Dispositivo {entry['device']} não encontrado.")
            continue

        interface = nb.dcim.interfaces.get(device_id=device.id, name=entry['interface'])
        if not interface:
            print(f"Interface {entry['interface']} não encontrada em {entry['device']}.")
            continue

        ip_addr = nb.ipam.ip_addresses.get(address=entry['address'])

        if not ip_addr:
            nb.ipam.ip_addresses.create(
                address=entry['address'],
                status='active',
                assigned_object_type='dcim.interface',
                assigned_object_id=interface.id
            )
            print(f"IP {entry['address']} atribuído a {entry['device']} [{entry['interface']}]")
        else:
            print(f"IP {entry['address']} já existe. A saltar...")


def import_vips_from_yaml(filepath):
    with open(filepath) as file:
        data = yaml.safe_load(file)

    if 'vips' not in data:
        return

    for vip in data['vips']:
        ip_obj = nb.ipam.ip_addresses.get(address=vip['address'])
        
        if not ip_obj:
            nb.ipam.ip_addresses.create(
                address=vip['address'],
                status='active',
                role='vip',
                description=vip['description']
            )
            print(f"VIP {vip['address']} ({vip['description']}) criado com sucesso.")
        else:
            print(f"VIP {vip['address']} já existe. A saltar...")



if __name__ == "__main__":
    create_sites(sites)
    create_device_roles(roles)
    create_manufacturers(manufacturer)
    create_device_models(device_models)
    import_devices_to_netbox(devices_list)
    create_vlans(vlans)
    import_connections_from_yaml("connections.yml")
    import_ips_from_yaml("ips.yml")
    import_vips_from_yaml("ips.yml")
    if prefixes:
        create_prefixes(prefixes)

