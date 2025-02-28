from sqlalchemy import Column, BigInteger, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Country(Base):
    __tablename__ = 'countries'

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    population_2022 = Column(BigInteger)
    population_2023 = Column(BigInteger)
    population_change = Column(Float)
    continent = Column(String)
    subregion = Column(String)

    def __repr__(self):
        return f"<Country(name='{self.name}', population_2023={self.population_2023})>"

def init_db(engine):
    Base.metadata.create_all(engine)