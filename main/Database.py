from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    insight_id = Column(Integer, ForeignKey('insight.id'), nullable=False)
    rating = Column(
        Integer,
        CheckConstraint("rating BETWEEN 1 AND 5 OR rating IS NULL", name="check_rating_range"),
        nullable=True
    )
    comment = Column(String(512), nullable=True)

    #used chatGPT to generate DateTime objects for created_date and modified_date
    # prompt: "The method "utcnow" in class "datetime" is deprecated Use timezone-aware 
    # objects to represent datetimes in UTC; e.g. by calling .now(datetime.timezone.utc)" 
    created_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    modified_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self):
        return (f"<Feedback(id={self.id}, user_id={self.user_id}, insight_id={self.insight_id}, "
                f"rating={self.rating}, created_date={self.created_date}, modified_date={self.modified_date})>")


if __name__ == '__main__':
    engine = create_engine('sqlite:///database.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
