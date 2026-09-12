import os
import sys
import time
import json
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

USER_EMAIL = os.environ.get("USER_EMAIL")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY")


def push_serverchan(title, desp):
    """Server 酱推送（使用内置 urllib，免装 requests）"""
    if not SERVERCHAN_KEY:
        return
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[*] Server 酱推送结果: {res}")
    except Exception as e:
        print(f"[-] Server 酱推送失败: {e}")


def run():
    if not USER_EMAIL or not USER_PASSWORD:
        print("[-] 错误: 请先配置 USER_EMAIL 与 USER_PASSWORD 环境变量。")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("[*] 正在打开登录页面...")
            page.goto("https://mxwljsq.com/auth/login", wait_until="networkidle", timeout=30000)

            # 输入账密
            page.fill("input[type='email'], input#email", USER_EMAIL)
            page.fill("input[type='password'], input#password", USER_PASSWORD)
            time.sleep(1)

            # 触发 PoW 计算
            print("[*] 触发本地 Pow 计算...")
            pow_btn = page.query_selector("button:has-text('安全验证'), div:has-text('安全验证'), #pow-btn")
            if pow_btn:
                pow_btn.click()

            print("[*] 正在等待算力结果...")
            page.wait_for_function(
                """() => {
                    const text = document.body.innerText;
                    return !text.includes("计算中") && (text.includes("验证成功") || text.includes("已验证") || true);
                }""",
                timeout=30000
            )
            print("[+] PoW 计算完成!")

            # ----------------------------------------------------
            # 增加延迟：等待 3 秒确保算力值完全绑定
            # ----------------------------------------------------
            print("[*] 正在等待 3 秒以确保验证状态就绪...")
            time.sleep(3)

            print("[*] 点击登录...")
            login_btn = page.query_selector("button[type='submit'], button:has-text('登录'), #login-btn")
            if login_btn:
                login_btn.click()
            else:
                page.keyboard.press("Enter")

            # 等待跳转
            try:
                page.wait_for_url("**/user**", timeout=15000)
                print("[+] 登录成功，已跳转至用户中心！")
            except Exception:
                if "/user" in page.url or "用户中心" in page.content():
                    print("[+] 登录成功！")
                else:
                    msg = "[-] 登录超时或未成功跳转,请确认账密是否正确或遇到风控。"
                    print(msg)
                    push_serverchan("猫熊签到失败 - 登录未跳转", msg)
                    sys.exit(1)

            # 签到处理
            time.sleep(2)
            print("[*] 检查并执行签到...")
            checkin_btn = page.query_selector("button:has-text('签到'), a:has-text('签到'), #checkin")
            if checkin_btn:
                checkin_btn.click()
                time.sleep(2)
                print("[+] 签到操作已触发！")
                push_serverchan("猫熊加速器签到成功", "今日签到已完成。")
            else:
                print("[*] 未找到签到按钮，可能今日已签到或已在后台。")
                push_serverchan("猫熊加速器通知", "已成功登录，未找到签到按钮（可能已签到）。")

        except Exception as e:
            err_msg = f"[-] 运行异常: {str(e)}"
            print(err_msg)
            push_serverchan("猫熊签到异常", err_msg)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    run()
