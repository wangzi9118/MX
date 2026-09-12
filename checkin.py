import os
import sys
import time
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from playwright.sync_api import sync_playwright

USER_EMAIL = os.environ.get("USER_EMAIL")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY")


def push_serverchan(title, desp):
    """Server 酱推送（自动适配 Key 类型，支持 POST + GET 双通道）"""
    if not SERVERCHAN_KEY:
        print("[-] 未配置 SERVERCHAN_KEY，跳过推送")
        return

    key = SERVERCHAN_KEY.strip()

    # 1. 自动适配官方不同版本的接口域名
    m = re.match(r"^sctp(\d+)t", key)
    if m:
        # 新版 sctp 专属轻量推送域名
        base_url = f"https://{m.group(1)}.push.ft07.com/send/{key}.send"
    elif key.startswith("SCU"):
        # 老版 SCKEY 域名
        base_url = f"https://sc.ftqq.com/{key}.send"
    else:
        # 标准 Turbo 版域名
        base_url = f"https://sctapi.ftqq.com/{key}.send"

    clean_title = re.sub(r"[\r\n]+", " ", str(title))[:30]
    clean_desp = re.sub(r"<[^>]+>", "", str(desp))[:500]
    params = {"title": clean_title, "desp": clean_desp}

    # 2. 优先尝试标准 POST 请求
    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[*] Server 酱推送结果: {res}")
            return
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[*] POST 推送返回 HTTP {e.code} ({err_msg})，自动切换 GET 方式重试...")
    except Exception as e:
        print(f"[*] POST 推送异常: {e}，自动切换 GET 方式重试...")

    # 3. 备用 GET 通道（直接拼 URL，避免 Header 与格式兼容性问题）
    try:
        query_str = urllib.parse.urlencode(params)
        get_url = f"{base_url}?{query_str}"
        req = urllib.request.Request(get_url, headers={"User-Agent": "Mozilla/5.0"}, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[*] Server 酱推送结果: {res}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[-] Server 酱推送失败: HTTP {e.code} - {err_msg}")
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

            # 等待 3 秒确保算力值就绪
            print("[*] 正在等待 3 秒以确保验证状态就绪...")
            time.sleep(3)

            print("[*] 点击登录...")
            login_btn = page.query_selector("button[type='submit'], button:has-text('登录'), #login-btn, #login")
            if login_btn:
                login_btn.click()
            else:
                page.keyboard.press("Enter")

            # 等待跳转至用户中心
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

            # 清理阻挡公告弹窗
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

            # 执行签到接口请求
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
