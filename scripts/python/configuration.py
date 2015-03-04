# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import shotgun_connection


class ShotConfiguration(object):
    '''Used to get Shot Configurations.
    Data is retrieved in the this order:
    Entity > Project > Default
    For example, if sg_resolution_x is not set on Shot level, value on Project will be returned.
    '''
    DEFAULT_CONFIG = 1
    SG_ENTITY_NAME = 'CustomNonProjectEntity01'
    SG_CONFIG_ATTR = 'sg_configuration'
    SG_CONFIG_KEYS = ['sg_resolution_x',
                      'sg_resolution_y',
                      'sg_fps']

    def __init__(self, project, entity, entity_type='Shot'):
        '''Get shot related config, like resolution and fps, from Shotgun.
        @ project: str, project name, e.g. 'tst';
        @ entity: str or dict, shot name, e.g. 'cd0001' or {'type':'Shot', 'id':25};
        @ entity_type: str, Shotgun entity type, default to 'Shot', ignored if entity is a dict.
        '''
        self.raw_project = project
        self.raw_entity = entity
        self.raw_type = entity_type

        self._sg = None
        self._default = None
        self._project = None
        self._entity = None
        self._fields = ['.'.join([self.SG_CONFIG_ATTR, self.SG_ENTITY_NAME, i])
                        for i in self.SG_CONFIG_KEYS]

    def _init_connection(self):
        if self._sg is None:
            self._sg = shotgun_connection.Connection()

    def getDefault(self):
        if self._default is None:
            self._init_connection()
            self._default = self._sg.find_one(self.SG_ENTITY_NAME,
                                            [['id', 'is', self.DEFAULT_CONFIG]],
                                            self.SG_CONFIG_KEYS)
            assert self._default, 'Default Configuration not found: %s' % self.DEFAULT_CONFIG
        return self._default

    def getProject(self):
        if self._project is None:
            self._init_connection()
            filters = [['name', 'is', self.raw_project]]
            self._project = self._sg.find_one('Project', filters, self._fields)
            assert self._project, 'Project not found on Shotgun: %s' % self.raw_project
        return self._project

    def getEntity(self):
        if self._entity is None:
            self._init_connection()
            if isinstance(self.raw_entity, dict):
                filters = [['id', 'is', self.raw_entity['id']]]
                type_ = self.raw_entity['type']
            else:
                filters = [['project', 'name_is', self.raw_project],
                           ['code', 'is', self.raw_entity]]
                type_ = self.raw_type
            self._entity = self._sg.find_one(type_, filters, self._fields)
            assert self._entity, 'Entity not found on Shotgun: %s %s' % (type_, self.raw_entity)
        return self._entity

    def __getattr__(self, attr):
        assert attr in self.SG_CONFIG_KEYS, 'Invalid attribute: %s' % attr
        field = '.'.join([self.SG_CONFIG_ATTR, self.SG_ENTITY_NAME, attr])
        value = self.getEntity().get(field)
        if value is None:
            value = self.getProject().get(field)
            if value is None:
                value = self.getDefault().get(attr)
        return value

    def get(self, attr):
        return getattr(self, attr)


if __name__ == '__main__':
    # example usage
    config = ShotConfiguration('tst', 'cd0001')
    print config.sg_resolution_x
    print config.sg_fps
    print config.get('sg_resolution_x')
