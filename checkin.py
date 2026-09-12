import json
import os
import sys
import time
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

EMAIL = os.getenv("USER_EMAIL")
PASSWORD = os.getenv("USER_PASSWORD")
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")

LOGIN_URL = "https://mxwljsq.com/auth/login"
CHECKIN_URL = "https://mxwljsq.com/user/checkin"


def send_serverchan(title: str, desp: str = ""):
    if not SERVERCHAN_KEY:
        print("[*] 未检测到 SERVERCHAN_KEY，跳过消息推送。")
        return

    if SERVERCHAN_KEY.startswith("SCT"):
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    else:
        url = f"https://sc.ftqq.com/{SERVERCHAN_KEY}.send"

    post_data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=post_data,
        headers={"User-Agent": "Mozilla/5.0 (compatible; CheckinBot/1.0)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[*] Server 酱推送结果: {res.get('data', res.get('errmsg', res))}")
    except Exception as e:
        print(f"[-] Server 酱推送失败: {e}")


def auto_checkin():
    if not EMAIL or not PASSWORD:
        err_msg = "缺少 USER_EMAIL 或 USER_PASSWORD 配置！"
        print(f"[-] {err_msg}")
        send_serverchan("签到失败：配置缺失", err_msg)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            print("[*] 正在打开登录页面...")
            page.goto(LOGIN_URL, timeout=30000)

            # 1. 填写输入框
            page.locator('input[type="text"], input[type="email"]').first.fill(EMAIL)
            page.locator('input[type="password"]').first.fill(PASSWORD)

            # 2. 点击安全验证按钮
            verify_btn = page.locator("text=点击开始安全验证")
            if verify_btn.is_visible():
                print("[*] 触发本地 PoW 计算...")
                verify_btn.click()
                print("[*] 正在等待算力结果...")
                try:
                    page.locator("text=计算中").wait_for(state="hidden", timeout=30000)
                    print("[+] PoW 计算完成！")
                except Exception:
                    time.sleep(6)

            time.sleep(1)

            # 3. 点击登录按钮
            print("[*] 点击登录...")
            login_btn = page.locator('button:has-text("登录"), input[value="登录"]').first
            login_btn.click()

            # 4. 确认登录跳转
            try:
                page.wait_for_url("**/user", timeout=25000)
                print("[+] 成功进入用户中心。")
            except Exception:
                err_text = "登录超时或未成功跳转，请确认账密是否正确或遇到风控。"
                print(f"[-] {err_text}")
                send_serverchan("签到失败：登录未成功", err_text)
                browser.close()
                sys.exit(1)

            # 5. 发起签到
            print("[*] 发起签到接口请求...")
            response = context.request.post(CHECKIN_URL)
            
            try:
                res_json = response.json()
                msg = res_json.get("msg", str(res_json))
                ret = res_json.get("ret")
                print(f"[+] 签到接口响应: {msg}")

                if ret == 1:
                    send_serverchan("机场签到成功 🎉", f"- **结果**: {msg}")
                else:
                    send_serverchan("机场签到提醒", f"- **结果**: {msg}")
            except Exception:
                checkin_btn = page.locator("text=签到, text=今日已签到").first
                if checkin_btn.is_visible():
                    checkin_btn.click()
                    send_serverchan("机场签到通知", "已点击页面签到按钮。")
                else:
                    send_serverchan("签到异常", f"接口状态码: {response.status}")

        except Exception as e:
            err = f"执行异常: {str(e)}"
            print(f"[!] {err}")
            send_serverchan("签到流程异常", err)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    auto_checkin()
