import time
from aar_operator import Operator


class RecruitInfo:
    """
    存储每次公招的所有

    Attributes:
        id (int): 招募编号
        start_time: 开始时间
        optional_tag (list): 可选标签
        selected_tag (list): 选择的标签
        possible_operator (list): 可能的干员
        score (int): 得分
        operator (Operator): 干员
    """

    def __init__(self, id: int, optional_tag: list = [], selected_tag: list = [], possible_operator: list = [], score: int = 0, operator: Operator = None):
        self.id = id
        # 获取当前时间
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.optional_tag = optional_tag
        self.selected_tag = selected_tag
        self.possible_operator = possible_operator
        self.score = score
        self.operator = operator
