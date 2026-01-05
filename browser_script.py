import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('browser.log'),
        logging.StreamHandler()
    ]
)

# 配置网站列表
WEBSITES = [
    'https://dahi.icu',
]

# 从环境变量获取持续时间（分钟），默认 5 分钟
DURATION_MINUTES = int(os.getenv('BROWSE_DURATION', '5'))

def setup_driver():
    """设置无头浏览器"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 使用系统安装的 ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_clickable_links(driver):
    """获取页面中可点击的链接"""
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        # 过滤有效链接
        valid_links = []
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and href.startswith('http') and link.is_displayed():
                    valid_links.append(link)
            except:
                continue
        return valid_links
    except Exception as e:
        logging.error(f"获取链接时出错: {str(e)}")
        return []

def click_random_link(driver):
    """随机点击页面中的链接"""
    try:
        links = get_clickable_links(driver)
        if not links:
            logging.warning("页面中没有找到可点击的链接")
            return False
        
        # 随机选择一个链接
        link = random.choice(links[:min(20, len(links))])  # 只从前20个链接中选择
        href = link.get_attribute("href")
        text = link.text[:50] if link.text else "无文本"
        
        logging.info(f"点击链接: {text} -> {href}")
        
        # 保存原窗口句柄
        original_window = driver.current_window_handle
        
        # 点击链接
        driver.execute_script("arguments[0].click();", link)
        time.sleep(2)
        
        # 如果打开了新窗口，切换到新窗口
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        return True
        
    except Exception as e:
        logging.error(f"点击链接时出错: {str(e)}")
        return False

def random_scroll(driver):
    """随机滚动页面"""
    scroll_times = random.randint(2, 5)
    for _ in range(scroll_times):
        scroll_height = random.randint(300, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_height});")
        time.sleep(random.uniform(0.5, 2))

def browse_with_clicks(driver, start_url, duration_seconds):
    """浏览网站并随机点击内页链接"""
    try:
        logging.info(f"开始浏览: {start_url}")
        driver.get(start_url)
        
        # 等待页面加载
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        start_time = time.time()
        click_count = 0
        visited_urls = set()
        visited_urls.add(driver.current_url)
        
        while (time.time() - start_time) < duration_seconds:
            # 随机滚动查看页面
            random_scroll(driver)
            
            # 随机停留
            stay_time = random.uniform(3, 8)
            logging.info(f"当前页面停留 {stay_time:.2f} 秒")
            time.sleep(stay_time)
            
            # 尝试点击随机链接
            if click_random_link(driver):
                click_count += 1
                current_url = driver.current_url
                
                # 避免重复访问相同URL
                if current_url not in visited_urls:
                    visited_urls.add(current_url)
                    logging.info(f"已访问 {len(visited_urls)} 个不同页面")
                
                # 等待新页面加载
                time.sleep(random.uniform(2, 4))
            else:
                # 如果无法点击链接，返回起始页面重新开始
                logging.info("返回起始页面重新开始")
                driver.get(start_url)
                time.sleep(2)
            
            elapsed = time.time() - start_time
            remaining = duration_seconds - elapsed
            logging.info(f"已运行 {elapsed:.0f} 秒，剩余 {remaining:.0f} 秒")
        
        logging.info(f"完成浏览，共点击 {click_count} 次，访问 {len(visited_urls)} 个不同页面")
        return click_count, len(visited_urls)
        
    except Exception as e:
        logging.error(f"浏览过程出错: {str(e)}")
        return 0, 0

def main():
    """主函数"""
    start_time = datetime.now()
    duration_seconds = DURATION_MINUTES * 60
    
    logging.info(f"开始浏览，总持续时间: {DURATION_MINUTES} 分钟")
    logging.info(f"网站列表: {WEBSITES}")
    
    driver = setup_driver()
    total_clicks = 0
    total_pages = 0
    
    try:
        # 随机选择一个起始网站
        start_url = random.choice(WEBSITES)
        logging.info(f"选择起始网站: {start_url}")
        
        # 开始浏览并点击链接
        clicks, pages = browse_with_clicks(driver, start_url, duration_seconds)
        total_clicks += clicks
        total_pages += pages
            
    except KeyboardInterrupt:
        logging.info("手动停止浏览")
    finally:
        # 关闭所有窗口
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            driver.close()
        driver.quit()
        
        total_time = (datetime.now() - start_time).total_seconds()
        logging.info(f"="*50)
        logging.info(f"浏览统计:")
        logging.info(f"  总运行时间: {total_time:.2f} 秒")
        logging.info(f"  总点击次数: {total_clicks}")
        logging.info(f"  访问页面数: {total_pages}")
        logging.info(f"="*50)

if __name__ == "__main__":
    main()
