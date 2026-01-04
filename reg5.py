import random
import time
import re
import string
import logging
import os
from concurrent.futures import ThreadPoolExecutor

# --- CÀI ĐẶT THƯ VIỆN TỰ ĐỘNG ---
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Đang cài đặt thư viện thiếu...")
    os.system("pip install selenium webdriver-manager")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH LOGGING ---
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

def get_chrome_options():
    """Cấu hình Chrome tối ưu cho Cloud Shell và Bypass cơ bản"""
    opts = Options()
    # Chạy ẩn (Headless) bắt buộc trên Cloud Shell không có màn hình
    opts.add_argument("--headless=new") 
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--window-size=375,812") # Kích thước màn hình iPhone
    opts.add_argument("--lang=vi-VN") 
    
    # User Agent Mobile ngẫu nhiên
    ua_list = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36"
    ]
    opts.add_argument(f"user-agent={random.choice(ua_list)}")
    
    # Bypass Automation check
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    
    return opts

def human_type(element, text):
    """Giả lập gõ phím từ từ"""
    element.click()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

def get_random_info():
    ho_list = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo", "Dang", "Bui", "Do"]
    ten_list = ["Nam", "Hung", "Tuan", "Dung", "Minh", "Hieu", "Phat", "Thanh", "Dat", "Khoa", "Long", "Duc"]
    
    ho = random.choice(ho_list)
    ten = random.choice(ten_list)
    
    # Tạo email outlook/hotmail ảo
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"{ten.lower()}{ho.lower()}.{random_str}@outlook.com"
    password = f"{ten.capitalize()}@{random.randint(10000, 99999)}"
    
    return ho, ten, email, password

def click_element_robust(driver, xpath_list):
    """Click mạnh mẽ: Thử nhiều xpath, dùng cả JS click"""
    # Cách 1: Thử click thường
    for xpath in xpath_list:
        try:
            elm = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elm.click()
            return True
        except:
            continue
    
    # Cách 2: Thử JS Click (nếu bị che)
    for xpath in xpath_list:
        try:
            elm = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", elm)
            return True
        except:
            pass
    return False

def run_acc(index):
    driver = None
    try:
        # Setup Driver
        try:
            driver_path = ChromeDriverManager().install()
        except:
            # Fallback cho linux server nếu không cài được tự động
            driver_path = "/usr/bin/chromedriver"
            
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=get_chrome_options())
        
        # Bypass JS Detect nâng cao
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
            """
        })
        
        ho, ten, email, password = get_random_info()
        print(f"[{index}] >>> Init: {email} | Pass: {password}")
        
        # 1. Vào trang chủ mobile (Ổn định hơn vào thẳng link reg)
        driver.get("https://m.facebook.com/")
        time.sleep(random.uniform(3, 6))
        
        # --- BƯỚC QUAN TRỌNG: TÌM NÚT TẠO TÀI KHOẢN ---
        # Trên Cloudshell, FB thường hiện trang login, phải bấm "Tạo tài khoản mới"
        print(f"[{index}] Đang tìm nút tạo tài khoản...")
        
        create_acc_selectors = [
            "//a[contains(@href, 'reg')]", 
            "//button[contains(text(), 'Tạo tài khoản')]",
            "//a[contains(text(), 'Tạo tài khoản')]",
            "//div[contains(text(), 'Tạo tài khoản')]",
            "//a[contains(text(), 'Create new account')]"
        ]
        
        click_element_robust(driver, create_acc_selectors)
        time.sleep(3) # Chờ load form

        # 2. Điền Tên (Firstname/Lastname)
        try:
            # Chờ ô nhập tên xuất hiện
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'firstname')))
            
            human_type(driver.find_element(By.NAME, 'firstname'), ten)
            human_type(driver.find_element(By.NAME, 'lastname'), ho)
            
            # Click Next
            click_element_robust(driver, [
                "//button[@value='Next']", 
                "//button[contains(text(), 'Tiếp')]", 
                "//button[contains(text(), 'Next')]"
            ])
            time.sleep(2)
        except Exception as e:
            # Nếu lỗi, chụp ảnh màn hình để debug
            driver.save_screenshot(f"error_name_{index}.png")
            print(f"[{index}] Lỗi Step Tên (Đã lưu ảnh error_name_{index}.png). Có thể do IP bị chặn form.")
            return

        # 3. Ngày sinh
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "year")))
            # Chọn đại năm sinh
            Select(driver.find_element(By.ID, "year")).select_by_value(str(random.randint(1995, 2002)))
            
            click_element_robust(driver, ["//button[@value='Next']", "//button[contains(text(), 'Tiếp')]"])
            time.sleep(2)
        except:
            # Form ngày sinh đôi khi tự động qua hoặc không load được, thử next tiếp
            click_element_robust(driver, ["//button[@value='Next']", "//button[contains(text(), 'Tiếp')]"])

        # 4. Email / SĐT
        try:
            # Ưu tiên chọn đăng ký bằng Email
            click_element_robust(driver, ["//a[contains(text(), 'hỉ email')]", "//div[contains(text(), 'email')]"])
            time.sleep(1)
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'reg_email__')))
            email_field = driver.find_element(By.NAME, 'reg_email__')
            email_field.clear()
            human_type(email_field, email)
            
            click_element_robust(driver, ["//button[@value='Next']", "//button[contains(text(), 'Tiếp')]"])
            time.sleep(2)
        except Exception as e:
            print(f"[{index}] Lỗi Step Email: {e}")
            return

        # 5. Giới tính
        try:
            # Chọn Nam (value=2 hoặc tìm theo text)
            click_element_robust(driver, [
                "//input[@value='2']", 
                "//label[contains(text(), 'Nam')]", 
                "//span[contains(text(), 'Nam')]"
            ])
            
            click_element_robust(driver, ["//button[@value='Next']", "//button[contains(text(), 'Tiếp')]"])
            time.sleep(2)
        except: 
            pass

        # 6. Mật khẩu & Submit
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'reg_passwd__')))
            pass_input = driver.find_element(By.NAME, 'reg_passwd__')
            human_type(pass_input, password)
            
            time.sleep(1)
            
            print(f"[{index}] Đang bấm Đăng Ký...")
            # Các loại nút Đăng ký
            signup_selectors = [
                "//button[@name='submit']",
                "//button[contains(text(), 'Đăng ký')]",
                "//button[contains(text(), 'Sign Up')]",
                "//div[@role='button' and contains(text(), 'Đăng ký')]"
            ]
            
            if not click_element_robust(driver, signup_selectors):
                pass_input.submit() # Fallback: Enter
                
            time.sleep(10) # Chờ FB xử lý lâu hơn chút
            
        except Exception as e:
            print(f"[{index}] Lỗi Step Password: {e}")
            return

        # 7. Check Thành Công (Cookie & UID)
        try:
            # Kiểm tra URL hoặc Cookie
            current_url = driver.current_url
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            is_success = False
            uid = "Unknown"

            # Check 1: Có c_user trong cookie
            if "c_user" in cookie_str:
                uid = re.search(r'c_user=(\d+)', cookie_str).group(1)
                is_success = True
            
            # Check 2: Chuyển hướng sang trang save-device hoặc confirm
            elif "save-device" in current_url or "confirmemail" in current_url:
                is_success = True
            
            if is_success:
                print(f"[{index}] ==> SUCCESS! UID: {uid}")
                with open("ACC_FB_LIVE.txt", "a") as f:
                    f.write(f"{email}|{password}|{uid}|{cookie_str}\n")
            else:
                # Nếu thất bại, chụp ảnh xem nó báo lỗi gì (Checkpoint hay sai info)
                driver.save_screenshot(f"fail_{index}.png")
                print(f"[{index}] ==> Thất bại/Checkpoint. (Đã lưu ảnh fail_{index}.png)")
                
        except Exception as e:
            print(f"[{index}] Lỗi Check Live: {e}")

    except Exception as e:
        print(f"[{index}] Crash Tổng: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    print("--- TOOL AUTO REG FB FIX (CLOUD SHELL VERSION) ---")
    try:
        num_str = input("Nhập số luồng (Enter mặc định là 1): ")
        num = int(num_str) if num_str.strip() else 1
        
        loops_str = input("Nhập số acc mỗi luồng (Enter mặc định là 1): ")
        loops = int(loops_str) if loops_str.strip() else 1
        
        with ThreadPoolExecutor(max_workers=num) as executor:
            for i in range(num):
                for _ in range(loops):
                    executor.submit(run_acc, f"T{i}")
                    time.sleep(5) # Delay giữa các luồng để tránh spam request cùng lúc
    except Exception as e:
        print(f"Lỗi nhập liệu: {e}")

if __name__ == "__main__":
    main()
