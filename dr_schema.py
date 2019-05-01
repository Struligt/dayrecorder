
# ==================================================================================================

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date  # Text, Time
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

# import datetime as dt

# for working around sqlite problem with Time
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TIME


@compiles(TIME, "sqlite")
def compile_time_sqlite(type_, compiler, **kw):
    return "TEXT"

# import sqlalchemy.types as types
# from dateutil.parser import parse


# ============ CONSTANTS ================================================================
FK_ON = True  # turns on Foreign Key constraint if sqlite db
# connect to database
Base = declarative_base()

# ========================================================================================


class DataAccessLayer:
    """
    instead of using loadSession stand-alone function that returns session, engine; use this
    (advs: attributes can be easily added, and thereby much more easily accessed than returning arrays)
    Usage:
        dal = DataAccessLayer(db_url)
        dal.connect()
        dal.create_session()
        a_session = dal.session
    """

    def __init__(self, db_url='some conn string', FK_on=FK_ON):
        self.engine = None
        self.session = None
        self.db_url = db_url
        self.is_sqlite = 'sqlite' in db_url
        self.FK_on = FK_on

    def connect(self):
        """ creates a session which can then be accessed as the attribute of the instance
        """
        try:
            self.engine = create_engine(self.db_url, pool_pre_ping=True)
            Base.metadata.create_all(self.engine, checkfirst=True)
        except Exception as exc_:
            print("Error: (caught) : Exception encountered in trying to connnect to db! ")
            print(exc_)
        else:
            self.Session = sessionmaker(bind=self.engine)

    def create_session(self):
        self.session = self.Session()
        if self.FK_on and self.is_sqlite:
            self.session.execute('pragma foreign_keys=on')


# === SCHEMA =======================================================================================

class ActvtyRec(Base):  # activity record
    """ describes activity done, most basic.
    """
    __tablename__ = 'act_recs'
    a_id = Column(Integer, primary_key=True)
    day = Column(Date, index=True)
    startt = Column(TIME, index=True)  # Time not supported by sqlite3; therefore need to convert to string from time if setting, from string to time if getting
    endt = Column(TIME)
    a_done = Column(String(40), ForeignKey('act_cats.a_done'), index=True)  # many-to-one
    comments = Column(String(50), default='NFI')

    __tableargs__ = (UniqueConstraint(day, startt, name='uniq_startt'),
                     UniqueConstraint(day, endt, name='uniq_endt'),
                     )

    def __repr__(self):
        return "<activity record ('%s','%s','%s','%s','%s')>" % (self.day, self.startt, self.endt, self.a_done, self.comments)


class ActvtyCat(Base):  # an activity category
    __tablename__ = 'act_cats'
    a_done = Column(String(40), primary_key=True)  # , index=True)
    a_cat = Column(String(40))  # , primary_key=True)

    activities = relationship('ActvtyRec', backref='category')


# ======== STARTERS ================================================================================


dal = DataAccessLayer()  # starting instance can be used by others (needs to have attributes modified)
