import uuid

import allure
import structlog
from sqlalchemy import create_engine


def allure_attach(fn):
    def wrapper(*args, **kwargs):
        query = kwargs.get('query')
        query = query.compile(compile_kwargs={"literal_binds": True})
        allure.attach(str(query), name='query', attachment_type=allure.attachment_type.TEXT)
        dataset = fn(*args, **kwargs)
        if dataset is not None:
            allure.attach(str(dataset), name='dataset', attachment_type=allure.attachment_type.TEXT)
        return dataset

    return wrapper


class OrmClient:
    def __init__(self, user, password, host, database, isolation_level='AUTOCOMMIT'):
        connection_string = f"postgresql://{user}:{password}@{host}/{database}"
        self.engine = create_engine(connection_string, isolation_level=isolation_level)
        self.db = self.engine.connect()
        self.log = structlog.getLogger(self.__class__.__name__).bind(service='DB')

    def close_connection(self):
        self.db.close()

    @staticmethod
    def _compiled_query(query):
        query = query.compile(compile_kwargs={"literal_binds": True})
        return query

    @allure_attach
    def send_query(self, query):
        query = self._compiled_query(query)
        print(query)
        log = self.log.bind(evet_id=str(uuid.uuid4()))
        log.msg(
            event='request',
            query=str(query),
        )
        dataset = self.db.execute(statement=query)
        result = [row for row in dataset]
        log.msg(
            event='response',
            dataset=[dict(row) for row in result],
        )
        return result

    @allure_attach
    def send_bulk_query(self, query):
        query = self._compiled_query(query)
        log = self.log.bind(evet_id=str(uuid.uuid4()))
        log.msg(
            event='request',
            query=str(query),
        )
        self.db.execute(statement=query)
