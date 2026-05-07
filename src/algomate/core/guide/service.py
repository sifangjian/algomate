from typing import Optional, Dict, Any

from algomate.core.guide.models import GuideAction, GuideData


def build_dialogue_end_guide(card: Optional[Dict[str, Any]] = None) -> GuideData:
    if card:
        return GuideData(
            available_actions=[
                GuideAction(
                    action="go_boss",
                    label="去 Boss 战巩固",
                    target_path="/boss",
                    params={"card_id": card["id"]},
                ),
                GuideAction(
                    action="go_workshop",
                    label="去卡牌工坊完善",
                    target_path="/workshop",
                    params={"card_id": card["id"], "expand": True},
                ),
            ],
            message=f"恭喜获得卡牌「{card['name']}」！",
        )
    return GuideData(
        available_actions=[
            GuideAction(
                action="go_workshop",
                label="去卡牌工坊查看",
                target_path="/workshop",
            ),
        ],
        message="卡牌生成失败，对话记录已保存",
    )


def build_boss_result_guide(
    is_victory: bool,
    card_id: int,
    npc_id: Optional[int] = None,
) -> GuideData:
    if is_victory:
        actions = [
            GuideAction(
                action="continue_challenge",
                label="继续挑战",
                target_path="/boss",
            ),
            GuideAction(
                action="go_review",
                label="去修炼巩固",
                target_path="/review",
            ),
        ]
        message = "挑战成功！"
    else:
        actions = [
            GuideAction(
                action="go_review",
                label="去修炼巩固",
                target_path="/review",
            ),
        ]
        if npc_id:
            actions.append(
                GuideAction(
                    action="go_dialogue",
                    label="去重新修习",
                    target_path="/",
                    params={"npc_id": npc_id},
                )
            )
        message = "挑战失败，建议修炼巩固"

    return GuideData(available_actions=actions, message=message)


def build_review_complete_guide(remaining_endangered: int) -> GuideData:
    if remaining_endangered > 0:
        return GuideData(
            available_actions=[
                GuideAction(
                    action="continue_review",
                    label="继续修炼",
                    target_path="/review",
                ),
            ],
            message=f"还有 {remaining_endangered} 张卡牌濒危，是否继续修炼？",
        )
    return GuideData(
        available_actions=[
            GuideAction(
                action="go_boss",
                label="去 Boss 战检验",
                target_path="/boss",
            ),
        ],
        message="所有卡牌状态良好，去 Boss 战检验学习成果吧！",
    )


class GuideService:
    def generate_guides(
        self,
        scene: str,
        card: Optional[Dict[str, Any]] = None,
        is_victory: Optional[bool] = None,
        card_id: Optional[int] = None,
        npc_id: Optional[int] = None,
        remaining_endangered: Optional[int] = None,
        has_available_boss: bool = True,
    ) -> GuideData:
        if scene == "after_dialogue":
            return self._build_dialogue_guide(card, has_available_boss)
        elif scene == "after_boss":
            return self._build_boss_guide(is_victory, card_id, npc_id, has_available_boss)
        elif scene == "after_review":
            return self._build_review_guide(remaining_endangered)
        return GuideData(available_actions=[], message="")

    def _build_dialogue_guide(
        self,
        card: Optional[Dict[str, Any]],
        has_available_boss: bool,
    ) -> GuideData:
        guide = build_dialogue_end_guide(card)
        if not has_available_boss and card:
            guide.available_actions = [
                a for a in guide.available_actions if a.action != "go_boss"
            ]
        return guide

    def _build_boss_guide(
        self,
        is_victory: Optional[bool],
        card_id: Optional[int],
        npc_id: Optional[int],
        has_available_boss: bool,
    ) -> GuideData:
        guide = build_boss_result_guide(
            is_victory=is_victory if is_victory is not None else False,
            card_id=card_id or 0,
            npc_id=npc_id,
        )
        if not has_available_boss and is_victory:
            guide.available_actions = [
                a for a in guide.available_actions if a.action != "continue_challenge"
            ]
        return guide

    def _build_review_guide(self, remaining_endangered: Optional[int]) -> GuideData:
        return build_review_complete_guide(remaining_endangered=remaining_endangered or 0)
