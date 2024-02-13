class Operator:
    """
    干员类, 用于存储干员的基本信息

    Attributes:
        name: 干员名字
        url: 干员详细信息页面的URL
        star: 星级
        class_name: 职业
        pos: 位置
        tag: 标签
        public_recruit: 是否可以通过公开招募获得
        report: 干员报道语音内容
    """

    name: str
    url: str
    star: int
    class_name: str
    pos: str
    tag: list
    public_recruit: bool
    report: str

    def __init__(self, name, url, star=0, class_name="", pos="", tag=[], public_recruit=False, report=""):
        self.name = name
        self.url = url
        self.star = star
        self.class_name = class_name
        self.pos = pos
        self.tag = tag
        self.public_recruit = public_recruit
        self.report = report
