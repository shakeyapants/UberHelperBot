from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import api_keys as keys


engine = create_engine(keys.DB_ADDRESS)

db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    chat_id = Column(Integer)
    uber_state = Column(String(70))
    uber_credentials = Column(String)

    def __init__(self, first_name=None, last_name=None, chat_id=None, uber_state=None, uber_credentials=None):
        self.first_name = first_name
        self.last_name = last_name
        self.chat_id = chat_id
        self.uber_state = uber_state
        self.uber_credentials = uber_credentials

    def get_last_request(self):
        return Request.query.filter(Request.user_id == self.id).order_by(Request.id.desc()).first()

    def __repr__(self):
        return '<User {} {}>'.format(self.first_name, self.last_name)


class Request(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True)
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    requested = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))


class Fare(Base):
    __tablename__ = 'fares'
    id = Column(Integer, primary_key=True)
    fare = Column(Float)
    time = Column(DateTime)
    request_id = Column(Integer, ForeignKey('requests.id'))

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)