# 🚀 Network Automation Framework: NetBox + Containerlab + FRR

Este projeto demonstra a implementação de uma metodologia **Infrastructure as Code (IaC)** para a automação de infraestruturas de rede. Utiliza o **NetBox** como a única fonte da verdade (*Single Source of Truth*) para gerir o ciclo de vida completo de uma rede virtualizada, desde o aprovisionamento do inventário até à validação de conectividade.

## 📌 Visão Geral
A solução resolve o problema de inconsistência de configurações através da automação de quatro pilares:
1.  **Inventário Dinâmico:** Sincronização automática de dados YAML com a API do NetBox.
2.  **Orquestração de Topologia:** Geração programática de cenários de laboratório baseados em grafos de conectividade.
3.  **Provisionamento Idempotente:** Configuração de interfaces, VLANs e protocolos de routing (OSPF) via Python.
4.  **Continuous Verification:** Testes automatizados para garantir o estado pretendido da rede.

---

## 🏗️ Fluxo de Trabalho (Pipeline de Automação)

O diagrama abaixo ilustra a interação entre as ferramentas e o fluxo de dados no ecossistema:

```mermaid
graph TD
    %% Fontes de Dados
    subgraph SSoT [Fontes de Dados YAML]
        Y1[devices.yml]
        Y2[connections.yml]
        Y3[ips.yml]
    end

    %% Processamento
    subgraph Logic [Scripts de Automação]
        S1[netbox_init.py]
        S2[generate_clab.py]
        S3[sync_netbox_lab.py]
    end

    %% Destinos
    subgraph Infrastructure [Infraestrutura]
        NB[(NetBox API)]
        CL[Containerlab]
        FRR[FRRouting Nodes]
    end

    Y1 & Y2 & Y3 --> S1
    S1 --> NB
    
    Y2 --> S2
    S2 --> CL
    
    NB --> S3
    S3 --> FRR
    
    FRR -->|Validação| V[verify_network.py]
    
    style NB fill:#f96,stroke:#333
    style CL fill:#69f,stroke:#333
    style V fill:#c8e6c9,stroke:#2e7d32

🛠️ Stack Tecnológica
Ferramenta	Função
NetBox	Gestão de IPAM e DCIM (Source of Truth)
Containerlab	Orquestração de topologias de rede em Docker
FRRouting (FRR)	Stack de protocolos de routing (OSPF)
Python 3.x	Core da automação (pynetbox, PyYAML)
Docker	Virtualização dos nós de rede

📂 Estrutura do Projeto

    netbox_init.py: Inicializa o NetBox com sites, roles, modelos e IPs.

    generate_clab.py: Gera o ficheiro de topologia projeto.clab.yml.

    sync_netbox_lab.py: Sincroniza as configurações de IP e OSPF nos equipamentos ativos.

    verify_network.py: Script de validação de vizinhança OSPF e testes de ICMP.

    *.yml: Ficheiros de definição de rede (Inventário, Conexões, Prefixos).

🚀 Como Executar
1. Pré-requisitos

    Docker e Containerlab instalados.

    Instância do NetBox acessível via API.

    Ambiente Python configurado:
    Bash

    pip install -r requirements.txt

2. Passo a Passo

    Popular o NetBox:
    Bash

    python3 netbox_init.py

    Levantar o Laboratório:
    Bash

    sudo clab deploy -t projeto.clab.yml

    Configurar a Rede:
    Bash

    python3 sync_netbox_lab.py

    Validar Conectividade:
    Bash

    python3 verify_network.py

💡 Key Features Implementadas

    Mapeamento Inteligente: Tradução automática de interfaces Cisco para nomes nativos do Linux (ethX).

    OSPF Dinâmico: Ativação automática de áreas OSPF baseada na função de cada interface e Router-ID dinâmico.

    Isolamento de Erros: Gestão de ficheiros PID e locks de processos FRR para garantir estabilidade operacional.

    Flexibilidade: Topologia escalável através de ficheiros de configuração agnósticos ao código.

👤 Autor

Daniel Veloso * LinkedIn: daniel-veloso-it

    Contacto: 912678262