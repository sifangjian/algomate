from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class Boss(Base):
    __tablename__ = "bosses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)
    weakness_type = Column(String(30), nullable=False)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False)
    description = Column(Text, nullable=False)

    npc = relationship("NPC", backref="bosses")
    answer_records = relationship("AnswerRecord", back_populates="boss")
