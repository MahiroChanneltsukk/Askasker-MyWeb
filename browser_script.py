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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    'https://home.greasyfork.org.cn',
]

# 从环境变量获取持续时间（分钟），默认 5 分钟
DURATION_MINUTES = int(os.getenv('BROWSE_DURATION', '5'))

# AdSense 点击概率（0-1 之间，0.3 表示 30% 的概率点击广告）
ADSENSE_CLICK_PROBABILITY = float(os.getenv('ADSENSE_CLICK_PROB', '0.3'))

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

def find_adsense_iframes(driver):
    """查找页面中的 AdSense iframe"""
    try:
        # 常见的 AdSense iframe 选择器
        iframe_selectors = [
            "iframe[id*='google_ads']",
            "iframe[id*='aswift']",
            "iframe[src*='googlesyndication']",
            "iframe[src*='doubleclick.net']",
            "iframe[name*='google_ads']",
            "ins[class*='adsbygoogle']"
        ]
        
        all_iframes = []
        for selector in iframe_selectors:
            try:
                iframes = driver.find_elements(By.CSS_SELECTOR, selector)
                all_iframes.extend(iframes)
            except:
                continue
        
        # 去重
        unique_iframes = list(set(all_iframes))
        
        # 过滤可见的 iframe
        visible_iframes = []
        for iframe in unique_iframes:
            try:
                if iframe.is_displayed() and iframe.size['height'] > 50 and iframe.size['width'] > 50:
                    visible_iframes.append(iframe)
            except:
                continue
        
        return visible_iframes
    except Exception as e:
        logging.error(f"查找 AdSense iframe 时出错: {str(e)}")
        return []

def click_adsense_ad(driver):
    """尝试点击 AdSense 广告"""
    try:
        # 保存当前窗口句柄
        main_window = driver.current_window_handle
        original_url = driver.current_url
        
        # 查找 AdSense iframes
        iframes = find_adsense_iframes(driver)
        
        if not iframes:
            logging.info("未找到 AdSense 广告")
            return False
        
        logging.info(f"找到 {len(iframes)} 个 AdSense iframe")
        
        # 随机选择一个 iframe
        iframe = random.choice(iframes)
        
        # 滚动到 iframe 位置
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", iframe)
        time.sleep(random.uniform(1, 2))
        
        # 切换到 iframe
        driver.switch_to.frame(iframe)
        logging.info("已切换到 AdSense iframe")
        
        # 尝试查找可点击元素
        clickable_elements = []
        try:
            # 查找链接
            links = driver.find_elements(By.TAG_NAME, "a")
            clickable_elements.extend([l for l in links if l.is_displayed()])
        except:
            pass
        
        try:
            # 查找其他可点击元素
            divs = driver.find_elements(By.TAG_NAME, "div")
            clickable_elements.extend([d for d in divs if d.is_displayed()])
        except:
            pass
        
        if clickable_elements:
            # 随机选择一个元素点击
            element = random.choice(clickable_elements[:5])
            
            # 模拟人类行为：移动到元素位置再点击
            driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(random.uniform(0.5, 1))
            
            # 点击
            driver.execute_script("arguments[0].click();", element)
            logging.info("✓ 已点击 AdSense 广告")
            
            # 等待可能的新窗口打开
            time.sleep(random.uniform(2, 4))
            
            # 如果打开了新窗口，关闭它
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                new_url = driver.current_url
                logging.info(f"广告页面: {new_url[:100]}")
                
                # 在广告页面停留一段时间（模拟真实用户）
                stay_time = random.uniform(3, 8)
                logging.info(f"在广告页面停留 {stay_time:.2f} 秒")
                time.sleep(stay_time)
                
                # 关闭广告窗口
                driver.close()
                logging.info("已关闭广告窗口")
            
            # 切回主窗口
            driver.switch_to.window(main_window)
            
            # 确保回到原页面
            if driver.current_url != original_url:
                driver.get(original_url)
                time.sleep(random.uniform(1, 2))
            
            logging.info("已返回原页面")
            return True
        else:
            logging.info("iframe 中未找到可点击元素")
            driver.switch_to.default_content()
            return False
            
    except Exception as e:
        logging.error(f"点击 AdSense 广告时出错: {str(e)}")
        try:
            # 确保返回默认内容
            driver.switch_to.default_content()
            # 尝试切回主窗口
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return False

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
        link = random.choice(links[:min(20, len(links))])
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
    """浏览网站并随机点击内页链接和 AdSense 广告"""
    try:
        logging.info(f"开始浏览: {start_url}")
        driver.get(start_url)
        
        # 等待页面加载
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        start_time = time.time()
        click_count = 0
        adsense_click_count = 0
        visited_urls = set()
        visited_urls.add(driver.current_url)
        
        while (time.time() - start_time) < duration_seconds:
            # 随机滚动查看页面
            random_scroll(driver)
            
            # 随机停留
            stay_time = random.uniform(3, 8)
            logging.info(f"当前页面停留 {stay_time:.2f} 秒")
            time.sleep(stay_time)
            
            # 尝试点击 AdSense 广告（按概率）
            if random.random() < ADSENSE_CLICK_PROBABILITY:
                logging.info("尝试点击 AdSense 广告...")
                if click_adsense_ad(driver):
                    adsense_click_count += 1
                    logging.info(f"✓ AdSense 点击成功 (总计: {adsense_click_count})")
                time.sleep(random.uniform(2, 4))
            
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
        
        logging.info(f"完成浏览，共点击 {click_count} 次链接，{adsense_click_count} 次广告，访问 {len(visited_urls)} 个不同页面")
        return click_count, adsense_click_count, len(visited_urls)
        
    except Exception as e:
        logging.error(f"浏览过程出错: {str(e)}")
        return 0, 0, 0

def main():
    """主函数"""
    start_time = datetime.now()
    duration_seconds = DURATION_MINUTES * 60
    
    logging.info(f"开始浏览，总持续时间: {DURATION_MINUTES} 分钟")
    logging.info(f"网站列表: {WEBSITES}")
    logging.info(f"AdSense 点击概率: {ADSENSE_CLICK_PROBABILITY * 100}%")
    
    driver = setup_driver()
    total_clicks = 0
    total_adsense_clicks = 0
    total_pages = 0
    
    try:
        # 随机选择一个起始网站
        start_url = random.choice(WEBSITES)
        logging.info(f"选择起始网站: {start_url}")
        
        # 开始浏览并点击链接
        clicks, ad_clicks, pages = browse_with_clicks(driver, start_url, duration_seconds)
        total_clicks += clicks
        total_adsense_clicks += ad_clicks
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
        logging.info(f"  链接点击次数: {total_clicks}")
        logging.info(f"  AdSense 点击次数: {total_adsense_clicks}")
        logging.info(f"  访问页面数: {total_pages}")
        logging.info(f"="*50)

if __name__ == "__main__":
    main()
