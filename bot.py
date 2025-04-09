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
        self.max_retries = 3  # Added max retries constant

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
    # ... [Keep all helper methods same until process_accounts] ...

    async def process_accounts(self, account: str, use_proxy: bool):
        retry_count = 0
        success = False
        
        while not success and retry_count < self.max_retries:
            proxy = self.get_next_proxy_for_account(account) if use_proxy else None
            try:
                # Login
                token = await self.user_login(account, proxy)
                if not token:
                    raise Exception("Login failed")

                # Confirm referral
                confirm_res = await self.user_confirm(token, proxy)
                if not confirm_res or "success" not in confirm_res:
                    raise Exception("Referral confirmation failed")

                # Get balance
                wallet = await self.user_balance(token, proxy)
                points = next((item.get("balance", 0) for item in wallet.get("data", []) 
                            if item.get("coin_id") == "3") if wallet else 0)

                # Check-in
                check_in = await self.perform_checkin(token, proxy)
                if not check_in or "success" not in check_in:
                    raise Exception("Check-in failed")

                # Log results
                self.log(f"{Fore.GREEN}Success | Balance: {points} POINTS{Style.RESET_ALL}")
                success = True

            except Exception as e:
                self.log(f"{Fore.RED}Attempt {retry_count + 1} failed: {str(e)}{Style.RESET_ALL}")
                retry_count += 1
                
                # Rotate proxy on failure
                if use_proxy:
                    new_proxy = self.rotate_proxy_for_account(account)
                    self.log(f"{Fore.YELLOW}Rotating proxy to: {new_proxy}{Style.RESET_ALL}")
                
                await asyncio.sleep(5)  # Add delay between retries

        if not success:
            self.log(f"{Fore.RED}Failed after {self.max_retries} attempts{Style.RESET_ALL}")

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in [1, 2]

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(f"{Fore.CYAN}Accounts loaded: {len(accounts)}{Style.RESET_ALL}")

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                    # Validate proxies before starting
                    if not self.proxies:
                        self.log(f"{Fore.RED}No valid proxies available!{Style.RESET_ALL}")
                        return

                # Process accounts with fresh proxy each cycle
                self.account_proxies = {}  # Reset proxy assignments
                self.proxy_index = 0

                for account in accounts:
                    if account:
                        self.log(f"{'='*30} Processing {self.mask_account(account)} {'='*30}")
                        await self.process_accounts(account, use_proxy)
                        await asyncio.sleep(3)  # Add delay between accounts

                self.log(f"{Fore.CYAN}Cycle completed. Restarting in 12 hours...{Style.RESET_ALL}")
                await self.countdown_timer(43200)  # 12 hours in seconds

        except Exception as e:
            self.log(f"{Fore.RED}Critical error: {str(e)}{Style.RESET_ALL}")

    async def countdown_timer(self, seconds):
        while seconds > 0:
            mins, secs = divmod(seconds, 60)
            hours, mins = divmod(mins, 60)
            timer = f"{hours:02d}:{mins:02d}:{secs:02d}"
            print(f"{Fore.YELLOW}Next cycle in: {timer}{Style.RESET_ALL}", end="\r")
            await asyncio.sleep(1)
            seconds -= 1

if __name__ == "__main__":
    try:
        asyncio.run(ZerosWallet().main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Bot terminated by user{Style.RESET_ALL}")
