#!/usr/bin/env python3
"""
NET-08: Network Digital Twin
Topología Mininet — ISP simulado con 10 nodos
Autor: Carlos David Rodriguez Lopez
"""
from mininet.net import Mininet
from mininet.node import OVSSwitch, Controller
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
import time
import threading


class ISPTopology(Topo):
    """
    Topología ISP de 3 niveles:
      Core:         2 routers (c1, c2)
      Distribución: 3 switches (d1, d2, d3)
      Acceso:       5 hosts (h1..h5)
    """

    def build(self):
        # --- Core ---
        c1 = self.addSwitch('c1', cls=OVSSwitch)
        c2 = self.addSwitch('c2', cls=OVSSwitch)

        # --- Distribución ---
        d1 = self.addSwitch('d1', cls=OVSSwitch)
        d2 = self.addSwitch('d2', cls=OVSSwitch)
        d3 = self.addSwitch('d3', cls=OVSSwitch)

        # --- Acceso (hosts) ---
        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        h3 = self.addHost('h3', ip='10.0.2.1/24')
        h4 = self.addHost('h4', ip='10.0.2.2/24')
        h5 = self.addHost('h5', ip='10.0.3.1/24')

        # --- Links Core (1 Gbps, latencia baja) ---
        self.addLink(c1, c2, bw=1000, delay='1ms', cls=TCLink)

        # --- Links Core → Distribución (100 Mbps) ---
        self.addLink(c1, d1, bw=100, delay='2ms', cls=TCLink)
        self.addLink(c1, d2, bw=100, delay='2ms', cls=TCLink)
        self.addLink(c2, d2, bw=100, delay='2ms', cls=TCLink)
        self.addLink(c2, d3, bw=100, delay='2ms', cls=TCLink)

        # --- Links Distribución → Acceso (10 Mbps) ---
        self.addLink(d1, h1, bw=10, delay='5ms', cls=TCLink)
        self.addLink(d1, h2, bw=10, delay='5ms', cls=TCLink)
        self.addLink(d2, h3, bw=10, delay='5ms', cls=TCLink)
        self.addLink(d2, h4, bw=10, delay='5ms', cls=TCLink)
        self.addLink(d3, h5, bw=10, delay='5ms', cls=TCLink)


def inject_congestion(net, host_name: str, duration: int = 30):
    """Inyecta congestión sintética para entrenar el modelo."""
    info(f'[DT] Inyectando congestión en {host_name} por {duration}s\n')
    host = net.get(host_name)
    host.cmd(f'iperf3 -c 10.0.2.1 -t {duration} -b 9M &')


def run():
    setLogLevel('info')
    topo = ISPTopology()
    net = Mininet(
        topo=topo,
        controller=Controller,
        link=TCLink,
        autoSetMacs=True
    )
    net.start()
    info('[DT] Red iniciada. Topología ISP activa.\n')
    info('[DT] Hosts: h1=10.0.1.1, h2=10.0.1.2, h3=10.0.2.1, h4=10.0.2.2, h5=10.0.3.1\n')

    # Test de conectividad inicial
    info('[DT] Ejecutando ping all...\n')
    net.pingAll()

    # Inicia CLI para exploración manual
    CLI(net)
    net.stop()


if __name__ == '__main__':
    run()
