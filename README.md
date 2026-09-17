🐼 MX

猫熊加速器自动签到

基于 Python + Playwright + GitHub Actions 实现的猫熊加速器自动签到工具。

无需服务器，配置好 GitHub Secrets 后即可通过 GitHub Actions 自动运行，并支持使用 Server 酱推送签到结果。

✨ 功能

* 🤖 自动登录猫熊加速器
* 🧮 自动完成 PoW 安全验证
* ✅ 自动执行每日签到
* 📱 支持 Server 酱消息推送
* ☁️ 使用 GitHub Actions 自动运行
* 🔐 使用 GitHub Secrets 保存账号信息
* 🚫 无需本地电脑或服务器长期运行

⸻

🚀 使用方法

1. Fork 本项目

点击右上角 Fork，将项目复制到你自己的 GitHub 账号下。

⸻

2. 配置 GitHub Secrets

进入你 Fork 后的仓库：

Settings → Secrets and variables → Actions

点击：

New repository secret

添加以下三个变量：

Name	Value	必填
USER_EMAIL	猫熊加速器登录邮箱	✅
USER_PASSWORD	猫熊加速器登录密码	✅
SERVERCHAN_KEY	Server 酱 Key	❌

例如：

USER_EMAIL
your@email.com
USER_PASSWORD
your_password
SERVERCHAN_KEY
sctpXXXXXX

其中：

* USER_EMAIL：你的猫熊加速器账号
* USER_PASSWORD：你的猫熊加速器密码
* SERVERCHAN_KEY：用于接收签到结果通知，不需要通知可以不填写

⚠️ 不要把账号密码直接写进代码或提交到 GitHub。

请使用 GitHub Secrets 保存敏感信息。

⸻

⏰ 自动运行

项目使用 GitHub Actions 自动执行签到。

Workflow 会按照项目中的定时任务自动运行，无需手动操作。

运行流程：

GitHub Actions
      │
      ▼
启动 Chromium
      │
      ▼
打开猫熊登录页面
      │
      ▼
填写账号密码
      │
      ▼
完成 PoW 安全验证
      │
      ▼
登录用户中心
      │
      ▼
执行每日签到
      │
      ▼
获取签到结果
      │
      ▼
Server 酱推送通知

⸻

▶️ 手动运行

除了自动定时运行外，也可以在 GitHub Actions 中手动执行。

进入：

Actions → 对应的 Workflow → Run workflow

点击 Run workflow 即可立即执行一次签到。

如果没有看到 Run workflow，请确认仓库中的 Workflow 已经启用。

⸻

📋 查看运行结果

进入：

Actions → 对应的 Workflow

即可查看每次运行记录。

点击具体的一次运行，可以查看详细日志。

正常情况下会看到类似：

[*] 正在打开登录页面...
[*] 寻找并触发本地 PoW 计算...
[*] 已找到验证按钮，正在点击触发...
[*] 正在等待算力结果...
[+] PoW 计算完成!
[*] 点击登录...
[+] 登录成功，已跳转至用户中心！
[*] 检查并执行签到...
[+] 签到接口响应: 今日签到成功

⸻

📱 Server 酱通知

配置 SERVERCHAN_KEY 后，签到完成会自动推送结果。

例如：

猫熊加速器签到结果
签到返回：今日签到成功

如果登录失败或程序出现异常，也会推送相应的错误信息。

⸻

🔐 安全说明

本项目通过 GitHub Secrets 获取账号信息：

USER_EMAIL
USER_PASSWORD
SERVERCHAN_KEY

这些信息不会直接写入代码。

请不要在：

* README
* Python 源代码
* GitHub Actions YAML
* Issue
* Pull Request

中公开自己的账号密码或 Server 酱 Key。

⸻

⚠️ 注意事项

本项目依赖猫熊加速器当前网页结构及接口。

如果网站修改了：

* 登录页面
* 登录流程
* PoW 验证机制
* 用户中心
* 签到接口
* 页面元素

可能会导致自动签到失效。

如果遇到问题，可以前往 Actions 查看运行日志，确认具体失败原因。

⸻

⭐ 项目地址

https://github.com/wangzi9118/MX

如果项目对你有帮助，欢迎点一个 ⭐ Star。

⸻

📄 License

本项目的开源许可协议以仓库中的 LICENSE 文件为准。
以上内容由ChatGPT生成
