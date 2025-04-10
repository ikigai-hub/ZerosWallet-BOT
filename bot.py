from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    FormData
)
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, os, pytz, random

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
                if p.strip().startswith(("http://", "https://", "socks4://", "socks5://"))
            ]
            
            if not self.proxies:
                self.log(f"{Fore.RED}No valid proxies found!")
                return False
            
            self.log(f"{Fore.GREEN}Loaded {len(self.proxies)} proxies")
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED}Proxy load failed: {str(e)}")
            return False

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.proxies[self.proxy_index]
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        return account[:6] + '*'*6 + account[-6:]
        
    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    return choose
                else:
                    print(f"{Fore.RED}Please enter 1, 2 or 3")
            except ValueError:
                print(f"{Fore.RED}Invalid input")

    async def user_login(self, account: str, proxy=None, retries=3):
        url = "https://api.zeroswallet.com/login"
        data = FormData()
        data.add_field("uid", account)
        
        for attempt in range(retries):
            try:
                # Rotate User-Agent for each attempt
                self.headers["User-Agent"] = FakeUserAgent().random
                
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.post(
                        url=url,
                        headers=self.headers,
                        data=data,
                        proxy=proxy,
                        verify_ssl=False
                    ) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 10))
                            self.log(f"{Fore.YELLOW}Rate limited. Retrying in {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                            
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("token")
            except Exception as e:
                self.log(f"{Fore.RED}Login attempt {attempt+1} failed: {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1) + random.uniform(0, 1))
                    continue
        return None
            
    async def user_confirm(self, token: str, proxy=None):
        url = "https://api.zeroswallet.com/addreferral"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        
        try:
            async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(
                    url=url,
                    headers=self.headers,
                    data=data,
                    proxy=proxy,
                    verify_ssl=False
                ) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"{Fore.RED}Referral error: {str(e)}")
            return None

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
                    proxy=proxy,
                    verify_ssl=False
                ) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"{Fore.RED}Balance error: {str(e)}")
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
                    proxy=proxy,
                    verify_ssl=False
                ) as response:
                    return await response.json()
        except Exception as e:
            self.log(f"{Fore.RED}Check-in error: {str(e)}")
            return None
        
    async def process_account(self, account: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(account) if use_proxy else None
        masked_account = self.mask_account(account)

        for attempt in range(3):
            token = await self.user_login(account, proxy)
            if not token:
                # Rotate proxy on failure
                if use_proxy:
                    proxy = self.rotate_proxy_for_account(account)
                continue
                
            try:
                # Add random delay between actions
                await asyncio.sleep(random.uniform(1, 3))
                
                # Confirm referral
                confirm_res = await self.user_confirm(token, proxy)
                if confirm_res and confirm_res.get("success"):
                    self.log(f"{Fore.GREEN}{masked_account} | Referral confirmed")
                
                # Check balance
                balance_res = await self.user_balance(token, proxy)
                if balance_res and "data" in balance_res:
                    points = next((item["balance"] for item in balance_res["data"] if item["coin_id"] == "3"), 0)
                    self.log(f"{Fore.CYAN}{masked_account} | Balance: {points} POINTS")
                
                # Perform check-in
                checkin_res = await self.perform_checkin(token, proxy)
                if checkin_res and checkin_res.get("success"):
                    self.log(f"{Fore.GREEN}{masked_account} | Check-in successful")
                else:
                    msg = checkin_res.get("message", "Unknown error") if checkin_res else "No response"
                    self.log(f"{Fore.YELLOW}{masked_account} | Check-in failed: {msg}")
                
                # Success - break retry loop
                break
                
            except Exception as e:
                self.log(f"{Fore.RED}{masked_account} | Processing error: {str(e)}")
                if use_proxy:
                    proxy = self.rotate_proxy_for_account(account)
                
            finally:
                await asyncio.sleep(random.uniform(2, 5))

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in [1, 2]

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(f"{Fore.GREEN}Processing {len(accounts)} accounts")

                if use_proxy:
                    if not await self.load_proxies(use_proxy_choice):
                        use_proxy = False
                        self.log(f"{Fore.YELLOW}Continuing without proxies")

                # Process all accounts in sequence
                for account in accounts:
                    if not account:
                        continue
                    await self.process_account(account, use_proxy)
                
                # Wait 12 hours before next cycle
                wait_time = 12 * 60 * 60
                self.log(f"{Fore.CYAN}Cycle completed. Next run in {self.format_seconds(wait_time)}")
                while wait_time > 0:
                    formatted = self.format_seconds(wait_time)
                    print(f"{Fore.CYAN}Next run in: {formatted}", end='\r')
                    await asyncio.sleep(1)
                    wait_time -= 1

        except KeyboardInterrupt:
            self.log(f"{Fore.RED}Process interrupted")
        except Exception as e:
            self.log(f"{Fore.RED}Fatal error: {str(e)}")

if __name__ == "__main__":
    bot = ZerosWallet()
    asyncio.run(bot.main())
