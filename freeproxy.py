from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
from supabase import create_client, Client
import time

# 直接在代码中设置 Supabase 客户端的 URL 和密钥
url: str = "https://crvpziqyfhhcqnxdkapn.supabase.co"  # 替换为你的 Supabase 项目 URL
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNydnB6aXF5ZmhoY3FueGRrYXBuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTc0ODE1OTgsImV4cCI6MjAzMzA1NzU5OH0.wvoTqQCOuoo8UVK-R7iyXXO99Nq0q0cSHzcu3wNNL7I"  # 替换为你的 Supabase API 密钥
supabase: Client = create_client(url, key)

def get_proxy_list():
    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无界面模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    chrome_options.add_argument('--ignore-ssl-errors')  # 忽略 SSL 错误
    chrome_options.add_argument('--no-sandbox')  # 禁用沙箱
    chrome_options.add_argument('--disable-dev-shm-usage')  # 禁用开发者工具
    chrome_options.add_argument('--enable-unsafe-swiftshader')  # 允许使用软件 WebGL
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.109 Safari/537.36")  # 设置 User-Agent
    
    # 创建 WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问网页
        print("正在访问网页...")
        driver.get('https://spys.one/en/free-proxy-list/')
        
        # 等页面加载完成
        print("等待页面加载...")
        driver.implicitly_wait(15)  # 增加等待时间
        
        # 获取代理列表
        proxy_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.spy1xx, tr.spy1x')
        proxy_list = []

        for row in proxy_rows:
            try:
                ip_port = row.find_element(By.CSS_SELECTOR, 'td:first-child').text
                proxy_type = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split(' ')[0]  # 只取前面的部分
                country = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                country = re.sub(r'\s*\(.*?\)', '', country).strip()  # 去掉括号内的内容
                country = country.replace('!', '').strip()  # 去掉感叹号
                
                # 映射 anonymity
                anonymity = row.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                if anonymity == "NOA":
                    anonymity = "Transparent"
                elif anonymity == "ANM":
                    anonymity = "Anonymous"
                elif anonymity == "HIA":
                    anonymity = "Elite"
                
                latency = row.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                
                # 修改为符合数据库格式的数据
                proxy_info = {
                    'address': ip_port,  # 对应 address
                    'country': country,  # 对应 country
                    'protocol': proxy_type,  # 对应 protocol
                    'anonymity_level': anonymity,  # 对应 anonymity_level
                    'ping': latency,  # 对应 ping
                }
                proxy_list.append(proxy_info)
                
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
                
        # 去掉第一条数据
        if proxy_list:
            proxy_list = proxy_list[1:]  # 去掉第一条数据
        
        # 查询并打印插入前数据库中的代理数量
        initial_count_response = supabase.table("free_proxy_list").select("address").execute()
        initial_count = len(initial_count_response.data)
        print(f"插入前数据库中的代理数量: {initial_count}")  # 打印插入前的数量

        # 插入代理数据到 free_proxy_list_test 表
        for proxy in proxy_list:
            # 检查地址是否已存在
            existing_response = supabase.table("free_proxy_list").select("address").eq("address", proxy['address']).execute()
            if not existing_response.data:  # 如果不存在，则插入
                response = (
                    supabase.table("free_proxy_list")
                    .insert({
                        "address": proxy['address'],
                        "country": proxy['country'],
                        "protocol": proxy['protocol'],
                        "anonymity_level": proxy['anonymity_level'],
                        "ping": proxy['ping'],
                    })
                    .execute()
                )  # 添加插入数据的代码

        # 查询并打印插入后数据库中的代理数量
        after_count_response = supabase.table("free_proxy_list").select("address").execute()
        after_count = len(after_count_response.data)
        print(f"插入后数据库中的代理数量: {after_count}")  # 打印插入后的数量

        return proxy_list
    
    finally:
        driver.quit()

def main():
    max_retries = 6
    while True:  # 无限循环，直到手动停止程序
        for attempt in range(max_retries):
            try:
                proxies = get_proxy_list()
                for proxy in proxies:
                    print(f"{proxy['address']} | {proxy['country']} | {proxy['protocol']} | {proxy['anonymity_level']} | {proxy['ping']}")
                break  # 成功后退出重试循环
            except Exception as e:
                print(f"获取代理列表失败: {e}")
                if attempt < max_retries - 1:
                    print("正在重试...")
                    time.sleep(10)  # 等待 10 秒后重试
                else:
                    print("达到最大重试次数，等待下一个小时...")
                    break  # 退出重试循环，等待下一个小时

        # 每小时执行一次
        print("等待一小时后再次执行...")
        time.sleep(3600)  # 等待一小时

if __name__ == '__main__':
    main()