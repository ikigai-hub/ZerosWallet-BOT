from aiohttp import ClientSession, ClientTimeout, FormData, ClientResponseError
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import Fore, Style, init
import asyncio
import os
import pytz
import random

# Initialize colorama
init(autoreset=True)
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
        print(f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}Zeros Wallet - BOT
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
        """)

    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()

            # Validate proxy format
            self.proxies = [
                p.strip() for p in self.proxies
                if p.strip().startswith(("http://", "https://"))
            ]
            
            if not self.proxies:
                self.log(f"{Fore.RED}No valid proxies found!")
                return False
                
            self.log(f"{Fore.GREEN}Loaded {len(self.proxies)} proxies")
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED}Proxy load failed: {str(e)}")
            return False

    def get_next_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def mask_account(self, account):
        return account[:6] + '*'*6 + account[-6:]

    async def user_login(self, account: str, proxy=None, retries=3):
        url = "https://api.zeroswallet.com/login"
        data = FormData()
        data.add_field("uid", account)
        
        for attempt in range(retries):
            try:
                # Rotate UA and proxy for each attempt
                self.headers["User-Agent"] = FakeUserAgent().random
                current_proxy = proxy or self.get_next_proxy()

                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.post(
                        url=url,
                        headers=self.headers,
                        data=data,
                        proxy=current_proxy,
                        verify_ssl=False
                    ) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 10))
                            self.log(f"{Fore.YELLOW}Rate limited - retrying in {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        result = await response.json()
                        return result.get("token"), current_proxy

            except Exception as e:
                error_msg = f"{str(e)}"
                if "500" in error_msg:
                    error_msg += " (Bad Proxy)"
                self.log(f"{Fore.RED}Login attempt {attempt+1} failed: {error_msg}")
                
                # Rotate proxy immediately on failure
                current_proxy = self.get_next_proxy()
                
                # Exponential backoff with jitter
                await asyncio.sleep(2 ** (attempt + 1) + random.uniform(0, 1))
                
        return None, None

    async def process_account(self, account: str, use_proxy: bool):
        token, proxy = None, None
        try:
            # Initial randomized delay
            await asyncio.sleep(random.uniform(1, 3))
            
            token, proxy = await self.user_login(account, None, 3)
            if not token:
                return

            # Perform account actions
            await self.perform_checkin(token, proxy)
            await self.check_balance(token, proxy)
            
            # Success delay
            await asyncio.sleep(random.uniform(5, 10))

        except Exception as e:
            self.log(f"{Fore.RED}Account processing failed: {str(e)}")
        finally:
            if proxy:
                self.proxies.append(proxy)  # Recycle proxy

    async def perform_checkin(self, token: str, proxy: str):
        url = "https://api.zeroswallet.com/task"
        data = FormData()
        data.add_field("token", token)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy,
                    verify_ssl=False
                ) as response:
                    result = await response.json()
                    if result.get("success"):
                        self.log(f"{Fore.GREEN}Check-in successful!")
                    else:
                        self.log(f"{Fore.YELLOW}Check-in failed: {result.get('message')}")
        except Exception as e:
            self.log(f"{Fore.RED}Check-in error: {str(e)}")

    async def check_balance(self, token: str, proxy: str):
        url = "https://api.zeroswallet.com/auth/mywallet"
        data = FormData()
        data.add_field("token", token)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy,
                    verify_ssl=False
                ) as response:
                    result = await response.json()
                    if "data" in result:
                        points = next((item["balance"] for item in result["data"] if item["coin_id"] == "3"), 0)
                        self.log(f"{Fore.CYAN}Balance: {points} POINTS")
        except Exception as e:
            self.log(f"{Fore.RED}Balance check failed: {str(e)}")

    async def main(self):
        self.clear_terminal()
        self.welcome()
        
        try:
            with open('accounts.txt', 'r') as f:
                accounts = [line.strip() for line in f if line.strip()]
                
            self.log(f"{Fore.GREEN}Loaded {len(accounts)} accounts")
            
            # Proxy selection
            use_proxy = input(f"{Fore.YELLOW}Use proxies? (y/n): ").lower() == 'y'
            if use_proxy and not await self.load_proxies(2):
                use_proxy = False
                self.log(f"{Fore.YELLOW}Continuing without proxies")
                
            # Process accounts with concurrency control
            semaphore = asyncio.Semaphore(3)  # 3 concurrent requests
            async with semaphore:
                tasks = [self.process_account(acc, use_proxy) for acc in accounts]
                await asyncio.gather(*tasks)
                
        except Exception as e:
            self.log(f"{Fore.RED}Fatal error: {str(e)}")
        finally:
            self.log(f"{Fore.GREEN}Process completed")

if __name__ == "__main__":
    try:
        bot = ZerosWallet()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Operation cancelled by user")
