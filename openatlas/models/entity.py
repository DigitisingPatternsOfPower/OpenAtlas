# -*- coding: utf-8 -*-
import openatlas
from openatlas import ClassMapper


class Entity(object):
    def __init__(self, row):
        self.id = row.id
        self.name = row.name
        self.description = row.description if row.description else ''
        self.created = row.created
        self.modified = row.modified
        self.begin = row.begin if hasattr(row, 'begin') else None
        self.end = row.end if hasattr(row, 'end') else None
        self.class_ = openatlas.classes[row.class_id]


class EntityMapper(object):

    @staticmethod
    def insert(code, name, description=None):
        sql = """
            INSERT INTO model.entity (name, description, class_id) VALUES (
                %(name)s,
                %(description)s,
                (SELECT id FROM model.class WHERE code = %(code)s)
            ) RETURNING id;"""
        params = {
            'name': name.strip(),
            'code': code,
            'description': description.strip() if description else None}
        cursor = openatlas.get_cursor()
        cursor.execute(sql, params)
        return EntityMapper.get_by_id(cursor.fetchone()[0])

    @staticmethod
    def get_by_id(entity_id):
        sql = """
            SELECT e.id, e.name, e.class_id, e.description, e.created, e.modified
            FROM model.entity e WHERE e.id = %(id)s;"""
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {'id': entity_id})
        openatlas.debug_model['by id'] += 1
        return Entity(cursor.fetchone())

    @staticmethod
    def get_by_codes(codes):
        class_ids = []
        for code in codes if isinstance(codes, list) else [codes]:
            class_ids.append(ClassMapper.get_by_code(code).id)
        sql = """
            SELECT e.id, e.name, e.class_id, e.description, e.created, e.modified
            FROM model.entity e WHERE class_id IN %(class_ids)s;"""
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {'class_ids': tuple(class_ids)})
        entities = []
        for row in cursor.fetchall():
            entities.append(Entity(row))
        openatlas.debug_model['by codes'] += 1
        return entities