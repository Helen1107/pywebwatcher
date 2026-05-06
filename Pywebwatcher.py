#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_monitor.py - 网页守望猫头鹰 🦉
一个带点脾气的网页监控工具，看得见变化，发得出通知。
"""

import hashlib
import json
import logging
import os
import sys
import smtplib
import time
import random
from email.message import EmailMessage
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

# ---------- 个性配置 ----------
CONFIG_FILE = "config.yaml"
STATE_FILE = "state.json"
# 彩色日志的 ANSI 代码
COLORS = {
    "INFO": "\033[92m",    # 绿
    "WARNING": "\033[93m", # 黄
    "ERROR": "\033[91m",   # 红
    "CHANGE": "\033[95m",  # 紫
    "RESET": "\033[0m"
}
BANNER = f"""
{COLORS['INFO']}🦉 Webbie the Watcher {COLORS['RESET']}
    /\\___/\\
   (  o o  )
   (  =^=  )
    (_____)  “盯住你的网页，有变化就喊你”
"""
EASTER_EGGS = [
    "💡 你知道吗？网页里的每一个元素都有它的故事。",
    "🎉 监控不是偷窥，是关心。",
    "☕ 用 GitHub Actions 运行我，连服务器都省了。",
    "🍎 特别适配 iPad 用户，你甚至可以用快捷指令。",
    "🔔 邮件通知别太频繁，小心被拉黑。"
]

def maybe_easter_egg():
    """随机彩蛋，10% 概率"""
    if random.random() < 0.1:
        print(random.choice(EASTER_EGGS) + "\n")

# 自定义日志格式，带颜色
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelname
        if level in COLORS:
            record.levelname = f"{COLORS[level]}{level}{COLORS['RESET']}"
        return super().format(record)

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------- 功能函数（和之前一样，但加一点俏皮） ----------
def load_config():
    if not Path(CONFIG_FILE).exists():
        logger.error(f"配置文件 {CONFIG_FILE} 不存在，你是忘记复制 config.example.yaml 了吗？")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_state():
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def fetch_html(url, timeout=10, retries=2):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            logger.info(f"✨ 成功抓住网页：{url}")
            return resp.text
        except requests.RequestException as e:
            logger.warning(f"抓取失败 ({attempt+1}/{retries+1})：{url} -> {e}")
            if attempt == retries:
                raise
            time.sleep(2)
    return None

def extract_content(html, selector, selector_type="css"):
    soup = BeautifulSoup(html, "lxml")
    if selector_type == "css":
        elements = soup.select(selector)
    elif selector_type == "xpath":
        from lxml import etree
        dom = etree.HTML(str(soup))
        elements = dom.xpath(selector)
        return " ".join(e.text_content().strip() for e in elements) if elements else ""
    else:
        raise ValueError(f"不支持的 selector_type: {selector_type}")
    if not elements:
        logger.warning(f"选择器 `{selector}` 没找到任何东西，检查一下？")
        return ""
    return " ".join(el.get_text(strip=True) for el in elements)

def compute_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ---------- 通知（邮件 / Bark） ----------
def send_email(subject, body, config):
    smtp_server = config.get("smtp_server")
    from_addr = config.get("from_addr")
    to_addr = config.get("to_addr")
    password = os.getenv(config.get("password_env", "EMAIL_PASSWORD"))
    if not all([smtp_server, from_addr, to_addr, password]):
        logger.error("邮件配置不全，发不了哦。检查一下环境变量 EMAIL_PASSWORD 有没有设置。")
        return
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(smtp_server, 587) as server:
            server.starttls()
            server.login(from_addr, password)
            server.send_message(msg)
        logger.info("📧 邮件通知已经飞出去啦！")
    except Exception as e:
        logger.error(f"邮件发送扑街：{e}")

def send_bark(title, body, config):
    device_key = os.getenv(config.get("device_key_env", "BARK_KEY"))
    if not device_key:
        logger.error("Bark Key 没找到，检查环境变量 BARK_KEY")
        return
    import urllib.parse
    safe_body = urllib.parse.quote(body[:100], safe="")
    url = f"https://api.day.app/{device_key}/{title}/{safe_body}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json().get("code") == 200:
            logger.info("📱 Bark 推送成功，你的 iOS 设备应该响了一下。")
        else:
            logger.warning(f"Bark 返回异常：{r.text}")
    except Exception as e:
        logger.error(f"Bark 发送辣眼睛：{e}")

def send_notification(name, url, preview, config):
    notify_cfg = config.get("notify", {})
    if "email" in notify_cfg:
        subject = f"[网页监控] {name} 内容变了！"
        body = f"监控项: {name}\nURL: {url}\n新内容预览（前200字）:\n{preview}..."
        send_email(subject, body, notify_cfg["email"])
    if "bark" in notify_cfg:
        title = f"📢 {name}"
        send_bark(title, preview, notify_cfg["bark"])
    if "email" not in notify_cfg and "bark" not in notify_cfg:
        logger.info(f"（没人要我通知，自己在日志里看着办）{name} 变化了")

# ---------- 主函数 ----------
def main():
    print(BANNER)
    maybe_easter_egg()
    logger.info("🦉 守望猫头鹰启动，开始巡视网页...")
    config = load_config()
    state = load_state()
    monitors = config.get("monitors", [])
    if not monitors:
        logger.warning("一个监控任务都没有！快去编辑 config.yaml 添加点东西吧。")
        return
    new_state = {}
    changed_items = []

    for mon in monitors:
        name = mon["name"]
        url = mon["url"]
        selector = mon["selector"]
        selector_type = mon.get("selector_type", "css")
        logger.info(f"🔍 检查：{name} ({url})")
        try:
            html = fetch_html(url)
            if html is None:
                continue
            content = extract_content(html, selector, selector_type)
            current_hash = compute_hash(content)
            old_hash = state.get(name, "")
            new_state[name] = current_hash

            if old_hash != current_hash:
                if old_hash == "":
                    logger.info(f"📝 首次记录 {name}，已保存指纹。")
                else:
                    logger.info(f"{COLORS['CHANGE']}⚠️ 发现变化！{name}{COLORS['RESET']}")
                    changed_items.append({
                        "name": name,
                        "url": url,
                        "preview": content[:200]
                    })
            else:
                logger.info(f"✅ {name} 风平浪静，没有变化。")
        except Exception as e:
            logger.exception(f"处理 {name} 时翻车了：{e}")

    save_state(new_state)

    for item in changed_items:
        send_notification(item["name"], item["url"], item["preview"], config)

    if not changed_items:
        logger.info("🛌 一切正常，猫头鹰去睡觉了，下次见。")
    else:
        logger.info("🎉 变化已通知，猫头鹰任务完成！")

if __name__ == "__main__":
    main()
