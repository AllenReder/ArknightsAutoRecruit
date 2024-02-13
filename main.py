from adb_tools import *
from aar_operator import Operator
from aar_recruit_info import RecruitInfo
import pandas as pd
from PIL import Image
from cnocr import CnOcr
import numpy as np
import itertools
import time
import re
import Levenshtein

window_size = (1920, 1080)  # 窗口大小

# 点击位置
click_pos = {
    '新建公招': (720, 565),
    '调整小时': (680, 450),
    'tag1': (660, 575),
    'tag2': (910, 575),
    'tag3': (1160, 575),
    'tag4': (660, 685),
    'tag5': (910, 685),
    '开始招募': (1470, 875),
    '立即招募': (720, 565),
    '确认立即招募': (1440, 760),
    '聘用候选人': (720, 565),
    '跳过': (1835, 65),
    '点击屏幕': (960, 540),
}

# tag 识别区域
# 每个 tag 按钮大小: (1920x1080 下)
# 宽 215px 高 70px
tag_ocr_area = [(562, 540, 562 + 215, 540 + 70),
                (812, 540, 812 + 215, 540 + 70),
                (1062, 540, 1062 + 215, 540 + 70),
                (562, 648, 562 + 215, 648 + 70),
                (812, 648, 812 + 215, 648 + 70)]

# 可能的标签 (tag)
possible_tag = ["高级资深干员", "资深干员", "新手", "近卫干员", "狙击干员", "重装干员", "医疗干员", "辅助干员", "术师干员", "特种干员", "先锋干员", "近战位", "远程位",
                "支援机械", "控场", "爆发", "治疗", "支援", "费用回复", "输出", "生存", "群攻", "防护", "减速", "削弱", "快速复活", "位移", "召唤"]


# 创建 cnocr 识别器
ocr = CnOcr()

# 干员信息
operators = []


def get_operators():
    """
    从 CSV 文件中读取可以通过公开招募获得的干员信息

    Returns:
        (list): 包含 Operator 实例的列表
    """
    # 读取 CSV 文件
    df = pd.read_csv("operators.csv")

    # 初始化Operator实例列表
    operators = []

    # 遍历DataFrame的每一行，为每一行创建一个Operator实例
    for index, row in df.iterrows():
        op = Operator(
            name=row['name'],
            url=row['url'],
            star=row['star'],
            class_name=row['class_name'],  # 补上 '干员' 二字
            pos=row['pos'],
            tag=row['tag'].split(','),
            public_recruit=row['public_recruit'] in [
                True, 'true', '1', 'yes'],  # 将值转换为布尔值
            report=row['report']
        )
        op.tag.append(op.class_name + "干员")
        op.tag.append(op.pos)
        operators.append(op)

    # 去除 public_recruit 为 False 的干员
    operators = [op for op in operators if op.public_recruit]
    # 去除 star 为 1/2/6 的干员
    operators = [op for op in operators if op.star not in [1, 2, 6]]

    return operators


def extract_chinese(text):
    """
    从文本中提取所有中文字符。

    Args: 
        text: 输入的字符串。
    Returns: 
        只包含中文字符的字符串。
    """

    # 使用正则表达式匹配中文字符
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    chinese_only = ''.join(pattern.findall(text))
    return chinese_only


def crop_img(img_path, area):
    """
    截取图片中部分区域, 并返回 RGB 格式的 NumPy 数组

    Args:
        img_path: 图片的路径
        area: 裁剪区域，格式为 (left, top, right, bottom)

    Returns:
        (np.array): RGB 格式的 NumPy 数组
    """

    # 读取图片
    img = Image.open(img_path)

    # 截取指定区域
    cropped_img = img.crop(area)

    # 将 Pillow 的 Image 对象转换为适合 OCR 处理的 RGB 格式的 NumPy 数组
    cropped_img_np = np.array(cropped_img.convert('RGB'))

    return cropped_img_np


def get_optional_tag(id: int):
    """
    获取所有公招标签 (tag) 

    Args:
        id: 自动公招编号

    Returns:
        (list): 所有标签的列表
    """

    while True:  # 循环直到识别到正确的标签
        screenshot_path = adb_screenshot(str(id) + '.png')  # 截图

        tag = []
        for area in tag_ocr_area:
            img = crop_img(screenshot_path, area)  # 截取单个 tag 的图片
            ocr_result = ocr.ocr_for_single_line(img)  # 识别单行文字
            chinese_only = extract_chinese(ocr_result['text'])
            tag.append(chinese_only)  # 添加识别结果

        # 如果识别到未知标签
        if not set(tag).issubset(set(possible_tag)):
            print("识别到未知标签:", set(tag) -
                  set(possible_tag), "正在尝试重新获取截图")
            continue
        break

    return tag


def choose_tag(optional_tag):
    """
    判断选择标签

    Args:
        optional_tag: 可选标签

    Returns:
        (list): 选择的标签
    """

    # 所有的可能组合
    selected_tag_list = []

    # 生成包含 1 至 3 个元素的所有可能组合
    for r in range(1, 4):
        for combination in itertools.combinations(optional_tag, r):
            selected_tag_list.append(list(combination))

    all_option = []

    # 每种选择的标签组合
    for selected_tag in selected_tag_list:
        possible_operator = []

        # 遍历所有的干员
        for op in operators:
            # 将 selected_tag 元组和 operator 的 tag 列表转换为集合
            selected_tag_set = set(selected_tag)
            op_tag_set = set(op.tag)

            # 检查 selected_tag_set 是否是 op_tag_set 的子集
            if selected_tag_set.issubset(op_tag_set):
                # 如果是，将该干员添加到可能的干员列表中
                possible_operator.append(op)

        # 如果没有可能的干员，跳过
        if not possible_operator:
            continue

        # 按照星级排序
        possible_operator.sort(key=lambda x: x.star)

        # 计算得分
        score = possible_operator[0].star * 100 - \
            len(selected_tag) + possible_operator[-1].star

        # 添加至可选组合
        all_option.append((selected_tag, possible_operator, score))

    # 按照分数排序
    all_option.sort(key=lambda x: x[2], reverse=True)

    # for option in all_option:
    #     print("标签组合:", option[0], " 分数:", option[2], "\n可能干员:", end='')
    #     for op in option[1]:
    #         print('(', op.star, ')', op.name,  sep='', end=' ')
    #     print()

    # 标签在可选标签中的位置
    return all_option[0]


def click(pos_name, delay=0.5):
    """
    点击特定位置, 并延时一段时间

    Args:
        pos_name: 点击位置的名称
        delay: 延时时间
    """

    adb_click(*click_pos[pos_name])
    time.sleep(delay)


def calc_text_cn_similarity(text1: str, text2: str):
    """
    计算两个字符串中文字符的编辑距离和相似度

    Args:
        text1 (str): 第一个字符串
        text2 (str): 第二个字符串

    Returns:
        (int, float): 编辑距离和相似度
    """
    # 去除非中文字符
    text1_cn = extract_chinese(text1)
    text2_cn = extract_chinese(text2)

    # 计算编辑距离
    edit_distance = Levenshtein.distance(text1_cn, text2_cn)

    # 计算相似度
    similarity = 1 - edit_distance / max(len(text1_cn), len(text2_cn))

    return edit_distance, similarity


def recongnize_operator(id):
    """
    识别干员

    Args:
        id: 自动公招编号

    Returns:
        (Operator): 干员信息
    """

    screenshot_path = adb_screenshot(str(id) + '_result.png')  # 截图
    img = crop_img(screenshot_path, (330, 950, 1590, 1080))  # 截取干员报道文字区域
    ocr_result = ocr.ocr(img)  # 识别报道文字
    ocr_report_text = ""  # 报道文字
    for result in ocr_result:
        ocr_report_text += result['text']  # 连接分段识别结果

    # 比对所有干员的报道文字与识别结果的相似度, 得到最高相似度的干员
    best_operator = None
    best_similarity = 0
    for op in operators:
        _, similarity = calc_text_cn_similarity(
            ocr_report_text, op.report)
        if similarity > best_similarity:
            best_similarity = similarity
            best_operator = op

    return best_operator


def save_recruit_info_with_pandas(recruit_info):
    """
    将招募信息保存到 CSV 文件中

    Args:
        recruit_info (RecruitInfo): 招募信息
    """
    # 根据当前日期生成文件名
    filename = 'history_' + time.strftime("%Y%m%d") + '.csv'

    # 检查文件是否存在，以决定是否需要添加标题行
    file_exists = os.path.isfile(filename)

    # 准备数据
    data = {
        '编号': [recruit_info.id],
        '时间': [recruit_info.start_time],
        '可选标签': [';'.join(recruit_info.optional_tag)],
        '选择的标签': [';'.join(recruit_info.selected_tag)],
        '可能的干员': [';'.join(op.name for op in recruit_info.possible_operator)],
        '得分': [recruit_info.score],
        '干员名称': [recruit_info.operator.name if recruit_info.operator else ''],
        '干员星级': [recruit_info.operator.star if recruit_info.operator else ''],
        '干员职业': [recruit_info.operator.class_name if recruit_info.operator else ''],
        '干员标签': [';'.join(recruit_info.operator.tag) if recruit_info.operator else '']
    }

    # 将数据转换为DataFrame
    df = pd.DataFrame(data)

    # 如果文件已存在，则追加数据，否则写入新文件（包括标题行）
    df.to_csv(filename, mode='a', index=False,
              header=not file_exists, encoding='utf-8-sig')


def auto_recruit(id=0):
    """
    自动公开招募一轮

    Args: 
        id: 自动公招编号
    """

    # 创建本次公招信息
    recruit_info = RecruitInfo(id)

    click('新建公招')
    click('调整小时')

    optional_tag = get_optional_tag(id)  # 获取可选标签
    recruit_info.optional_tag = optional_tag  # 存入信息

    # 如果 "高级资深干员" 出现在可选标签中, 由用户手动选择, 按下回车后继续
    if "高级资深干员" in optional_tag:
        input("出现高级资深干员! 请手动选择标签, 按下回车键继续...")
    else:
        option = choose_tag(optional_tag)  # 判断选择标签

        # 记录信息
        recruit_info.selected_tag = option[0]
        recruit_info.possible_operator = option[1]
        recruit_info.score = option[2]

        # 选择标签
        for tag in option[0]:
            click('tag' + str(optional_tag.index(tag) + 1), delay=0.1)

    # 开始招募
    click('开始招募', delay=1)
    click('立即招募')
    click('确认立即招募', delay=2)
    click('聘用候选人', delay=1)
    click('跳过', delay=4)

    # 识别干员
    best_operatorerator = recongnize_operator(id)
    recruit_info.operator = best_operatorerator  # 记录干员信息

    save_recruit_info_with_pandas(recruit_info)  # 保存招募信息

    click('点击屏幕')


if __name__ == '__main__':
    # 获取干员信息
    operators = get_operators()

    # 连接 ADB 调试
    adb_connect()

    for i in range(40, 45):
        auto_recruit(i)

    # 断开 ADB 调试
    adb_disconnect()
