import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import pandas as pd

from aar_operator import Operator

# 目标URL, 指向“干员一览”的页面
operator_list_url = 'https://prts.wiki/w/%E5%B9%B2%E5%91%98%E4%B8%80%E8%A7%88'

# 指定 chromedriver 的路径
driver_path = '.\\chromedriver.exe'

# 使用 Service 对象指定 ChromeDriver 的路径
service = Service(executable_path=driver_path)

# 初始化 WebDriver
driver = webdriver.Chrome(service=service)


def get_all_operators_url():
    """
    获取所有干员的详细信息页面 URL

    Returns:
        包含所有干员详细信息页面 URL 的列表
    """
    # 发送GET请求获取页面内容
    response = requests.get(operator_list_url)
    response.encoding = 'utf-8'  # 确保正确处理页面编码

    # 使用BeautifulSoup解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 定位包含干员信息的<div>元素, 这里假设它们都在id为"filter-data"的<div>内
    operator_divs = soup.select('div#filter-data > div')

    operators = []

    # 遍历这些<div>元素, 提取干员名字, 并构造详细信息页面URL
    for div in operator_divs:
        operator_name = div['data-zh']  # 提取干员的中文名
        # 构造详细信息页面的URL
        operator_url = f'https://prts.wiki/w/{operator_name}'
        operators.append(
            Operator(operator_name, operator_url))  # 记录 URL

    return operators


def safe_get_element_text(soup, selector):
    """
    安全地获取页面元素的文本内容，如果找不到元素则返回 None。

    Args:
        soup: BeautifulSoup 对象
        selector: CSS 选择器

    Returns:
        (str): 元素的文本内容，如果元素不存在则返回 None
    """
    try:
        return soup.select_one(selector).text.strip()
    except AttributeError:  # 如果 select_one 找不到元素，将返回 None
        return None


def get_operator_info(operator):
    """
    获取干员的详细信息

    Args:
        operator: Operator 实例
    """
    try:
        driver.get(operator.url)
    except TimeoutException:
        print("请求超时，无法获取干员页面。")
        return

    try:
        driver.get(operator.url)

        # 等待“星级”图片元素加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".charstar img"))
        )

        # 等待“职业”图片元素加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".charclass-img img"))
        )

    except TimeoutException:
        print("请求超时，无法获取干员页面。")
        return

    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # 提取星级信息
    star_img_src = soup.select_one('.charstar img')[
        'src'] if soup.select_one('.charstar img') else None
    if star_img_src:
        parts = star_img_src.split('/')[-1].split('_')
        operator.star = int(parts[1].split('.')[0]) if len(
            parts) >= 2 and parts[1].split('.')[0].isdigit() else None
    else:
        print("未找到星级信息。")

    # 提取职业信息
    class_img = soup.select_one('.charclass-img img')
    if class_img and 'src' in class_img.attrs:
        class_src = class_img['src']
        parts = class_src.split('/')
        if len(parts) > 0:
            file_name = parts[-1]  # 获取 URL 的最后一部分，即文件名
            name_parts = file_name.split('_')
            if len(name_parts) > 1:
                operator.class_name = name_parts[1].split('.')[0]  # 从文件名解析职业名称
            else:
                print("职业信息格式不符合预期。")
        else:
            print("未找到职业信息。")
    else:
        print("未找到职业信息。")

    # 提取位置信息
    position_element = soup.select_one('.char-pos-text a')
    if position_element:
        operator.pos = position_element.text.strip()
    else:
        print("未找到位置信息。")

    # 提取标签信息
    operator.tag = [tag.text for tag in soup.select(
        '.char-tag-flex .char-tag a')]

    # 提取获得方式信息
    obtain_method_td = soup.find('th', string=re.compile('获得方式')).find_next_sibling(
        'td') if soup.find('th', string=re.compile('获得方式')) else None
    operator.public_recruit = '公开招募' in obtain_method_td.text if obtain_method_td else False

    # 提取干员报道信息
    report_title_div = soup.find('div', class_='table-cell', text='干员报到')
    if report_title_div:
        report_content_div = report_title_div.find_next_sibling('div')
        if report_content_div:
            report_text = report_content_div.p.text.strip() if report_content_div.p else None
            if report_text:
                operator.report = report_text
            else:
                print("未找到干员报道内容。")
        else:
            print("未找到干员报道内容的容器。")
    else:
        print("未找到干员报道标题。")


def save_csv(operators, filename="operators.csv"):
    """
    将 Operator 实例转换为字典列表, 并保存到CSV文件

    Args:
        operators (list): 包含 Operator 实例的列表
    """
    # 将 Operator 实例转换为字典列表
    operators_data = [
        {"name": op.name, "url": op.url, "star": op.star, "class_name": op.class_name, "pos": op.pos, "tag": ','.join(
            op.tag), "public_recruit": op.public_recruit, "report": op.report}
        for op in operators
    ]

    # 转换为 pandas DataFrame
    df = pd.DataFrame(operators_data)

    # 保存到 CSV 文件
    df.to_csv(filename, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    operators = get_all_operators_url()
    print("干员数量:", len(operators))

    for operator in operators:
        print("-" * 40)
        print("干员名称: ", operator.name)

        # 多次循环
        count = 0
        while operator.star == 0 and count < 10:
            print("==第 {} 次尝试==".format(count + 1))
            get_operator_info(operator)
            count += 1
        print("星级: ", operator.star)
        print("职业: ", operator.class_name)
        print("位置: ", operator.pos)
        print("标签: ", operator.tag)
        print("公开招募: ", operator.public_recruit)
        print("干员报道: ", operator.report)

    save_csv(operators)

    driver.quit()
