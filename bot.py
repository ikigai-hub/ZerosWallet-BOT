from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    FormData
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, os, pytz, random, ssl
from collections import deque
from typing import Optional, List, Dict

wib = pytz.timezone('Asia/Jakarta')

class ZerosWallet:
    def __init__(self) -> None:
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.zeroswallet.com",
            "Referer": "https://app.zeroswallet.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        self.code = "ee1364ef82"
        self.valid_proxies = deque()
        self.failed_proxies = set()
        self.proxy_failure_count: Dict[str, int] = {}
        self.account_proxies: Dict[str, str] = {}
        self.MAX_PROXY_FAILURES = 5
        self.semaphore = asyncio.Semaphore(15)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.MAX_PROXIES = 90
        self.PROXY_RETRIES = 10

    def get_headers(self) -> Dict[str, str]:
        return {**self.base_headers, "User-Agent": FakeUserAgent().random}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message: str):
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

    def format_seconds(self, seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def validate_proxy(self, proxy: str) -> bool:
        """Validate proxy connection to multiple endpoints"""
        try:
            connector = ProxyConnector.from_url(proxy, ssl=self.ssl_context)
            async with ClientSession(
                connector=connector, 
                timeout=ClientTimeout(total=15)
            ) as session:
                # Test Google endpoint
                async with session.get("https://www.google.com") as google_resp:
                    if google_resp.status != 200:
                        return False
                
                # Test API endpoint
                async with session.get("https://api.zeroswallet.com") as api_resp:
                    return api_resp.status == 200
                
        except Exception:
            return False

    async def load_proxies(self, use_proxy_choice: int):
        """Load and validate 90 proxies"""
        try:
            proxies = []
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        content = await response.text()
                        proxies = content.splitlines()[:self.MAX_PROXIES]
            elif use_proxy_choice == 2:
                with open('proxy.txt', 'r') as f:
                    proxies = [line.strip() for idx, line in enumerate(f) if idx < self.MAX_PROXIES]

            validation_tasks = [self.validate_proxy(p) for p in proxies]
            results = await asyncio.gather(*validation_tasks)
            
            self.valid_proxies = deque([p for p, valid in zip(proxies, results) if valid])
            self.log(f"Loaded {len(self.valid_proxies)}/{self.MAX_PROXIES} valid proxies")

        except Exception as e:
            self.log(f"{Fore.RED}Proxy loading failed: {str(e)}{Style.RESET_ALL}")

    def get_proxy_for_account(self, account: str) -> Optional[str]:
        """Get proxy with smart rotation"""
        if account in self.account_proxies:
            current_proxy = self.account_proxies[account]
            if self.proxy_failure_count.get(current_proxy, 0) < self.MAX_PROXY_FAILURES:
                return current_proxy
                
        if self.valid_proxies:
            proxy = self.valid_proxies.popleft()
            self.account_proxies[account] = proxy
            self.valid_proxies.append(proxy)
            return proxy
        return None

    async def make_request(self, method: str, url: str, data: Optional[FormData] = None, 
                         proxy: Optional[str] = None, max_retries: int = 5) -> Optional[dict]:
        """Enhanced request handler with 5 retries"""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(random.uniform(1, 3))
                connector = ProxyConnector.from_url(proxy, ssl=self.ssl_context) if proxy else None
                
                async with ClientSession(
                    connector=connector,
                    timeout=ClientTimeout(total=40),
                    headers=self.get_headers()
                ) as session:
                    async with session.request(method, url, data=data) as response:
                        response.raise_for_status()
                        return await response.json()

            except ClientResponseError as e:
                if e.status == 429:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    await asyncio.sleep(backoff)
                if proxy:
                    self.handle_proxy_failure(proxy)
            except Exception as e:
                if proxy:
                    self.handle_proxy_failure(proxy)
                await asyncio.sleep(random.uniform(1, 2))
                
        return None

    def handle_proxy_failure(self, proxy: str):
        self.proxy_failure_count[proxy] = self.proxy_failure_count.get(proxy, 0) + 1
        if self.proxy_failure_count[proxy] >= self.MAX_PROXY_FAILURES:
            self.failed_proxies.add(proxy)
            try:
                self.valid_proxies.remove(proxy)
            except ValueError:
                pass

    def mask_account(self, account: str) -> str:
        return account[:6] + '*' * 6 + account[-6:]

    async def user_login(self, account: str, proxy: Optional[str]) -> Optional[str]:
        data = FormData()
        data.add_field("uid", account)
        result = await self.make_request("POST", "https://api.zeroswallet.com/login", 
                                       data=data, proxy=proxy)
        return result.get("token") if result else None

    async def user_confirm(self, token: str, proxy: Optional[str]) -> Optional[dict]:
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        return await self.make_request("POST", "https://api.zeroswallet.com/addreferral", 
                                    data=data, proxy=proxy)

    async def user_balance(self, token: str, proxy: Optional[str]) -> Optional[dict]:
        data = FormData()
        data.add_field("token", token)
        return await self.make_request("POST", "https://api.zeroswallet.com/auth/mywallet", 
                                     data=data, proxy=proxy)

    async def perform_checkin(self, token: str, proxy: Optional[str]) -> Optional[dict]:
        data = FormData()
        data.add_field("token", token)
        return await self.make_request("POST", "https://api.zeroswallet.com/task", 
                                    data=data, proxy=proxy)

    async def process_account(self, account: str, use_proxy: bool):
        for _ in range(self.PROXY_RETRIES):
            proxy = self.get_proxy_for_account(account) if use_proxy else None
            try:
                async with self.semaphore:
                    token = await self.user_login(account, proxy)
                    if not token:
                        continue
                        
                    await self.user_confirm(token, proxy)
                    balance = await self.user_balance(token, proxy)
                    checkin = await self.perform_checkin(token, proxy)
                    
                    self.log(f"{Fore.GREEN}Success: {self.mask_account(account)}")
                    self.log(f"Proxy: {proxy or 'Direct'} | Balance: {balance} | Checkin: {checkin}")
                    return
                    
            except Exception as e:
                self.log(f"{Fore.YELLOW}Attempt failed: {str(e)}{Style.RESET_ALL}")
                continue

        try:
            async with self.semaphore:
                token = await self.user_login(account, None)
                if token:
                    await self.user_confirm(token, None)
                    self.log(f"{Fore.CYAN}Fallback success: {self.mask_account(account)}{Style.RESET_ALL}")
        except Exception:
            self.log(f"{Fore.RED}Complete failure: {self.mask_account(account)}{Style.RESET_ALL}")

    async def main(self):
        try:
            self.clear_terminal()
            self.welcome()
            
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            self.log(f"{Fore.CYAN}Loaded {len(accounts)} accounts{Style.RESET_ALL}")

            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in (1, 2)
            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            batch_size = 20
            for i in range(0, len(accounts), batch_size):
                batch = accounts[i:i+batch_size]
                tasks = [self.process_account(acc, use_proxy) for acc in batch]
                await asyncio.gather(*tasks)
                delay = random.uniform(5, 15)
                self.log(f"{Fore.MAGENTA}Next batch in {delay:.1f}s...{Style.RESET_ALL}")
                await asyncio.sleep(delay)

            self.log(f"{Fore.CYAN}All accounts processed. Cycling...{Style.RESET_ALL}")
            while True:
                await asyncio.sleep(43200)
                await self.main()

        except KeyboardInterrupt:
            self.log(f"{Fore.RED}Process interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED}Critical error: {str(e)}{Style.RESET_ALL}")

    def print_question(self) -> int:
        while True:
            try:
                print(f"{Fore.CYAN}Choose proxy mode:")
                print("1. Use public proxies")
                print("2. Use private proxies")
                print("3. No proxies")
                choice = int(input("Selection [1-3]: "))
                if 1 <= choice <= 3:
                    return choice
                print(f"{Fore.RED}Invalid choice{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Enter a number{Style.RESET_ALL}")

if __name__ == "__main__":
    bot = ZerosWallet()
    asyncio.run(bot.main())
