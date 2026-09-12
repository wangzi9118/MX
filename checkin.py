import os
import sys
import time
import json
import re
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

USER_EMAIL = os.environ.get("USER_EMAIL")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY")


def push_serverchan(title, desp):
    """Server 酱推送（已限制长度和格式，防止 400 错误）"""
    if not SERVERCHAN_KEY:
        return
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    clean_desp = re.sub(r"<[^>]+>", "", str(desp))[:200]
    data = urllib.parse.urlencode({
        "title": str(title)[:30],
        "desp": clean_desp
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
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

            # 填写邮箱密码
            page.fill("input[type='email'], input#email", USER_EMAIL)
            page.fill("input[type='password'], input#password", USER_PASSWORD)
            time.sleep(1)

            # 触发 PoW 计算
            print("[*] 寻找并触发本地 PoW 计算...")
            pow_btn = (
                page.query_selector("text='点击开始安全验证'")
                or page.query_selector("text='安全验证'")
                or page.query_selector("button:has-text('安全验证')")
                or page.query_selector(".captcha-btn, #pow-btn, #captcha")
            )

            if pow_btn:
                print("[*] 已找到验证按钮，正在点击触发...")
                pow_btn.click()
                time.sleep(1)

                print("[*] 正在等待算力结果...")
                try:
                    page.wait_for_function(
                        """() => {
                            const text = document.body.innerText;
                            return !text.includes("计算中") && !text.includes("正在加载验证模块");
                        }""",
                        timeout=35000
                    )
                    print("[+] PoW 计算完成!")
                except Exception:
                    print("[-] 等待 PoW 计算状态超时，尝试继续执行...")
            else:
                print("[-] 提示: 未在页面找到 PoW 安全验证按钮，跳过点击。")

            # 等待 3 秒确保验证结果写入
            print("[*] 正在等待 3 秒以确保验证状态就绪...")
            time.sleep(3)

            print("[*] 点击登录...")
            login_btn = page.query_selector("button[type='submit'], button:has-text('登录'), #login-btn, #login")
            if login_btn:
                login_btn.click()
            else:
                page.keyboard.press("Enter")

            # 等待跳转至用户中心（最多等待 20 秒）
            print("[*] 正在等待登录跳转至用户中心...")
            try:
                page.wait_for_url("**/user**", timeout=20000)
                print("[+] 登录成功，已跳转至用户中心！")
            except Exception:
                if "/user" in page.url or "用户中心" in page.content():
                    print("[+] 登录成功！")
                else:
                    msg = "[-] 登录超时或未成功跳转至 /user"
                    print(msg)
                    push_serverchan("猫熊签到失败", "登录超时未成功跳转")
                    sys.exit(1)

            # ==========================================
            # 关键：清除公告弹窗遮罩，防止遮挡签到操作
            # ==========================================
            time.sleep(2)
            print("[*] 正在清除后台公告遮罩弹窗...")
            page.evaluate("""() => {
                const modal = document.querySelector('#popup-ann-modal, .modal.show');
                if (modal) modal.remove();
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(b => b.remove());
                document.body.classList.remove('modal-open');
            }""")
            time.sleep(1)

            # ==========================================
            # 执行签到（优先直接请求后台接口，无视任何遮挡）
            # ==========================================
            print("[*] 检查并执行签到...")
            checkin_res = page.evaluate("""async () => {
                try {
                    const res = await fetch('/user/checkin', {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });
                    return await res.json();
                } catch (e) {
                    return null;
                }
            }""")

            if isinstance(checkin_res, dict) and "msg" in checkin_res:
                msg = checkin_res.get("msg", "无返回信息")
                print(f"[+] 签到接口响应: {msg}")
                push_serverchan("猫熊加速器签到结果", f"签到返回: {msg}")
            else:
                # 备用方案：强制点击（force=True 绕过遮挡限制）
                checkin_btn = page.query_selector("button:has-text('签到'), a:has-text('签到'), #checkin")
                if checkin_btn:
                    checkin_btn.click(force=True)
                    time.sleep(3)
                    print("[+] 签到按钮已强制点击触发！")
                    push_serverchan("猫熊加速器签到", "已成功强制触发签到按钮。")
                else:
                    print("[*] 未找到签到按钮，可能今日已完成签到。")
                    push_serverchan("猫熊加速器通知", "已成功登录用户中心，未找到签到按钮或今日已签到。")

        except Exception as e:
            clean_err = str(e).split("\n")[0][:100]
            err_msg = f"[-] 运行异常: {clean_err}"
            print(err_msg)
            push_serverchan("猫熊签到异常", err_msg)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    run()
