import logging
import google.appengine.ext.db as db

from datetime import date
from he3.db.tower.paging import PagedQuery, PageLinks
from gaeunit import GAETestCase
	
class PagedQueryTest(GAETestCase):
	'''Contains tests for the utilities.db.pages.PagedQuery class'''
	
	def setUp(self):
		self.util_create_test_persons_data()
		self.pagedQuery = self.util_create_persons_pagedQuery()
		self.pagedGqlQuery = self.util_create_persons_GQL_pagedQuery()
			
	def test_setup(self):
		waricks_children_query = PersonTestEntity.all().ancestor(self.warwick)
		children = waricks_children_query.fetch(10)
		#self.util_log_persons_names(children)

		self.assertTrue(
			PersonTestEntity.all().ancestor(self.warwick).count(100) == 6)
		self.assertTrue(self.pagedQuery)

	def test_instancing(self):
		'''Tests instancing of the object'''
		
		#test 1 - should fail - no parameters
		self.assertRaises(TypeError, PagedQuery)
		
		#test 2 - should fail (no pagesize)
		self.assertRaises(TypeError, PagedQuery, PersonTestEntity.all())
		self.assertRaises(TypeError, PagedQuery, PersonTestEntity.gql(
							'WHERE ANCESTOR IS :parent', self.warwick))
		
		#test 3 - should pass
		pagedQuery = PagedQuery(PersonTestEntity.all(), 5)
		pagedQuery = PagedQuery(PersonTestEntity.gql(
								'WHERE ANCESTOR IS :parent', self.warwick), 5)
	
		#test 4 - should fail due to bad query type
		self.assertRaises(TypeError, PagedQuery, {}, 5)
		self.assertRaises(TypeError, PagedQuery, object(), 5)
	
	def test_fetch(self):
		'''Tests that fetch behaves normally'''
		
		#test1 - should succeed and return 6 results
		persons = self.pagedQuery.fetch(limit=10)
		self.assertTrue(len(persons)==6)

		#test1b - should succeed and return 6 results
		persons = self.pagedGqlQuery.fetch(limit=10)
		self.assertTrue(len(persons)==6)
		
		#test2 - should succeed and return 3 result
		persons = self.pagedQuery.fetch(limit=10, offset=3)
		self.assertTrue(len(persons)==3)
		
		#test2b - should succeed and return 3 result
		persons = self.pagedGqlQuery.fetch(limit=10, offset=3)
		self.assertTrue(len(persons)==3)
		
		#test3 - should succeed and return 6 results
		persons = self.pagedQuery.fetch(10)
		self.assertTrue(len(persons)==6)

		#test3b - should succeed and return 6 results
		persons = self.pagedGqlQuery.fetch(10)
		self.assertTrue(len(persons)==6)
		
		#test4 - should error (required args not present)
		self.assertRaises(TypeError, self.pagedQuery.fetch)
		
		#test4b - should error (required args not present)
		self.assertRaises(TypeError, self.pagedGqlQuery.fetch)
		
		
	def test_filter(self):
		'''Tests the filter method behaves correctly'''
		
		#test1 - should succeed and return 2 results
		persons = self.pagedQuery.filter('birthdate >', date(1981,1,1)).fetch(10)
		self.assertTrue(len(persons)==2)
		
		#test2 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.pagedQuery.filter)
		
		#test3 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.pagedQuery.filter, 'name >')
		
		#test4 - should fail with GqlQuery
		self.assertRaises(TypeError, self.pagedGqlQuery.filter, 'birthdate >', date(1981,1,1))		
	
	def test_order(self):
		'''Tests the order method behaves correctly'''
		
		#test1 - should succeed and return results in birthdate ascending order
		persons = self.pagedQuery.order('birthdate').fetch(10)
		self.assertTrue(len(persons)==6)
		
		last_birthdate = None
		for person in persons:
			if not last_birthdate: last_birthdate = person.birthdate
			else: self.assertTrue(person.birthdate >= last_birthdate)
		
		#test2 - should succeed and return results in birthdate descending order
		self.pagedQuery = self.util_create_persons_pagedQuery()
		persons = self.pagedQuery.order('-birthdate').fetch(10)
		self.assertTrue(len(persons)==6)
		
		last_birthdate = None
		for person in persons:
			if not last_birthdate: last_birthdate = person.birthdate
			else: self.assertTrue(person.birthdate <= last_birthdate)
		
		#test3 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.pagedQuery.order)
		
		#test4 - should fail (too many arguments)
		self.assertRaises(TypeError, self.pagedQuery.order, 'birthdate', 'asc')
	
		#test5 - should fail for GqlQuery
		self.assertRaises(TypeError, self.pagedGqlQuery.order, 'birthdate')
	
	def test_ancestor(self):
		'''Tests the ancestor method behaves correctly'''
		
		#test 1- should succeed and return 6 results
		persons = self.pagedQuery.ancestor(self.warwick).fetch(10)
		self.assertTrue(len(persons)==6)
		
		#test 2 - should succeed and return 1 results
		self.pagedQuery = self.util_create_persons_pagedQuery()
		persons = self.pagedQuery.ancestor(self.marilyn).fetch(10)
		self.assertTrue(len(persons)==1)
		
		#test 3 - should fail - too few arguments
		self.pagedQuery = self.util_create_persons_pagedQuery()
		self.assertRaises(TypeError, self.pagedQuery.ancestor)
				
		#test 4 - should fail - too many arguments
		self.pagedQuery = self.util_create_persons_pagedQuery()
		self.assertRaises(TypeError, self.pagedQuery.ancestor,
						self.warwick, self.marilyn)
		
		#test 5 - should fail with TypeError - GqlQuery not supported
		self.pagedQuery = self.util_create_persons_GQL_pagedQuery()
		self.assertRaises(TypeError, self.pagedQuery.ancestor, self.warwick)
		
		
	def test_count(self):
		'''Tests that the count method behaves correctly'''
		
		#test 1 - (with high limit) should succeed and return 6
		self.assertTrue( self.pagedQuery.count(10) == 6 )
		self.assertTrue( self.pagedGqlQuery.count(10) == 6 )
		
		#test 2 - (with no limit) should succeed and return 6
		self.assertTrue( self.pagedQuery.count() == 6 )
		self.assertTrue( self.pagedGqlQuery.count() == 6 )
		
		#test 3 - (with low limit) should succeed and return 2 results
		self.assertTrue( self.pagedQuery.count(2) == 2 )
		self.assertTrue( self.pagedGqlQuery.count(2) == 2 )		
		
		#test 4 - (with too many params) should fail
		self.assertRaises( TypeError, self.pagedQuery.count, 2, 4)		
		
	def test_attr_page_size(self):
		'''Tests the page_size attribute works correctly'''
		
		#test 1 -- read of initialised page_size value works
		self.assertTrue(self.pagedQuery.page_size == 2)
		self.assertTrue(self.pagedGqlQuery.page_size == 2)
		
		#test 2 -- Setting a new page size works
		self.pagedQuery.page_size = 4
		self.assertTrue(self.pagedQuery.page_size == 4)
		
		self.pagedGqlQuery.page_size = 5
		self.assertTrue(self.pagedGqlQuery.page_size == 5)
		
		#test 3 -- Settings an invalid page size raises an exception
		self.assertRaises(TypeError, self.pagedQuery.__setattr__,'page_size',0)
		self.assertRaises(TypeError, self.pagedQuery.__setattr__,'page_size',-1)
		self.assertRaises(TypeError, self.pagedQuery.__setattr__,'page_size',1.5)
		self.assertRaises(TypeError, self.pagedQuery.__setattr__,'page_size','invalid')
				
	def test_fetch_page_same_progressive(self):
		'''Tests the fetch_page() method to ensure it is working correctly
		within a single request and progressive advancement'''
		
		self.pagedQuery.order('birthdate').order('name')
		
		#test 1 -- Call fetch_page() without arguments and receive the first
		#page of results (2)
		persons = self.pagedQuery.fetch_page()
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
		
		persons = self.pagedGqlQuery.fetch_page()
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
				
		#test 2 -- Call fetch_page(1) and received the first page of results (2)
		persons = self.pagedQuery.fetch_page(1)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
		
		persons = self.pagedGqlQuery.fetch_page(1)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
		
		#test 3 -- Call fetch_page(2) and received the second page of results (2)
		persons = self.pagedQuery.fetch_page(2)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Richard')
		self.assertTrue(persons[1].name == 'Shannon')
		
		persons = self.pagedGqlQuery.fetch_page(2)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Richard')
		self.assertTrue(persons[1].name == 'Shannon')		
				
		#test 4 -- Call fetch_page(3) and receive the third page of results (2)
		persons = self.pagedQuery.fetch_page(3)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Colleen')
		self.assertTrue(persons[1].name == 'Kate')
		
		persons = self.pagedGqlQuery.fetch_page(3)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Colleen')
		self.assertTrue(persons[1].name == 'Kate')
		
		#test 5 -- Call fetch_page(4) and receive the an empty set of results
		persons = self.pagedQuery.fetch_page(4)
		self.assertTrue(len(persons)==0)
		
		persons = self.pagedGqlQuery.fetch_page(4)
		self.assertTrue(len(persons)==0)
				
		#test 6 -- Call fetch_page(5) and receive the an empty set of results
		persons = self.pagedQuery.fetch_page(5)
		self.assertTrue(len(persons)==0)
		
		persons = self.pagedGqlQuery.fetch_page(5)
		self.assertTrue(len(persons)==0)

	def test_fetch_page_same_random(self):
		'''Tests the fetch_page() method to ensure it is working correctly
		within a single request and random advancement'''
		
		self.pagedQuery.order('birthdate').order('name').clear()
		
		offset_query_count = self.pagedQuery._num_offset_queries

		
		#test 1 -- Call fetch_page(2)and receive the second page of results (2)
		persons = self.pagedQuery.fetch_page(2)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Richard')
		self.assertTrue(persons[1].name == 'Shannon')
		#this SHOULD use an offset query to jump to page 2 without fetching
		#page 1 first.
				
		persons = self.pagedGqlQuery.fetch_page(2)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Richard')
		self.assertTrue(persons[1].name == 'Shannon')	
				
		#test 2 -- Call fetch_page(1) and receive the first page of results
		persons = self.pagedQuery.fetch_page(1)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
		#should not use offset query since this is page 1
		
		persons = self.pagedGqlQuery.fetch_page(1)
		self.assertTrue(len(persons)==2)
		
		self.assertTrue(persons[0].name == 'Warwick')
		self.assertTrue(persons[1].name == 'Alex')
		
		#test 3 - Call fetch_page(4) and receive an empty set of results
		persons = self.pagedQuery.fetch_page(4)
		self.assertTrue(len(persons)==0)
		#should not use offset query since we already know there is no page 4
		
		persons = self.pagedGqlQuery.fetch_page(4)
		self.assertTrue(len(persons)==0)
		
		#test 4 - Call fetch_page(3) and receive the third page of results(2)
		persons = self.pagedQuery.fetch_page(3)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Colleen')
		self.assertTrue(persons[1].name == 'Kate')
		#should not use offset query since page 2 has been called.
				
		persons = self.pagedGqlQuery.fetch_page(3)
		self.assertTrue(len(persons)==2)
		self.assertTrue(persons[0].name == 'Colleen')
		self.assertTrue(persons[1].name == 'Kate')	
		
		self.assertTrue(offset_query_count + 1 == self.pagedQuery._num_offset_queries)
							
	
	def test_clear(self):
		'''Tests that the clear() method works'''
		
		#test 1 - PageQueries start out with no caching
		self.assertTrue(self.pagedQuery._page_cursors == [None])
		self.assertTrue(self.pagedGqlQuery._page_cursors == [None])
		
		#test 2 - After fetching a page, there appears to be caching
		persons = self.pagedQuery.fetch_page(2)
		self.assertFalse(self.pagedQuery._page_cursors == [None])
		
		persons = self.pagedGqlQuery.fetch_page(2)
		self.assertFalse(self.pagedGqlQuery._page_cursors == [None])
		
		#test 3 - After calling() clear, there appears to be no caching again
		self.pagedQuery.clear()
		self.assertTrue(self.pagedQuery._page_cursors == [None])
		
		self.pagedGqlQuery.clear()
		self.assertTrue(self.pagedGqlQuery._page_cursors == [None])
		
		#test 4 - if we filter a Db.Query based PagedQuery, the cache should be 
		#cleared as well
		persons = self.pagedQuery.fetch_page(2)
		self.pagedQuery.filter('name >','C' )
		self.assertTrue(self.pagedQuery._page_cursors == [None])
		
		#test 5 - if we order a Db.Query based on PagedQuery, the cache should 
		#be cleared as well.
		self.pagedQuery = self.util_create_persons_pagedQuery()
		persons = self.pagedQuery.fetch_page(2)
		self.pagedQuery.order('-name')
		self.assertTrue(self.pagedQuery._page_cursors == [None])

		#test 6 - if we add an ancestor condition to the query, the cache should
		#also be cleared
		self.pagedQuery = self.util_create_persons_pagedQuery()
		persons = self.pagedQuery.fetch_page(2)
		self.pagedQuery.ancestor(self.kate)
		self.assertTrue(self.pagedQuery._page_cursors == [None])
		

					
	def test_page_count(self):
		'''Tests that the page_count() method works as expected'''
		
		#test 1 - PageCount returns correct value(6) on unfetched query
		count_call_count = self.pagedQuery._num_count_calls
		self.assertTrue(self.pagedQuery.page_count() == 3)
		self.assertTrue(count_call_count + 1 == self.pagedQuery._num_count_calls)
		
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)

		#test 2 - PageCount returns correct value(3) on same fetched query 
		#(fetched to before the end of the dataset)
		#note count() not re-executed 
				
		persons = self.pagedQuery.fetch_page(2)
		count_call_count = self.pagedQuery._num_count_calls
		self.assertTrue(self.pagedQuery.page_count() == 3)
		self.assertTrue(count_call_count == self.pagedQuery._num_count_calls)
		
		persons = self.pagedGqlQuery.fetch_page(2)
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)
		
		#test 2b - PageCount returns correct value(3) on same fetched query 
		#(fetched to after the end of the dataset)
		persons = self.pagedQuery.fetch_page(4)
		self.assertTrue(self.pagedQuery.page_count() == 3)
		
		persons = self.pagedGqlQuery.fetch_page(4)
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)				
		
		#test 3 - PageCount returns correct value(6) on new fetched query
		self.pagedQuery = self.util_create_persons_pagedQuery()
		self.pagedGqlQuery = self.util_create_persons_GQL_pagedQuery()

		persons = self.pagedQuery.fetch_page(2)
		self.assertTrue(self.pagedQuery.page_count() == 3)
		
		persons = self.pagedGqlQuery.fetch_page(2)
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)		
		
		#test 4 - After removing 2 people and not calling clear(), the value
		#of page_count() is not changed

		persons = self.pagedQuery.fetch_page(2)
		for person in persons:
			person.delete()
			
		self.assertTrue(self.pagedQuery.page_count() == 3)	
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)
		
		#test 5 - If we clear() the PagedQuery, the correct result is returned
		self.pagedQuery.clear()
		self.assertTrue(self.pagedQuery.page_count() == 2)
		
		self.pagedGqlQuery.clear()
		self.assertTrue(self.pagedGqlQuery.page_count() == 2)
		
		#test 6 - If add one more person and call clear, the correct result is
		#returned(3)
		lilly = PersonTestEntity(
								parent=self.kate,
								name='Lilly',
								birthdate=date(year=2008,month=4,day=20))
		lilly.put()
				
		self.pagedQuery.clear()
		self.assertTrue(self.pagedQuery.page_count() == 3)

		self.pagedGqlQuery.clear()
		self.assertTrue(self.pagedGqlQuery.page_count() == 3)
		
	def test_page_count_advanced(self):
		'''Tests the page_count() method in cases where query.count() should not
		be called'''

		offset_query_count = self.pagedQuery._num_offset_queries
		count_call_count = self.pagedQuery._num_count_calls

		persons = self.pagedQuery.fetch_page(1)
		persons = self.pagedQuery.fetch_page(2)
		persons = self.pagedQuery.fetch_page(3)
		persons = self.pagedQuery.fetch_page(4)

		self.assertTrue(offset_query_count == self.pagedQuery._num_offset_queries)
		self.assertTrue(count_call_count == self.pagedQuery._num_count_calls)

		
		self.assertTrue(len(self.pagedQuery._page_cursors) == 4)
		self.assertTrue(self.pagedQuery._page_cursors[0] == None)
		self.assertTrue(self.pagedQuery._page_cursors[1] != None)
		self.assertTrue(self.pagedQuery._page_cursors[2] != None)
		self.assertTrue(self.pagedQuery._page_cursors[3] == None)

	def test_fetch_page_progressive_opt(self):
		'''Tests what should be optimum query sequence (Page 1 to 3 to 1)'''
		
		offset_query_count = self.pagedQuery._num_offset_queries
		count_call_count = self.pagedQuery._num_count_calls
		count_persist = self.pagedQuery._num_persist
		count_restore = self.pagedQuery._num_restore
		
		self.assertTrue(count_persist == 0)
		self.assertTrue(count_restore == 0)
		
		self.assertTrue(self.pagedQuery._last_persisted_as == None)
		
		persons = self.pagedQuery.fetch_page(1, clear=True)
		persons = self.pagedQuery.fetch_page(2)
		persons = self.pagedQuery.fetch_page(3)
		persons = self.pagedQuery.fetch_page(2)
		self.util_test_cursor_set(self.pagedQuery._page_cursors)
		persons = self.pagedQuery.fetch_page(1)
		
		self.assertTrue(offset_query_count == self.pagedQuery._num_offset_queries)
		self.assertTrue(count_call_count == self.pagedQuery._num_count_calls)
		
		count_persist_1 = self.pagedQuery._num_persist
		count_restore_1 = self.pagedQuery._num_restore
		
		logging.info((count_persist_1, count_restore_1))
		
		self.assertTrue(count_restore_1 == 0)
		self.assertTrue(count_persist_1 == 3)
		
		

	def test_cross_request_caching(self):
		'''Tests the behaviours of PagedQuery across different requests. Uses
		test_cross_request_caching_b() and _c()'''

		#test a-1: fetch a first page of results, and on the next request
		#fetch the second. No offset methods should be called
		q0 = self.util_create_persons_pagedQuery()

		self.assertTrue(q0._last_persisted_as == None)
		self.assertTrue(q0._num_offset_queries == 0)
		self.assertTrue(len(q0._page_cursors) == 1)
		
		persons = q0.fetch_page()
		
		self.assertTrue(q0._last_persisted_as != None)
		self.assertTrue(q0._num_offset_queries == 0)
		self.assertTrue(len(q0._page_cursors) == 2)

		#test a-1: fetch a first page of results, and on the next request
		#fetch the second. No offset methods should be called
		q1 = self.util_create_persons_pagedQuery()
		
		self.assertTrue(q1._last_persisted_as == None)
		self.assertTrue(q1._num_offset_queries == 0)
		self.assertTrue(len(q1._page_cursors) == 1)
		
		persons = q1.fetch_page(2)
	
		self.assertTrue(q1._last_persisted_as != None)
		self.assertTrue(len(q1._page_cursors) == 3)
		self.assertTrue(q0._page_cursors[1] == q1._page_cursors[1])		
		self.assertTrue(q1._last_persisted_as != None)
		self.assertTrue(q1._num_offset_queries == 0)
				
	def test_id(self):
		'''Tests the Id method within a single request'''
		
		#test 2 different objects of the same query
		q = self.util_create_persons_pagedQuery()
		p = self.util_create_persons_pagedQuery()
		self.assertTrue(p.id == q.id)
		
		r = self.util_create_persons_GQL_pagedQuery()
		s = self.util_create_persons_GQL_pagedQuery()
		self.assertTrue(r.id == s.id)
		
		#test the two queries are not the same id
		self.assertFalse(p.id == r.id)
		
		#add a filter to q and ensure id changes
		q_id = q.id
		persons_1 = q.fetch_page(1)
			
		q.filter('name >', 'c')
		persons_2 = q.fetch_page(1)
		
		self.assertTrue(persons_1 != persons_2)
		self.assertTrue(q_id != q.id)
		
		
		#reset q, add filter using inline chaining
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q.fetch_page(1)
		self.assertTrue(q_id != q.filter('name =','Warwick').id)
		
		#add an order to q1 and ensure id changes
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q.order('-name')
		g_id2 = q.id
		self.assertTrue(q_id != g_id2)
						
		#add an order to q1 and ensure id changes (inline)
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		self.assertTrue(q_id != q.order('-name').id)
		
		#add an ancestor to q1 and ensure id changes
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q.ancestor(self.kate)
		self.assertTrue(q_id != q.id)
		
		#add an ancestor to q1 and ensure id changes (inline)
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		self.assertTrue(q_id != q.ancestor(self.kate).id)
	
		#perform a fetch and ensure id does not change
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		persons = q.fetch_page(1)
		self.assertTrue(q_id == q.id)		
	
	def test_id2(self):
		'''Tests the Id method within a single request'''
		
		#add a filter to q and ensure id changes
		q1 = self.util_create_persons_pagedQuery()
		q1_internal_id = q1._id
		self.assertTrue(q1_internal_id == None)
		
		q1_id = q1.id
		q1_internal_id = q1._id
		q1_generated_id = q1._generate_query_id()
		self.assertTrue(q1_internal_id != None)
		self.assertTrue(q1_internal_id == q1_id)
		q1_internal_id = q1._id
		q1_getter = q1._get_query_id()
		
		q1.filter('name >', 'c')
		q2 = q1
		
				
		q2_id = q2.id
		q2_internal_id = q2._id
		q2_generated_id = q2._generate_query_id()
		q2_getter = q2._get_query_id()
		
		self.assertTrue(q2_internal_id == q2_id)
		self.assertTrue(q1_generated_id != q2_generated_id)
				
		self.assertTrue(q1_getter != q2_getter)		
		self.assertTrue(q1_internal_id != q2_internal_id)
		self.assertTrue(q1_id != q2_id)
		
	def test_id3(self):
		#perform a fetch and ensure id does not change
		#note a fetch_page() automatically clears cache and id will change
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q_internal_id = q._id
		
		persons = q.fetch_page(clear=True) #clears
		
		self.assertTrue(q._id != None)
		self.assertTrue(q_id != q.id)
		
		#a different fetch_page(x) shouldn't change the ID
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q_internal_id = q._id
		
		persons = q.fetch_page(1) 
		
		self.assertTrue(q_id == q.id)		
		
		#a different fetch_page(x) shouldn't change the ID
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q_internal_id = q._id
		
		persons = q.fetch_page(3) 
		
		self.assertTrue(q_id == q.id)
		
		#a different fetch_page(x) shouldn't change the ID
		q = self.util_create_persons_pagedQuery()
		q_id = q.id
		q_internal_id = q._id
		
		persons = q.fetch_page(5) 
		
		self.assertTrue(q_id == q.id)		
		
	def test_id_principle(self):
		'''Tests the underlying principle for identifying queries'''
		import pickle
		
		q1 = PersonTestEntity.all().ancestor(self.warwick)
		q1_pickle = pickle.dumps(q1, 2)
		q1_hash = hash(q1_pickle)
		q1_str = str(q1_hash)
		
		q2 = q1.filter('name >', 'c')
		q2_pickle = pickle.dumps(q2, 2)
		q2_hash = hash(q2_pickle)
		q2_str = str(q2_hash)
		
		self.assertTrue(q1_pickle != q2_pickle)
		self.assertTrue(q1_hash != q2_hash)
		self.assertTrue(q1_str != q2_str)
		
		q1 = PersonTestEntity.all()
		q1_pickle = pickle.dumps(q1, 2)
		q1_hash = hash(q1_pickle)
		q1_str = str(q1_hash)
		
		q2 = q1.order('-name')
		q2_pickle = pickle.dumps(q2, 2)
		q2_hash = hash(q2_pickle)
		q2_str = str(q2_hash)
		
		self.assertTrue(q1_pickle != q2_pickle)
		self.assertTrue(q1_hash != q2_hash)
		self.assertTrue(q1_str != q2_str)

		q1 = PersonTestEntity.all()
		q1_pickle = pickle.dumps(q1, 2)
		q1_hash = hash(q1_pickle)
		q1_str = str(q1_hash)
		
		q2 = q1.fetch(2)
		q2_pickle = pickle.dumps(q2, 2)
		q2_hash = hash(q2_pickle)
		q2_str = str(q2_hash)
		
		self.assertTrue(q1_pickle != q2_pickle)
		self.assertTrue(q1_hash != q2_hash)
		self.assertTrue(q1_str != q2_str)		

	def test_has_page(self):
		'''Tests the has_page() method'''
		
		self.assertTrue(self.pagedQuery.has_page(0) == False)
		self.assertTrue(self.pagedQuery.has_page(1) == True)
		self.assertTrue(self.pagedQuery.has_page(3) == True)
		self.assertTrue(self.pagedQuery.has_page(4) == False)
		self.assertTrue(self.pagedQuery.has_page(10) == False)
		
		self.assertTrue(self.pagedGqlQuery.has_page(0) == False)
		self.assertTrue(self.pagedGqlQuery.has_page(1) == True)
		self.assertTrue(self.pagedGqlQuery.has_page(3) == True)
		self.assertTrue(self.pagedGqlQuery.has_page(4) == False)
		self.assertTrue(self.pagedGqlQuery.has_page(10) == False)
		
	def test_has_page_performance(self):
		'''Test the operating characteristics of has_page(), in particular
		where a full page_count is called'''
		
		#Test for page 1 - page count should be called
		page_count = self.pagedQuery._num_count_calls
		logging.info(page_count)
		hp1 = self.pagedQuery.has_page(1)
		logging.info(self.pagedQuery._num_count_calls)
		self.assertTrue(page_count + 1 == self.pagedQuery._num_count_calls)
		
		#Test after fetching page 3 - page count should not be called for
		#has_page(3) (already called)
		people = self.pagedQuery.fetch_page(3)
		page_count = self.pagedQuery._num_count_calls
		hp1 = self.pagedQuery.has_page(3)
		self.assertTrue(page_count == self.pagedQuery._num_count_calls)		
		
		#test has_page(10) - we expect page_count not to be called since it has 
		#already been called 
		page_count = self.pagedQuery._num_count_calls
		hp1 = self.pagedQuery.has_page(10)
		self.assertTrue(page_count  == self.pagedQuery._num_count_calls)		

		self.pagedQuery.clear()
		
		#Test after fetching page 3 - page count should not be called for
		#has_page(3) (cursor exists)
		people = self.pagedQuery.fetch_page(1)
		people = self.pagedQuery.fetch_page(2)
		people = self.pagedQuery.fetch_page(3)
		page_count = self.pagedQuery._num_count_calls
		hp1 = self.pagedQuery.has_page(3)
		self.assertTrue(page_count == self.pagedQuery._num_count_calls)		
		
		#test has_page(4) - we expect page_count to be called since a cursor
		#does not exist and page count should not already have been called.
		#NB - offset bug meant not sequential page fetches would cause a page_count()
		#which would ruin this test.
		page_count = self.pagedQuery._num_count_calls
		#logging.info(page_count)
		hp1 = self.pagedQuery.has_page(4)
		#logging.info(self.pagedQuery._num_count_calls)
		self.assertTrue(page_count + 1 == self.pagedQuery._num_count_calls)		

	def util_test_cursor_set(self, cursors):
		'''utility function to test a set of cursors for validity'''
		
		for cursor_idx in range(0,len(cursors)):
			for cursor_idx_2 in range(0,len(cursors)):
				if cursor_idx != cursor_idx_2:
					self.assertTrue(cursors[cursor_idx] != cursors[cursor_idx_2])
				
		
	def util_create_persons_pagedQuery(self):
		'''creates a new pagedQuery object for all PersonTestEntities
		with Warwick entity as ancestor (includes Warwick)'''
		return PagedQuery(PersonTestEntity.all().ancestor(self.warwick),2)
	
	
	def util_create_persons_GQL_pagedQuery(self):
		'''creates a new pagedQuery object for all PersonTestEntities
		using GQL'''
		gqlQuery = PersonTestEntity.gql(
									'WHERE ANCESTOR IS :parent ORDER BY birthdate, name', 
									parent=self.warwick)
		return PagedQuery(gqlQuery, 2)
	
	def util_create_test_persons_data(self):
		'''creates a set of test data'''
		
		self.warwick = PersonTestEntity(
								name='Warwick', 
								birthdate=date(year=1950,month=6,day=18))
		self.warwick.put()
		self.marilyn = PersonTestEntity(
								name='Marilyn', 
								birthdate=date(year=1955,month=6,day=18))
		self.marilyn.put()
		self.alex = PersonTestEntity(
							parent=self.warwick,
							name='Alex',
							birthdate=date(year=1978,month=3, day=9))
		self.alex.put()
		self.richard = PersonTestEntity(
							parent=self.warwick,
							name='Richard',
							birthdate=date(year=1979,month=8, day=14))
		self.richard.put()
		self.shannon = PersonTestEntity(
								parent=self.warwick,
								name='Shannon',
								birthdate=date(year=1980,month=3,day=26))
		self.shannon.put()
		self.kate = PersonTestEntity(
							parent=self.warwick,
							name='Kate',
							birthdate=date(year=1982,month=4,day=2))
		self.kate.put()
		self.colleen = PersonTestEntity(
							parent=self.warwick,
							name='Colleen',
							birthdate=date(year=1982,month=4,day=2))
		self.colleen.put()
	
	def util_log_persons_names(self, persons):
		logging.info([x.name for x in persons])

	def util_log_cursors(self,cursors):
		logging.info([x[:6] if x else None for x in cursors])
		
	
class PersonTestEntity(db.Model):
	'''This is an entity to be used for testing purposes. It is intended to be
	application agnostic'''
	
	name = db.StringProperty(required=True)
	birthdate = db.DateProperty(default=None)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	
	
class PageLinksTest(GAETestCase):
	'''Contains tests for the utilities.db.pages.PageLinks class'''
	
	def test_small_page_count(self):
		
		#test with default size
		pageLinks = PageLinks(2,3,'/blah', 'page')
		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 5)
		
		#test with different size
		pageLinks = PageLinks(2,3,'/blah', 'page',3)
		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 5)
		
		#test with different size
		pageLinks = PageLinks(2,3,'/blah', 'page',20)
		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 5)		
		
	def test_large_page_count(self):
		#test with default size
		pageLinks = PageLinks(2,30,'/blah', 'page')
		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 12) #ten page + 2
		
		#test with custom size
		pageLinks = PageLinks(2,30,'/blah', 'page',6)		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 8) #ten page + 2
		
		#test with first page
		pageLinks = PageLinks(1,30,'/blah', 'page',6)
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 7) #6 pages + 1
		
		#test with last page
		pageLinks = PageLinks(30,30,'/blah', 'page',6)
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 5) #4 pages + 1

	def test_with_one_page(self):
		#test with default size
		pageLinks = PageLinks(1,1,'/blah', 'page')
		
		myLinks = pageLinks.get_links()
		logging.info(myLinks)		
		self.assertTrue(len(myLinks) == 1) 
		
		#test with custom size
		pageLinks = PageLinks(1,1,'/blah', 'page',6)		
		myLinks = pageLinks.get_links()
		self.assertTrue(len(myLinks) == 1)
		
	def test_with_question_mark_exists(self):
		#test with default size
		pageLinks = PageLinks(1,1,'/blah?foo=23', 'page')
		
		myLinks = pageLinks.get_links()	
		self.assertTrue(myLinks[0][1].count('?') == 1)
		self.assertTrue(myLinks[0][1].count('&') == 1) 

		
	def test_without_question_mark_exists(self):
		#test with default size
		pageLinks = PageLinks(1,1,'/blah', 'page')
		
		myLinks = pageLinks.get_links()
		self.assertTrue(myLinks[0][1].count('?') == 1)
		self.assertTrue(myLinks[0][1].count('&') == 0) 
		
	
	