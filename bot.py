from aiohttp import ClientResponseError, ClientSession, ClientTimeout, FormData
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
        self.max_retries = 3
        self.current_retries = 0

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
            
            self.proxies = [p.strip() for p in self.proxies if p.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(f"Loaded {len(self.proxies)} proxies")
        
        except Exception as e:
            self.log(f"Proxy load failed: {str(e)}")
            self.proxies = []

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.proxies[self.proxy_index % len(self.proxies)]
            self.account_proxies[token] = proxy
            self.proxy_index += 1
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.account_proxies[token] = proxy
        self.proxy_index += 1
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
                return choose
            except ValueError:
                print("Invalid input")
    
    async def user_login(self, account: str, proxy=None, retries=3):
        url = "https://api.zeroswallet.com/login"
        data = FormData()
        data.add_field("uid", account)
        
        for attempt in range(retries):
            try:
                connector = None
                if proxy:
                    from aiohttp_socks import ProxyConnector
                    connector = ProxyConnector.from_url(proxy)
                
                async with ClientSession(
                    connector=connector,
                    timeout=ClientTimeout(total=30)
                ) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        if response.status != 200:
                            continue
                        return (await response.json()).get("token")
            except Exception as e:
                self.log(f"Login attempt {attempt+1} failed: {str(e)}")
                await asyncio.sleep(2)
        
        return None
            
    async def user_confirm(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com//addreferral"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        
        try:
            connector = None
            if proxy:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy)
            
            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=30)
            ) as session:
                async with session.post(url=url, headers=self.headers, data=data) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"Confirm failed: {str(e)}")
            return None
            
    async def user_balance(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com/auth/mywallet"
        data = FormData()
        data.add_field("token", token)
        
        try:
            connector = None
            if proxy:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy)
            
            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=30)
            ) as session:
                async with session.post(url=url, headers=self.headers, data=data) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"Balance check failed: {str(e)}")
            return None
            
    async def perform_checkin(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com/task"
        data = FormData()
        data.add_field("token", token)
        
        try:
            connector = None
            if proxy:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy)
            
            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=30)
            ) as session:
                async with session.post(url=url, headers=self.headers, data=data) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"Checkin failed: {str(e)}")
            return None
        
    async def process_accounts(self, account: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(account) if use_proxy else None
        self.current_retries = 0
        
        while self.current_retries < self.max_retries:
            token = await self.user_login(account, proxy)
            if not token:
                self.current_retries += 1
                if use_proxy:
                    proxy = self.rotate_proxy_for_account(account)
                await asyncio.sleep(3)
                continue
            
            try:
                # Process account operations
                await self.user_confirm(token, proxy)
                wallet = await self.user_balance(token, proxy)
                check_in = await self.perform_checkin(token, proxy)

                # Display results
                self.log(f"Login Success | Proxy: {proxy or 'None'}")
                if wallet:
                    points = next((i.get("balance", 0) for i in wallet.get("data", []) if i.get("coin_id") == "3")
                    self.log(f"Balance: {points} POINTS")
                self.log("Check-In: " + ("Claimed" if check_in and check_in.get("success") else "Failed"))
                
                return  # Success - exit loop
            
            except Exception as e:
                self.log(f"Processing error: {str(e)}")
                self.current_retries += 1
                if use_proxy:
                    proxy = self.rotate_proxy_for_account(account)
                await asyncio.sleep(5)
        
        self.log(f"Failed after {self.max_retries} attempts")
        
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            choice = self.print_question()
            use_proxy = choice in [1, 2]

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(f"Processing {len(accounts)} accounts")

                if use_proxy:
                    await self.load_proxies(choice)
                    if not self.proxies:
                        self.log("No proxies available!")
                        return

                for account in accounts:
                    if account:
                        self.log(f"Processing {self.mask_account(account)}")
                        await self.process_accounts(account, use_proxy)
                        await asyncio.sleep(3)

                self.log("Cycle complete - restarting in 12 hours")
                await self.countdown_timer(43200)

        except Exception as e:
            self.log(f"Fatal error: {str(e)}")

    async def countdown_timer(self, seconds):
        while seconds > 0:
            print(f"Next cycle: {self.format_seconds(seconds)}", end="\r")
            await asyncio.sleep(1)
            seconds -= 1

if __name__ == "__main__":
    try:
        asyncio.run(ZerosWallet().main())
    except KeyboardInterrupt:
        print("\nBot terminated")
