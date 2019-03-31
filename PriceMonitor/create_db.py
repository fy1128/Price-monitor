#!/usr/bin/env python3
# coding=utf-8
# import logging
from gevent import monkey  # IMPORT: must import gevent at first
monkey.patch_all()
from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import TypeDecorator, Integer, String, Text, DateTime, Numeric, Boolean, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
import datetime
import json
Base = declarative_base()

class JSONEncodedDict(TypeDecorator):
    @property
    def python_type(self):
        return object

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_literal_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None

Json = MutableDict.as_mutable(JSONEncodedDict)

class User(Base):
    __tablename__ = 'user'
    column_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(32), nullable=False, unique=True)
    email = Column(String(64), nullable=False, unique=True)
    category = Column(String(128))
    endpoint = Column(String(255))
    endpoint_data = Column(Text())


class Monitor(Base):
    __tablename__ = 'monitor'
    column_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(BIGINT, nullable=False)
    item_name = Column(String(128))
    item_price = Column(String(32))  # Please consider storing Decimal numbers as strings or integers on this platform.
    user_price = Column(String(32))  # for lossless storage.
    discount = Column(String(32))
    lowest_price = Column(String(32))
    highest_price = Column(String(32))
    last_price = Column(String(32))
    plus_price = Column(String(32))
    subtitle = Column(String(128))
    area = Column(String(32))
    ext = Column(Json, default=lambda: {})
    user_id = Column(Integer, ForeignKey('user.column_id'))
    note = Column(String(128))
    update_time = Column(DateTime, default=datetime.datetime.now())
    add_time = Column(DateTime, default=datetime.datetime.now())
    status = Column(Boolean, nullable=False, default=1)
    enable = Column(Boolean, nullable=False, default=1)
    user = relationship(User)


class SmartPhone_9987653655(Base):
    __tablename__ = 'SmartPhone_9987653655'
    column_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(BIGINT, nullable=False)
    item_name = Column(String(128))
    item_price = Column(String(32))
    discount = Column(String(32))
    lowest_price = Column(String(32))
    highest_price = Column(String(32))
    last_price = Column(String(32))
    plus_price = Column(String(32))
    subtitle = Column(String(128))
    area = Column(String(32), default="1_72_2799_0") # beijing
    ext = Column(Json, default=lambda: {})
    note = Column(String(128))
    update_time = Column(DateTime, default=datetime.datetime.now())
    add_time = Column(DateTime, default=datetime.datetime.now())
    status = Column(Boolean, nullable=False, default=1)
    enable = Column(Boolean, nullable=False, default=1)

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    engine = create_engine('sqlite:///db_demo.db', echo=True)
    # engine = create_engine('mysql+pymysql://root:root@localhost/pricemonitor?charset=utf8', echo=True, )
    Base.metadata.create_all(engine)
