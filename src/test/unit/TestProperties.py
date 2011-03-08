'''
Unit Tests for the he3.db.properties package
'''

import logging

import google.appengine.ext.db as db
from google.appengine.api import datastore_errors
from gaeunit import GAETestCase

from he3.db.properties.date import UtcDateTimeProperty
from he3.db.properties.reference import ReferenceListProperty

#pylint:disable=R0904

class UtcDateTimePropertyTest(GAETestCase):
    '''
    Contains tests for the he3.db.properties.date.UtcDateTimeProperty property
    TODO: Write some tests for this!
    '''

class ReferenceListPropertyTest(GAETestCase):
    '''
    Contains tests for the the he3.db.properties.reference.ReferenceListProperty
    class
    '''
    
    def test_init(self):
        '''
        Test that a model class can be created with a ReferenceListProperty
        attached to it
        '''
        titan = Computer(name='titan')
        
    def test_init_non_model(self):
        '''
        Test that only db.Model objects are allowed as the reference class
        in a ReferenceListProperty
        '''
        
        #note: this proves impossible to test without breaking GaeUnit!

    def test_empty_list(self):
        '''
        Tests that a newly created model object with the ReferenceListProperty
        expresses it as an empty list
        '''
        titan = Computer(name='titan')
                
        self.assertTrue(len(titan.parts) == 0, 'inital length of property is '
                        'not zero')
        #try after putting
        
        titan = Computer.get(titan.put())
        #pylint:disable=E1103
        self.assertTrue(len(titan.parts) == 0, 'final length of property is '
                        'not zero')        
            
    def test_adding_model(self):    #pylint:disable=R0201
        '''
        Tests adding a model to the ReferencePropertyList.
        We expect normal list syntax to work. 
        Eg. titan.parts.append(printer)
        '''
        titan = Computer(name='titan')
        printer = Peripheral(name='printer')
        
        printer.put()
        
        titan.parts.append(printer)
        
        #try persisting
        titan.put()
        
    def test_adding_model_unsaved(self):
        '''
        Tests adding a model object that is unsaved. should raise a 
        BadValueError
        '''
        titan = Computer(name='titan')
        printer = Peripheral(name='printer')
        
        titan.parts.append(printer)
        
        #try persisting
        self.assertRaises(datastore_errors.BadValueError, titan.put)
                
    def test_retrieving_model(self):
        '''test retrieving model entities from the ReferenceListProperty'''
        
        titan = Computer(name='titan')
        printer = Peripheral(name='printer')
        
        printer.put()
        
        
        titan.parts.append(printer)
        printer2 = titan.parts[0]
        
        self.assertTrue(printer.key() == printer2.key())
        
        titan2 = Computer.get(titan.put())
        
        printer3 = titan2.parts[0]
        
        self.assertTrue(printer.key() == printer3.key())
        
    def test_multiple_reference_items_and_order(self):
        
        titan = Computer(name='titan')
        printer = Peripheral(name='printer')
        mouse = Peripheral(name='mouse')
        monitor = Peripheral(name='monitor')
        
        printer.put()
        mouse.put()
        monitor.put()
        
        titan.parts = [printer, mouse, monitor]
        parts_names = [e.name for e in titan.parts]
        titan.put()
        
        titan = Computer.get(titan.key())
        
        self.assertEquals(parts_names, [e.name for e in titan.parts])
        
        
        
        
        
            
class Peripheral(db.Model):
    '''
    Another sample model object to test the capabilities of the 
    ReferencelistProperty
    '''
    
    name = db.StringProperty(required=True)

    
class SomeWidget():
    '''This is something else, NOT a model!'''
    
    
class WackyComputer(db.Model):
    '''
    This wacky computer should not initialise since ReferenceListProperty
    names a non-model as reference class
    '''

    name = db.StringProperty(required=True)
    #this breaks gaeunit. Guess it means it works?
    #parts = ReferenceListProperty(reference_class=SomeWidget, 
    #                              verbose_name=None,
    #                              default=None)        

class Computer(db.Model):
    '''
    A sample model object to test the capabilities of ReferenceListProperty
    '''
    
    name = db.StringProperty(required=True)
    parts = ReferenceListProperty(reference_class=Peripheral, verbose_name=None,
                                  default=None)