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
            
            # Validate proxy format
            self.proxies = [
                p.strip()
                for p in self.proxies
                if p.strip().startswith(("http://", "https://", "socks4://", "socks5://"))
            ]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Valid Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

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
    
    async def user_login(self, account: str, proxy=None, retries=3):
        url = "https://api.zeroswallet.com/login"
        data = FormData()
        data.add_field("uid", account)
        
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.post(
                        url=url,
                        headers=self.headers,
                        data=data,
                        proxy=proxy
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("token")
            except Exception as e:
                self.log(f"{Fore.RED}Attempt {attempt+1}/{retries} failed for {self.mask_account(account)}: {str(e)}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
        return None
            
    async def user_confirm(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com//addreferral"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy
                ) as response:
                    await response.json()
        except Exception as e:
            self.log(f"{Fore.YELLOW}Referral confirmation failed: {str(e)}{Style.RESET_ALL}")

    async def user_balance(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com/auth/mywallet"
        data = FormData()
        data.add_field("token", token)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy
                ) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"{Fore.RED}Balance check failed: {str(e)}{Style.RESET_ALL}")
            return None
            
    async def perform_checkin(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com/task"
        data = FormData()
        data.add_field("token", token)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy
                ) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"{Fore.RED}Check-in failed: {str(e)}{Style.RESET_ALL}")
            return None
        
    async def process_accounts(self, account: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(account) if use_proxy else None

        for attempt in range(3):
            token = await self.user_login(account, proxy)
            if token:
                break
            proxy = self.rotate_proxy_for_account(account) if use_proxy else None
        else:
            self.log(f"{Fore.RED}Login failed after 3 attempts{Style.RESET_ALL}")
            return

        await self.user_confirm(token, proxy)

        self.log(f"{Fore.GREEN}Login successful | Proxy: {proxy}{Style.RESET_ALL}")

        # Check balance
        wallet = await self.user_balance(token, proxy)
        if wallet and "data" in wallet:
            points = next(
                (item["balance"] for item in wallet["data"] if item["coin_id"] == "3"),
                0
            )
            self.log(f"{Fore.CYAN}Current Balance: {points} POINTS{Style.RESET_ALL}")
        else:
            self.log(f"{Fore.YELLOW}Failed to get balance{Style.RESET_ALL}")

        # Perform check-in
        check_in = await self.perform_checkin(token, proxy)
        if check_in and check_in.get("success"):
            self.log(f"{Fore.GREEN}Check-in successful!{Style.RESET_ALL}")
        else:
            msg = check_in.get("message", "Unknown error") if check_in else "No response"
            self.log(f"{Fore.YELLOW}Check-in failed: {msg}{Style.RESET_ALL}")
        
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in [1, 2]

            self.clear_terminal()
            self.welcome()
            self.log(f"Processing {len(accounts)} accounts")

            if use_proxy:
                await self.load_proxies(use_proxy_choice)
                if not self.proxies:
                    self.log(f"{Fore.RED}No valid proxies available, switching to no proxy mode{Style.RESET_ALL}")
                    use_proxy = False

            for account in accounts:
                if not account:
                    continue
                self.log(f"{Fore.CYAN}Processing {self.mask_account(account)}{Style.RESET_ALL}")
                await self.process_accounts(account, use_proxy)
                await asyncio.sleep(3)

            self.log(f"{Fore.GREEN}All accounts processed!{Style.RESET_ALL}")

        except Exception as e:
            self.log(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = ZerosWallet()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Bot interrupted by user{Style.RESET_ALL}")
