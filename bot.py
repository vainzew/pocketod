import os
import sys
import json
import time
import requests
from colorama import *
from datetime import datetime
from urllib.parse import unquote, parse_qs

merah = Fore.LIGHTRED_EX
kuning = Fore.LIGHTYELLOW_EX
hijau = Fore.LIGHTGREEN_EX
hitam = Fore.LIGHTBLACK_EX
biru = Fore.LIGHTBLUE_EX
putih = Fore.LIGHTWHITE_EX
reset = Style.RESET_ALL


class PocketfiTod:
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "gm.pocketfi.org",
            "Origin": "https://pocketfi.app",
            "Referer": "https://pocketfi.app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            "sec-ch-ua": '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24", "Microsoft Edge WebView2";v="125"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        self.line = putih + "~" * 50
        self.marin_kitagawa = lambda data: {
            key: value[0] for key, value in parse_qs(data).items()
        }

    def next_claim_is(self, last_claim):
        next_claim = last_claim + 7200
        now = datetime.now().timestamp()
        tetod = round(next_claim - now)
        return tetod

    def http(self, url, headers, data=None):
        while True:
            try:
                if data is None:
                    res = requests.get(url, headers=headers)
                elif data == "":
                    res = requests.post(url, headers=headers)
                else:
                    res = requests.post(url, headers=headers, data=data)

                open("http.log", "a", encoding="utf-8").write(f"{res.text}\n")
                if "<html>" in res.text:
                    self.log(f"{merah}failed to fetch json response !")
                    time.sleep(2)
                    continue
                return res

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                self.log(f"{merah}connection error / connection timeout !")
                time.sleep(1)
                continue

    def countdown(self, t):
        for t in range(t, 0, -1):
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"{putih}waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def log(self, msg):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{hitam}[{now}] {reset}{msg}")

    def get_user_mining(self, tg_data):
        url = "https://gm.pocketfi.org/mining/getUserMining"
        url_claim = "https://gm.pocketfi.org/mining/claimMining"
        headers = self.headers.copy()
        headers["Telegramrawdata"] = tg_data
        res = self.http(url, headers)
        if len(res.text) <= 0:
            self.log(f"{merah}failed get resopnse, 0 length response !")
            return 60
        balance = res.json()["userMining"]["gotAmount"]
        last_claim = res.json()["userMining"]["dttmLastClaim"] / 1000
        self.log(f"{hijau}balance : {putih}{balance}")
        can_claim = self.next_claim_is(last_claim)
        if can_claim >= 0:
            self.log(f"{kuning}not time to claim !")
            return can_claim

        res = self.http(url_claim, headers, "")
        if len(res.text) <= 0:
            self.log(f"{merah}failed get response, 0 length response !")
            return 60
        new_balance = res.json()["userMining"]["gotAmount"]
        self.log(f"{hijau}balance after claim : {putih}{new_balance}")
        return 7200

    def daily_task(self, tg_data):
        task_url = "https://bot2.pocketfi.org/mining/taskExecuting"
        active_boost_url = "https://bot2.pocketfi.org/boost/activateDailyBoost"
        headers = self.headers.copy()
        headers["telegramRawData"] = tg_data
        res = self.http(task_url, headers)
        tasks = res.json().get("tasks")
        if tasks is None:
            self.log(f"{merah}tasks is none, try again later !")
            return None
        daily = tasks.get("daily")[0]
        done_amount = daily.get("doneAmount")
        current_day = daily.get("currentDay")
        reward_list = daily.get("rewardList")
        if done_amount < reward_list[current_day]:
            res = self.http(active_boost_url, headers, "")
            if res.status_code != 200:
                self.log(f"{merah}failed claim daily boost today !")
                return False
            self.log(f"{hijau}success {putih}claim daily boost today !")
            return True
        self.log(f"{kuning}already {putih}claim daily today !")
        return True

    def main(self):
        banner = f"""
    {hijau}Auto Claim {putih}Pocketfi Bot {hijau}Telegram Every 1 Hour
    
    {putih}By : {hijau}t.me/dhtsryan
    {putih}Github : {hijau}@vainzew
    
        """
        arg = sys.argv
        if "marinkitagawa" not in arg:
            os.system("cls" if os.name == "nt" else "clear")
        print(banner)
        datas = open("data.txt", "r").read().splitlines()
        if len(datas) <= 0:
            self.log(f"{merah}add data account in data.txt first !")
            sys.exit()
        self.log(f"{hijau}account detected : {putih}{len(datas)}")
        print(self.line)
        while True:
            list_countdown = []
            _start = int(time.time())
            for no, data in enumerate(datas):
                self.log(f"{hijau}account number : {putih}{no + 1}/{len(datas)}")
                parser = self.marin_kitagawa(data)
                user = json.loads(parser.get("user"))
                self.log(f"{hijau}login as {putih}{user.get('first_name')}")
                self.daily_task(data)
                res = self.get_user_mining(data)
                print(self.line)
                list_countdown.append(res)
                self.countdown(5)
            _end = int(time.time())
            _tot = _end - _start
            _min = min(list_countdown)

            if (_min - _tot) <= 0:
                continue

            self.countdown(_min - _tot)


if __name__ == "__main__":
    try:
        PocketfiTod().main()
    except KeyboardInterrupt:
        sys.exit()
