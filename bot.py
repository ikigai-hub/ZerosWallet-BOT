from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    FormData
)
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class ZerosWallet:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.zeroswallet.com",
            "Referer": "https://app.zeroswallet.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.code = "ee1364ef82"
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}Zeros Wallet - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            self.proxies = [self.check_proxy_schemes(p) for p in self.proxies if p.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxy):
        if proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            return proxy
        return f"http://{proxy}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.proxies[self.proxy_index]
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        return account[:6] + '*' * 6 + account[-6:]
        
    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")
    
    async def user_login(self, account: str, proxy=None, retries=5):
        url = "https://api.zeroswallet.com/login"
        data = FormData()
        data.add_field("uid", account)
        
        for attempt in range(retries):
            try:
                async with ClientSession(
                    timeout=ClientTimeout(total=60),
                    proxy=proxy if proxy else None
                ) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["token"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def user_confirm(self, token: str, proxy=None, retries=5):
        url = "https://api.zeroswallet.com//addreferral"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        
        for attempt in range(retries):
            try:
                async with ClientSession(
                    timeout=ClientTimeout(total=60),
                    proxy=proxy if proxy else None
                ) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def user_balance(self, token: str, proxy=None, retries=5):
        url = "https://api.zeroswallet.com/auth/mywallet"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        
        for attempt in range(retries):
            try:
                async with ClientSession(
                    timeout=ClientTimeout(total=60),
                    proxy=proxy if proxy else None
                ) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def perform_checkin(self, token: str, proxy=None, retries=5):
        url = "https://api.zeroswallet.com/task"
        data = FormData()
        data.add_field("token", token)
        
        for attempt in range(retries):
            try:
                async with ClientSession(
                    timeout=ClientTimeout(total=60),
                    proxy=proxy if proxy else None
                ) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
        
    async def process_accounts(self, account: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(account) if use_proxy else None

        token = None
        while token is None:
            token = await self.user_login(account, proxy)
            if not token:
                self.log(f"{Fore.RED + Style.BRIGHT}Login Failed {Style.RESET_ALL}")
                proxy = self.rotate_proxy_for_account(account) if use_proxy else None
                continue

        await self.user_confirm(token, proxy)

        self.log(f"{Fore.GREEN + Style.BRIGHT}Login Success {Style.RESET_ALL}")
        self.log(f"{Fore.WHITE + Style.BRIGHT}Proxy: {proxy or 'No Proxy'} {Style.RESET_ALL}")

        wallet = await self.user_balance(token, proxy)
        if wallet:
            points = next((item.get("balance", 0) for item in wallet.get("data", []) 
                         if item.get("coin_id") == "3"), 0)
            self.log(f"{Fore.WHITE + Style.BRIGHT}Balance: {points} POINT {Style.RESET_ALL}")
        else:
            self.log(f"{Fore.RED + Style.BRIGHT}Balance Data Missing {Style.RESET_ALL}")

        check_in = await self.perform_checkin(token, proxy)
        if check_in and check_in.get("success"):
            self.log(f"{Fore.GREEN + Style.BRIGHT}Check-In: Claimed {Style.RESET_ALL}")
        else:
            self.log(f"{Fore.YELLOW + Style.BRIGHT}Check-In: Already Claimed {Style.RESET_ALL}")
        
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()

            while True:
                use_proxy = use_proxy_choice in [1, 2]
                
                self.clear_terminal()
                self.welcome()
                self.log(f"{Fore.GREEN}Accounts: {len(accounts)}{Style.RESET_ALL}")

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 23
                for account in accounts:
                    if account:
                        self.log(f"{separator}[ {self.mask_account(account)} ]{separator}")
                        await self.process_accounts(account, use_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN}={Style.RESET_ALL}"*68)
                seconds = 12 * 60 * 60
                while seconds > 0:
                    print(f"Waiting {self.format_seconds(seconds)}...", end="\r")
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}accounts.txt missing{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        asyncio.run(ZerosWallet().main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Bot Stopped{Style.RESET_ALL}")
