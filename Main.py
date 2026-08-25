import os
import sys
import time
import socket
import random
import ssl
import json
import subprocess
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    print("\033[1;31m[!] Missing required library 'rich'. Install using: pip install rich\033[0m")

    class SimpleConsole:
        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            clean = text.replace('[bold green]', '').replace('[/bold green]', '') \
                        .replace('[bold cyan]', '').replace('[/bold cyan]', '') \
                        .replace('[bold red]', '').replace('[/bold red]', '') \
                        .replace('[bold yellow]', '').replace('[/bold yellow]', '')
            print(clean)

    console = SimpleConsole()
    class PromptFallback:
        @staticmethod
        def ask(prompt, choices=None, default=None):
            if choices:
                opts = '/'.join(choices)
                raw = input(f"{prompt} ({opts}) [{default}]: ").strip()
            else:
                raw = input(f"{prompt}: ").strip()
            return raw if raw else str(default)
    Prompt = PromptFallback


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def display_logo():
    logo = r"""

                       ______     __   __     __  __     __    __                   ______     ______     ______     ______     __   __    
   _______            /\  ___\   /\ "-.\ \   /\ \/\ \   /\ "-./  \        ______   /\  == \   /\  ___\   /\  ___\   /\  __ \   /\ "-.\ \   
  /\ o o o\           \ \  __\   \ \ \-.  \  \ \ \_\ \  \ \ \-./\ \      /\_____\  \ \  __<   \ \  __\   \ \ \____  \ \ \/\ \  \ \ \-.  \  
 /o \ o o o\________   \ \_____\  \ \_\\"\_\  \ \_____\  \ \_\ \ \_\     \/_____/   \ \_\ \_\  \ \_____\  \ \_____\  \ \_____\  \ \_\\"\_\ 
<    >------>    o /|   \/_____/   \/_/ \/_/   \/_____/   \/_/  \/_/                 \/_/ /_/   \/_____/   \/_____/   \/_____/   \/_/ \/_/ 
  \   o/  o /_____/o|
   \/______/     |oo|                              
         |   o   |o/
         |_______|/                                                                                                   
    """
    if RICH_AVAILABLE:
        console.print(Panel(logo, title="Advanced Security & Recon Framework", subtitle="Released by: Mohamed Ragheb | DarkRagheb", style="bold cyan"))
    else:
        print(logo)
        print("Released by: Mohamed Ragheb | GitHub: DarkRagheb\n")


def display_menu(title, options, exit_text="Exit"):
    if RICH_AVAILABLE:
        table = Table(title=title, title_style="bold yellow", border_style="bold cyan", expand=True)
        table.add_column("Option", justify="center", style="bold green", width=10)
        table.add_column("Module Name / Functionality", justify="left", style="bold white")
        for idx, opt in enumerate(options, start=1):
            table.add_row(f"[{idx:02d}]", opt)
        table.add_section()
        table.add_row("[00]", f"[bold red]{exit_text}[/bold red]")
        console.print(table)
    else:
        print(f"\n=== {title} ===")
        for idx, opt in enumerate(options, start=1):
            print(f"[{idx:02d}] {opt}")
        print(f"[00] {exit_text}")


def grab_banner(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        
        if port in [443, 8443, 465, 993, 995]:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            s = context.wrap_socket(s, server_hostname=ip)
            
        s.connect((ip, port))
           
        if port in [80, 8080, 8000]:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
            ]
            req = f"GET / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: {random.choice(user_agents)}\r\n\r\n"
            s.sendall(req.encode())
        else:
            s.sendall(b"\r\n")

        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        return banner if banner else "Unknown Service"
    except Exception:
        try:
            return socket.getservbyport(port, "tcp")
        except Exception:
            return "Unknown"



def stealth_scan_port(ip, port, open_ports, evasion=False):
    try:
        if evasion:
            time.sleep(random.uniform(0.01, 0.08))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.2)
        result = s.connect_ex((ip, port))
        
        if result == 0:
            service_info = grab_banner(ip, port)
            open_ports.append((port, service_info))
            if RICH_AVAILABLE:
                console.print(f"[bold green][+] Port {port:<5} | State: OPEN | Service: {service_info[:40]}[/bold green]")
            else:
                print(f"[+] Port {port:<5} | OPEN | Service: {service_info[:40]}")
        s.close()
    except Exception:
        pass


def run_port_scanner():
    clear_screen()
    display_logo()
    
    target_host = input("Enter Target IP/Domain: ").strip()
    if not target_host:
        return

    try:
        target_ip = socket.gethostbyname(target_host)
    except socket.gaierror:
        console.print("[bold red][-] Hostname resolution failed.[/bold red]")
        input("\nPress Enter to return...")
        return

    print("\nSelect Port Range:")
    print("1. Top Common Ports (1-1024)")
    print("2. Extended Ports Range (1-10000)")
    print("3. Full Range (1-65535)")
    range_choice = input("Choice [1-3] (Default 1): ").strip() or "1"
    
    port_limits = {"1": 1024, "2": 10000, "3": 65535}
    end_port = port_limits.get(range_choice, 1024)

    evasion = input("Enable WAF/IDS Evasion (Delay & Randomization) [y/N]: ").strip().lower() == 'y'
    threads = int(input("Threads (Default 150): ").strip() or "150")

    console.print(f"\n[bold yellow][i] Target: {target_ip} | Range: 1-{end_port} | Evasion: {evasion}[/bold yellow]\n")

    open_ports = []
    ports = list(range(1, end_port + 1))
    
    if evasion:
        random.shuffle(ports)

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for port in ports:
            executor.submit(stealth_scan_port, target_ip, port, open_ports, evasion)

    duration = time.time() - start_time
    console.print(f"\n[bold green][+] Scan finished in {duration:.2f}s. Total Open Ports: {len(open_ports)}[/bold green]")
    input("\nPress Enter to return...")


def run_ping_check():
    clear_screen()
    display_logo()
    target = input("Enter Target IP/Domain to Ping: ").strip()
    if not target:
        return
    
    param = '-n' if os.name == 'nt' else '-c'
    command = ['ping', param, '4', target]
    
    console.print(f"\n[bold yellow][i] Pinging {target}...[/bold yellow]\n")
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(res.stdout)
    input("\nPress Enter to return...")


def fetch_crt_sh(domain):
    found = set()
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                for entry in data:
                    name_value = entry.get('name_value', '')
                    for sub in name_value.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and not sub.startswith('*'):
                            found.add(sub)
    except Exception:
        pass
    return found


def fetch_hackertarget(domain):
    found = set()
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                lines = response.read().decode('utf-8').splitlines()
                for line in lines:
                    if ',' in line:
                        sub = line.split(',')[0].strip().lower()
                        if sub.endswith(domain):
                            found.add(sub)
    except Exception:
        pass
    return found


def resolve_subdomain(subdomain):
    try:
        ip = socket.gethostbyname(subdomain)
        return subdomain, ip
    except Exception:
        return subdomain, None


def run_subdomain_finder():
    clear_screen()
    display_logo()
    
    domain = input("Enter Target Domain (e.g. example.com): ").strip().lower()
    if not domain:
        return

    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]

    console.print(f"\n[bold yellow][i] Gathering Subdomains for: {domain}[/bold yellow]")

    discovered_subdomains = set()

    if RICH_AVAILABLE:
        console.print("[bold cyan][*] Querying SSL Certificate Transparency Logs (crt.sh)...[/bold cyan]")
    else:
        print("[*] Querying SSL Certificate Transparency Logs (crt.sh)...")
    
    crt_subs = fetch_crt_sh(domain)
    discovered_subdomains.update(crt_subs)
    console.print(f"[bold green]  └─ Found {len(crt_subs)} unique entries via SSL Logs.[/bold green]")

    if RICH_AVAILABLE:
        console.print("[bold cyan][*] Querying HackerTarget Passive DNS...[/bold cyan]")
    else:
        print("[*] Querying HackerTarget Passive DNS...")

    ht_subs = fetch_hackertarget(domain)
    discovered_subdomains.update(ht_subs)
    console.print(f"[bold green]  └─ Found {len(ht_subs)} entries via HackerTarget.[/bold green]")

    common_wordlist = [
        "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
        "smtp", "secure", "vpn", "api", "dev", "staging", "test", "portal",
        "admin", "dashboard", "cpanel", "whm", "store", "shop", "ftp", "m",
        "auth", "login", "cloud", "app", "git", "gitlab", "jira", "status",
        "monitor", "database", "db", "mysql", "redis", "elastic", "jenkins",
        "s3", "assets", "static", "cdn", "media", "vps", "node", "support"
    ]

    for word in common_wordlist:
        discovered_subdomains.add(f"{word}.{domain}")

    console.print(f"\n[bold yellow][i] Resolving IPs for {len(discovered_subdomains)} accumulated targets...[/bold yellow]\n")

    valid_results = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(resolve_subdomain, sub) for sub in discovered_subdomains]
        for future in futures:
            subdomain, ip = future.result()
            if ip:
                valid_results.append((subdomain, ip))
                if RICH_AVAILABLE:
                    console.print(f"[bold green][+] Resolved: {subdomain:<35} -> {ip}[/bold green]")
                else:
                    print(f"[+] Resolved: {subdomain:<35} -> {ip}")

    if RICH_AVAILABLE:
        table = Table(title=f"Subdomain Discovery Results ({domain})", border_style="bold green", expand=True)
        table.add_column("Subdomain", style="bold cyan")
        table.add_column("IP Address", style="bold yellow")

        for sub, ip in valid_results:
            table.add_row(sub, ip)
        
        console.print("\n", table)
    else:
        print(f"\n=== Summary: Found {len(valid_results)} Active Subdomains ===")

    input("\nPress Enter to return to main menu...")


def main():
    while True:
        clear_screen()
        display_logo()
        
        options = [
            "Advanced Port & Service Scanner (WAF Evasion & Banner Grab)",
            "System ICMP Ping Check",
            "Subdomain Enumerator (Passive SSL/DNS Recon + Active DNS Resolution)"
        ]
        
        display_menu("MAIN CONTROL CENTER", options, exit_text="Exit Framework")
        choice = input("\nSelect Option: ").strip()
        
        if choice in ["0", "00"]:
            console.print("[bold red]Exiting framework... Goodbye![/bold red]")
            sys.exit(0)
        elif choice in ["1", "01"]:
            run_port_scanner()
        elif choice in ["2", "02"]:
            run_ping_check()
        elif choice in ["3", "03"]:
            run_subdomain_finder()


if __name__ == "__main__":
    main()
