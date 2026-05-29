from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from typing import Dict, Any

Base = declarative_base()


class AccountTransactionTemplate(Base):
    __tablename__ = "accounts_transaction_template"
    user = Column(String, primary_key=True)
    balance = Column(Integer, nullable=False)
