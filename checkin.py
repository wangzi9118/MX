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
    """Server 酱推送（过滤 HTML 标签，防止触发 400 错误）"""
    if not SERVERCHAN_KEY:
        return
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    clean_desp = re.sub(r"<[^>]+>", "", str(desp))[:500]
    data = urllib.parse.urlencode({
        "title": str(title)[:30],
        "desp": clean_desp
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        login_resp_info = {}

        def on_response(response):
            if "/auth/login" in response.url:
                try:
                    text = response.text()
                    login_resp_info["status"] = response.status
                    login_resp_info["body"] = text
                    print(f"[*] 登录接口返回: 状态码 {response.status} -> {text}")
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            print("[*] 正在打开登录页面...")
            page.goto("https://mxwljsq.com/auth/login", wait_until="networkidle", timeout=30000)

            # 填写账密
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

            # 等待验证状态写入
            print("[*] 正在等待 3 秒以确保验证状态就绪...")
            time.sleep(3)

            print("[*] 点击登录...")
            login_btn = page.query_selector("button[type='submit'], button:has-text('登录'), #login-btn, #login")
            if login_btn:
                login_btn.click()
            else:
                page.keyboard.press("Enter")

            # 等待登录跳转
            time.sleep(5)

            if "/user" in page.url or "用户中心" in page.content():
                print("[+] 登录成功，已跳转至用户中心！")
            else:
                page_error = page.evaluate("""() => {
                    const el = document.querySelector('.swal2-html-container, .swal2-title, .toast, .alert, .modal-body, #msg');
                    return el ? el.innerText.trim() : '';
                }""")
                detail = f"弹窗: {page_error or '无'} | 接口返回: {login_resp_info.get('body', '无响应')}"
                msg = f"[-] 登录未成功跳转: {detail}"
                print(msg)
                push_serverchan("猫熊加速器签到失败", f"登录未成功跳转。\n详情: {detail}")
                sys.exit(1)

            # 清除阻挡操作的公告弹窗
            print("[*] 正在关闭/清除公告弹窗...")
            time.sleep(2)
            page.evaluate("""() => {
                const modal = document.querySelector('#popup-ann-modal, .modal.show');
                if (modal) modal.remove();
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(b => b.remove());
                document.body.classList.remove('modal-open');
            }""")
            time.sleep(1)

            # 执行签到请求
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
                    return { ret: -1, msg: e.toString() };
                }
            }""")

            # 修复此处语法错误：补全 (0, 1) 判断范围
            if isinstance(checkin_res, dict) and checkin_res.get("ret") in (0, 1):
                msg = checkin_res.get("msg", "无返回说明")
                print(f"[+] 签到返回: {msg}")
                push_serverchan("猫熊加速器签到结果", f"签到结果: {msg}")
            else:
                checkin_btn = page.query_selector("button:has-text('签到'), a:has-text('签到'), #checkin")
                if checkin_btn:
                    checkin_btn.click(force=True)
                    time.sleep(3)
                    print("[+] 签到按钮已强制点击！")
                    push_serverchan("猫熊加速器签到", "已成功触发签到。")
                else:
                    print("[*] 未找到签到按钮，可能今日已签到。")
                    push_serverchan("猫熊加速器通知", "已成功登录，未找到签到按钮（可能今日已完成签到）。")

        except Exception as e:
            err_msg = f"[-] 运行异常: {str(e)}"
            print(err_msg)
            push_serverchan("猫熊签到异常", err_msg)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    run()
