#-*-coding:utf-8-*-
"""
@package bcore.core.shotgun.interfaces
@brief Provides an interface to access a shotgun database, pre-initialized and ready to go

@copyright 2013 Sebastian Thiel
"""
__all__ = ['IShotgunConnection']

from bcore import (
                abstractmethod,
                InterfaceBase
                )

class IShotgunConnection(InterfaceBase):
    """Represents a connection to the shotgun database. It obeys the default shotgun API, for reference 
    see https://github.com/shotgunsoftware/python-api/wiki/Reference%3A-Methods
    """
    __slots__ = ()
    
    ## A tuple of method names that are not altering the database. May be used to automate class creation
    ## for instance
    _rw_methods_ = ('create', 'update', 'delete', 'revive', 'batch', 'upload_thumbnail', 
                    'upload_filmstrip_thumbnail', 'share_thumbnail', 'work_schedule_update',
                    'schema_field_delete', 'schema_field_update', 'schema_field_create',
                    'set_session_uuid', 'reset_user_agent', 'add_user_agent')
    
    @abstractmethod
    def find(self, entity_type, filters, fields, order=list(), filter_operator='all', limit=0, retired_only=False, page=0):
        pass
    
    @abstractmethod
    def find_one(self, entity_type, filters, fields=['id'], order=list(), filter_operator='all'):
        pass
    
    @abstractmethod
    def summarize(self, entity_type, filters, summary_fields, filter_operator='all', grouping=list()):
        pass
    
    @abstractmethod
    def create(self, entity_type, data, return_fields=list()):
        pass
    
    @abstractmethod
    def update(self, entity_type, entity_id, data):
        pass
    
    @abstractmethod
    def delete(self, entity_type, entity_id):
        pass
    
    @abstractmethod
    def revive(self, entity_type, entity_id):
        pass
    
    @abstractmethod
    def batch(self, requests):
        pass
    
    @abstractmethod
    def upload(self, entity_type, entity_id, path, field_name='sg_attachment', display_name=None, tag_list=None):
        pass
    
    @abstractmethod
    def upload_thumbnail(self, entity_type, entity_id, path):
        pass
    
    @abstractmethod
    def upload_filmstrip_thumbnail(self, entity_type, entity_id, path):
        pass
    
    @abstractmethod
    def share_thumbnail(self, entities, thumbnail_path=None, source_entity=dict(), filmstrip_thumbnail=False):
        pass
    
    @abstractmethod
    def download_attachment(self, entity_id):
        pass
        
    @abstractmethod
    def work_schedule_read(self, start_date, end_date, project=dict(), user=dict()):
        pass
    
    @abstractmethod
    def work_schedule_update(self, date, working, description=None, project=dict(), user=dict(), recalculate_field=None):
        pass
    
    @abstractmethod
    def authenticate_human_user(self, user_login, user_password):
        pass
        
    @abstractmethod
    def schema_read(self):
        pass
    
    @abstractmethod
    def schema_field_read(self, entity_type, field_name=None):
        pass
    
    @abstractmethod
    def schema_entity_read(self):
        pass
    
    @abstractmethod
    def schema_field_delete(self, entity_type, field_name):
        pass
    
    @abstractmethod
    def schema_field_update(self, entity_type, field_name, properties):
        pass
    
    @abstractmethod
    def schema_field_create(self, entity_type, field_type, display_name, properties=dict()):
        pass
    
    @abstractmethod
    def set_session_uuid(self, session_uuid):
        pass
        
    @abstractmethod
    def add_user_agent(self, agent_string):
        pass
    
    @abstractmethod
    def reset_user_agent(self):
        pass
        
# end class ShotgunConnection

