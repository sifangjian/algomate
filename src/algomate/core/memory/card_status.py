"""
卡牌状态工具函数

提供卡牌状态判断的便捷函数。
"""


def compute_card_status(durability: int, pending_retake: bool) -> str:
    """计算卡牌状态

    Args:
        durability: 当前耐久度
        pending_retake: 是否待重修

    Returns:
        状态字符串: pending_retake / endangered / normal
    """
    if pending_retake or durability == 0:
        return "pending_retake"
    if durability < 30:
        return "endangered"
    return "normal"