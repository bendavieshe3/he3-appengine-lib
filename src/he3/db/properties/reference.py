'''
The reference module contains properties that relate to other datastore
entities
'''
from google.appengine.ext import db
from google.appengine.api import datastore_errors
from google.appengine.api import datastore

import logging

BadValueError = datastore_errors.BadValueError #pylint:disable=C0103

class ReferenceListProperty(db.ListProperty):
    '''
    The ReferenceListProperty allows a many-to-many relationship between
    2 entity types. As a ListProperty subclass, you interact with the 
    ReferenceListProperty as a list.
    
    ReferenceListProperty, like the ReferenceProperty, creates a corresponding
    collection on the side of the referenced entity
    
    
    CURRENT STATUS
    At time of writing
    - Referenced entities are always retrieved from the datastore. This should
        be replaced by model-instance caching and possibly even lazy loading so
        individual list members can be instanced as required.
    
    
    '''

    def __init__(self, reference_class=None, verbose_name=None, 
                 collection_name=None, reverse_collection_name=None, **attrs):
        '''
        Construct ReferenceListProperty
        
        args:
            reference_class is a db.model class to create a list of references
                of. As per ReferenceProperty
            verbose_name is a human readable name
            collection_name is the name of the query exposed on the 1st party 
                model object
            reverse_collection_name is the name of query attributes on the 
                reference class model object.
        
        raises:
            KindError if the reference class is not a db.model object
            
        '''      
        super(ReferenceListProperty, self).__init__(item_type=db.Key, 
                                                    verbose_name=verbose_name,
                                                    **attrs)
    
        self.collection_name = collection_name
        self.reverse_collection_name = reverse_collection_name
    
        if reference_class is None:
            reference_class = db.Model
        if not (isinstance(reference_class, type) and 
                issubclass(reference_class, db.Model)):
            raise db.KindError('reference_class must be db.Model')
        self.reference_class = self.data_type = reference_class


    def __property_config__(self, model_class, property_name):
        '''
        Adds the normal and reverse collections to the model
        
        
        Args:
        model_class: Model class which will have its reference properties
        initialized.
        property_name: Name of property being configured.
        
        Raises:
        DuplicatePropertyError if referenced class already has the provided
        collection name as a property.
        '''

        super(ReferenceListProperty, self).__property_config__(model_class,
                                                               property_name)
                
        #set up (forward) collection
        if self.collection_name is None:
            self.collection_name = '%s_set' % (
                                    self.reference_class.__name__.lower())     
        
        existing_prop = getattr(self.model_class,
                                self.collection_name, None)
        
        if existing_prop is not None:
            
            if not(isinstance(existing_prop, db._ReverseReferenceProperty) and
                   existing_prop._prop_name == property_name and
                   existing_prop._model.__name__ == self.reference_class.__name__ and
                   existing_prop._model.__module__ == self.reference_class.__module__):
                raise db.DuplicatePropertyError( 
                    'Class %s already has property %s ' % (
                                                    self.model_class.__name__, 
                                                    self.collection_name))                
        #create and attach forward collection
        setattr(self.model_class, self.collection_name,
                _ForwardReferenceProperty(self.reference_class, property_name))        
        
        
        
        #Set up Reverse Collection
        if self.reverse_collection_name is None:
            self.reverse_collection_name = '%s_set' % (
                                            model_class.__name__.lower())
        
        
        
        #check for duplicate reverse_collection_name
        existing_prop = getattr(self.reference_class, 
                                self.reverse_collection_name, None)
        if existing_prop is not None:
            
            if not (isinstance(existing_prop, db._ReverseReferenceProperty) and
                    existing_prop._prop_name == property_name and
                    existing_prop._model.__name__ == model_class.__name__ and
                    existing_prop._model.__module__ == model_class.__module__):
                raise db.DuplicatePropertyError(
                    'Class %s already has property %s '
                    % (self.reference_class.__name__, 
                       self.reverse_collection_name))
                
        #create and attach reverse collection
        setattr(self.reference_class, self.reverse_collection_name,
                db._ReverseReferenceProperty(model_class, property_name))
        

    def validate(self, value):
        '''
        Validate the ReferenceListProperty values as a list of model instance
        of class reference class that have been saved.

        '''

        if value is not None:
            if not isinstance(value, list):
                raise datastore_errors.BadValueError(
                    'Property %s must be a list' % self.name)
            
            value = self.validate_list_contents(value)
            
            #check required, choices, user validator
            value = super(ReferenceListProperty, self).validate(value)
        
        return value
        
    def validate_list_contents(self, value):
        '''
        validates each member of the list as being not None, not a member of 
        any class except reference_class, and being saved. 
        '''
        for member in value:
            
            if isinstance(member, datastore.Key):
                #skip further checks
                continue
            
            if isinstance(member, db.Model) and not member.has_key():
                raise BadValueError(
                    '%s instance must have a complete key before it can be '
                    'stored as a reference' % self.reference_class.kind())
            
            if not isinstance(member, self.reference_class):
                raise db.KindError('All members of %s must be an instance of %s'
                                   % (self.name, self.reference_class.kind())) 
                
        return value

    def get_value_for_datastore(self, model_instance):
        '''
        Returns a list of keys for storage in the datastore
        '''
        entity_list = self.validate_list_contents(
            self.__get__(model_instance, self.reference_class))

        return [e.key() for e in entity_list if e]
    
    def make_value_from_datastore(self, value):
        '''
        Returns a populated list of entity models
        '''
        return db.get(value);

class _ForwardReferenceProperty(db._ReverseReferenceProperty):
    ''' 
    A variation on the _reverseReferenceProperty to change the returned
    query to be effective for 1st party collections
    '''

    def __get__(self, model_instance, model_class):
        '''
        Return a query which will fetch the members specified in the
        ReferenceListProperty
        ''' 
        if model_instance is not None:
            logging.info(self._ReverseReferenceProperty__model)
            query = db.Query(self._ReverseReferenceProperty__model)
            logging.info('here')
            keys = [reference_item.key() for reference_item in 
                    getattr(model_instance, self._ReverseReferenceProperty__property)]
            return query.filter('__key__ IN ', keys)            
        else:
            return self
