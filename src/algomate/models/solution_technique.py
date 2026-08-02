from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint

from algomate.data.database import Base


class SolutionTechnique(Base):
    """解法↔技巧多对多关联表"""
    __tablename__ = "solution_techniques"
    __table_args__ = (
        UniqueConstraint("solution_id", "technique_id", name="uq_solution_technique"),
        {'extend_existing': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    solution_id = Column(Integer, ForeignKey("solution_cards.id", ondelete="CASCADE"), nullable=False)
    technique_id = Column(Integer, ForeignKey("technique_cards.id", ondelete="CASCADE"), nullable=False)