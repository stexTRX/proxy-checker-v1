import requests
import socket
import threading
import time

class ProxyChecker:
    def __init__(self, proxy_list, check_url):
        self.proxy_list = proxy_list
        self.working_proxies = []
        self.check_url = check_url

    def check_proxy(self, proxy):
        protocol, ip_port = proxy.split("://")
        ip, port = ip_port.split(":")
        port = int(port)

        if protocol == "http" or protocol == "https":
            try:
                proxies = {protocol: f"{protocol}://{ip}:{port}"}
                response = requests.get(self.check_url, proxies=proxies, timeout=5)
                if response.status_code == 200:
                    self.working_proxies.append(proxy)
                    print(f"\033[92m{proxy} is working!\033[0m")  # green color
            except requests.exceptions.RequestException:
                print(f"\033[91m{proxy} is not working.\033[0m")  # red color
        elif protocol == "socks4" or protocol == "socks5":
            try:
                socks_proxy = f"{ip}:{port}"
                socks_version = 4 if protocol == "socks4" else 5
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, port))
                s.send(b"\x04\x01" + bytes([port >> 8, port & 0xFF]) + b"\x00\x01\x00\x00\x00\x00\x00\x00")
                if socks_version == 5:
                    s.send(b"\x05\x01\x00")
                response = s.recv(1024)
                if response and (response[0] == 0x5 and response[1] == 0x0):
                    self.working_proxies.append(proxy)
                    print(f"\033[92m{proxy} is working!\033[0m")  # green color
            except socket.error:
                print(f"\033[91m{proxy} is not working.\033[0m")  # red color

    def start(self, num_threads):
        threads = []
        for proxy in self.proxy_list:
            t = threading.Thread(target=self.check_proxy, args=(proxy,))
            threads.append(t)
            t.start()
            while threading.active_count() > num_threads:
                time.sleep(0.1)  # wait for 0.1 seconds before checking again
        for t in threads:
            t.join()

def load_proxies(filename):
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f]
    return proxies

def main():
    proxy_filename = input("Enter the filename of the proxy list: ")
    proxy_list = load_proxies(proxy_filename)
    num_threads = int(input("Enter the number of threads(5-10 is good dont do more): "))
    check_url = input("Enter the URL to check proxies against: ")

    checker = ProxyChecker(proxy_list, check_url)
    checker.start(num_threads)

    working_proxies_by_protocol = {}
    for proxy in checker.working_proxies:
        protocol, _ = proxy.split("://")
        if protocol in working_proxies_by_protocol:
            working_proxies_by_protocol[protocol] += 1
        else:
            working_proxies_by_protocol[protocol] = 1

    print("Working proxies by protocol:")
    for protocol, count in working_proxies_by_protocol.items():
        print(f"{protocol}: {count}")

    save_filename = input("Enter the filename to save the working proxies: ")
    save_format = input("Enter the save format (1 for protocol://ip:port, 2 for ip:port): ")

    with open(save_filename, 'w') as f:
        for proxy in checker.working_proxies:
            if save_format == "1":
                f.write(f"{proxy}\n")
            elif save_format == "2":
                _, ip_port = proxy.split("://")
                f.write(f"{ip_port}\n")

if __name__ == '__main__':
    main()