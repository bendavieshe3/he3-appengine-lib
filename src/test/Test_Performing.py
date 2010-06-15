import google.appengine.ext.db as db
import logging

from datetime import date
from he3.db.tower.performing import PrefetchingQuery
from gaeunit import GAETestCase
	
class PrefetchingQueryTest(GAETestCase):
	'''Contains tests for the utilities.db.tower.prefetchingQuery class'''
	
	def setUp(self):
		self.util_create_test_post_data()
		self.prefetchingQuery = self.util_create_posts_PrefetchingQuery()
		self.prefetchingGqlQuery = self.util_create_posts_GQL_PrefetchingQuery()
			
	def test_setup(self):
		'''Tests that setup executed correctly and test data is in place.'''
		
		self.assertTrue(self.prefetchingQuery)
		self.assertTrue(self.prefetchingGqlQuery)
		
		bills_posts = PostTestEntity.all().ancestor(self.bill).fetch(10)
		self.assertTrue(len(bills_posts) == 4)
		

	def test_instancing(self):
		'''Tests instancing of the object'''
		
		#test 1 - should fail - no parameters
		self.assertRaises(TypeError, PrefetchingQuery)
		
		#test 2 - should succeed with no dereferenced property list
		instance_test_1 = PrefetchingQuery(PostTestEntity.all())
		
		#test 3 - should pass with a dereferenced property list
		instance_test_2 = PrefetchingQuery(PostTestEntity.all()
										, ('prop1', 'prop2'))

		#test 4 - should fail due to bad query type
		self.assertRaises(TypeError, PrefetchingQuery, {}, ('prop1'))
	
	def test_fetch_1(self):
		#test1 - should succeed and return 6 results
		posts = self.prefetchingQuery.order('posted_on').fetch(limit=1)
		self.assertTrue(len(posts)==1)		
	
	def test_fetch(self):
		'''Tests that fetch behaves normally'''
		
		#test1 - should succeed and return 6 results
		posts = self.prefetchingQuery.fetch(limit=10)
		self.assertTrue(len(posts)==4)

		#test1b - should succeed and return 6 results
		posts = self.prefetchingGqlQuery.fetch(limit=10)
		self.assertTrue(len(posts)==4)
		
		#test2 - should succeed and return 3 result
		posts = self.prefetchingQuery.fetch(limit=10, offset=3)
		self.assertTrue(len(posts)==1)
		
		#test2b - should succeed and return 3 result
		posts = self.prefetchingGqlQuery.fetch(limit=10, offset=3)
		self.assertTrue(len(posts)==1)
				
		#test3 - should error (required args not present)
		self.assertRaises(TypeError, self.prefetchingQuery.fetch)
		
		#test3b - should error (required args not present)
		self.assertRaises(TypeError, self.prefetchingGqlQuery.fetch)
		
		#test4 - should succeed and return 2 result
		posts = self.prefetchingQuery.fetch(limit=2, offset=0)
		self.assertTrue(len(posts)==2)
		
		#test2b - should succeed and return 2 result
		posts = self.prefetchingGqlQuery.fetch(limit=2, offset=0)
		self.assertTrue(len(posts)==2)		
		
	def test_filter(self):
		'''Tests the filter method behaves correctly'''		
	
		
		#test1 - should succeed and return 2 results
		posts = self.prefetchingQuery.filter('posted_on >', date(2010,2,4)).fetch(10)
		self.assertTrue(len(posts)==2)
		
		#test2 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.prefetchingQuery.filter)
		
		#test3 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.prefetchingQuery.filter, 'name >')
		
		#test4 - should fail with GqlQuery
		self.assertRaises(TypeError, self.prefetchingGqlQuery.filter, 'posted_on >', date(1981,1,1))

	def test_order(self):
		'''Tests the order method behaves correctly	'''
		
		#test1 - should succeed and return results in posted on ascending order
		posts = self.prefetchingQuery.order('posted_on').fetch(10)
		self.assertTrue(len(posts)==4)
		
		last_posted_on = None
		for post in posts:
			if not last_posted_on: last_posted_on = post.posted_on
			else: self.assertTrue(post.posted_on >= last_posted_on)
		
		#test2 - should succeed and return results in posted on descending order
		self.prefetchingQuery = self.util_create_posts_PrefetchingQuery()
		posts = self.prefetchingQuery.order('-posted_on').fetch(10)
		self.assertTrue(len(posts)==4)
		
		last_posted_on = None
		for post in posts:
			if not last_posted_on: last_posted_on = post.posted_on
			else: self.assertTrue(post.posted_on <= last_posted_on)
		
		#test3 - should fail (not enough arguments)
		self.assertRaises(TypeError, self.prefetchingQuery.order)
		
		#test4 - should fail (too many arguments)
		self.assertRaises(TypeError, self.prefetchingQuery.order, 'posted_on', 'asc')
	
		#test5 - should fail for GqlQuery
		self.assertRaises(TypeError, self.prefetchingGqlQuery.order, 'posted_on')

	
	def test_ancestor(self):
		'''Tests the ancestor method behaves correctly'''
		
		#test 1- should succeed and return 6 results
		posts = self.prefetchingQuery.ancestor(self.bill).fetch(10)
		self.assertTrue(len(posts)==4)
		
		#test 2 - should succeed and return 1 results
		self.prefetchingQuery = self.util_create_posts_PrefetchingQuery()
		posts = self.prefetchingQuery.ancestor(self.post1).fetch(10)
		self.assertTrue(len(posts)==1)
		
		#test 3 - should fail - too few arguments
		self.prefetchingQuery = self.util_create_posts_PrefetchingQuery()
		self.assertRaises(TypeError, self.prefetchingQuery.ancestor)
				
		#test 4 - should fail - too many arguments
		self.prefetchingQuery = self.util_create_posts_PrefetchingQuery()
		self.assertRaises(TypeError, self.prefetchingQuery.ancestor,
						self.bill, self.post1)
		
		#test 5 - should fail with TypeError - GqlQuery not supported
		self.assertRaises(TypeError, self.prefetchingGqlQuery.ancestor, self.post1)

		
	def test_count(self):
		'''Tests that the count method behaves correctly'''
		
		#test 1 - (with high limit) should succeed and return 6
		self.assertTrue( self.prefetchingQuery.count(10) == 4 )
		self.assertTrue( self.prefetchingGqlQuery.count(10) == 4 )
		
		#test 2 - (with no limit) should succeed and return 6
		self.assertTrue( self.prefetchingQuery.count() == 4 )
		self.assertTrue( self.prefetchingGqlQuery.count() ==4 )
		
		#test 3 - (with low limit) should succeed and return 2 results
		self.assertTrue( self.prefetchingQuery.count(2) == 2 )
		self.assertTrue( self.prefetchingGqlQuery.count(2) == 2 )		
		
		#test 4 - (with too many params) should fail
		self.assertRaises( TypeError, self.prefetchingQuery.count, 2, 4)
		
		
	def test_attr_properties_to_prefetch(self):
		'''Tests the properties_to_prefetch attribute works correctly'''

		
		#test 1 -- read of initialised properties_to_prefetch value works
		self.assertTrue(len(self.prefetchingQuery.properties_to_prefetch) == 2)
		self.assertTrue(self.prefetchingQuery.properties_to_prefetch[0] == PostTestEntity.topic)
		self.assertTrue(self.prefetchingQuery.properties_to_prefetch[1] == 'parent')
		self.assertTrue(self.prefetchingGqlQuery.properties_to_prefetch == None)
		
		#test 2 -- Setting a properties_to_prefetch size works
		self.prefetchingQuery.properties_to_prefetch = ('topic',)
		self.assertTrue(len(self.prefetchingQuery.properties_to_prefetch) == 1)
		
		self.prefetchingGqlQuery.properties_to_prefetch = ('parent',)
		self.assertTrue(len(self.prefetchingGqlQuery.properties_to_prefetch) == 1)
		
		#test 3 -- Settings an invalid page size raises an exception
		self.assertRaises(TypeError, self.prefetchingQuery.__setattr__,'properties_to_prefetch',0)
		self.assertRaises(TypeError, self.prefetchingQuery.__setattr__,'properties_to_prefetch',{})
		self.assertRaises(TypeError, self.prefetchingQuery.__setattr__,'properties_to_prefetch',[])
		self.assertRaises(TypeError, self.prefetchingQuery.__setattr__,'properties_to_prefetch','invalid')
		
	def test_automatically_find_refprops(self):
		'''Tests the _automatically_determine_refprops method in PrefetchingQuery'''
		
		post = PostTestEntity(parent=self.bill, title='a post'
							,posted_on = date(2010,1,1))
		refprops = PrefetchingQuery._automatically_determine_refprops(post)
		self.assertTrue(len(refprops) == 2) #parent + topic ref prop

	def test_get_properties_defined_in_class(self):
		'''Tests the private static method get_properties_defined_in_class'''
		post = PostTestEntity(parent=self.bill, title='a post'
							,posted_on = date(2010,1,1))		
		self.assertTrue(PrefetchingQuery._get_properties_defined_in_class(post) is None)
		
		self.assertTrue(len(PrefetchingQuery._get_properties_defined_in_class(self.admin))
					== 1)
		
	def test_is_worthwhile(self):
		'''Tests that PrefetchingQuery actually saves db.get() calls'''
		
		# we will compare the number of initialisations of authors (parents)
		# and topics in 2 queries - 1 normal and one prefetched
		normalQuery = PostTestEntity.all().ancestor(self.bill)
		pfQuery = self.prefetchingQuery						
		
		#run normal test
		PostTopicTestEntity.number_of_inits = 0
		UserTestEntity.number_of_inits = 0
		
		normals = normalQuery.fetch(100)
		authors = [post.parent().name for post in normals]
		topics = [post.topic.topic_name for post in normals if post.topic]
		
		normal_topic_inits = PostTopicTestEntity.number_of_inits
		normal_parent_inits = UserTestEntity.number_of_inits
		
		#run prefetched case
		PostTopicTestEntity.number_of_inits = 0
		UserTestEntity.number_of_inits = 0
		
		normals = pfQuery.fetch(100)
		authors = [post.parent().name for post in normals]
		topics = [post.topic.topic_name for post in normals if post.topic]
	
		prefetched_topic_inits = PostTopicTestEntity.number_of_inits
		prefetched_parent_inits = UserTestEntity.number_of_inits
		
		#compared the two numbers. A 'worthwhile' prefetching query will init
		#fewer parents and topics
		self.assertTrue(prefetched_topic_inits < normal_topic_inits)
		self.assertTrue(prefetched_parent_inits < normal_parent_inits)
		
	def test_compatible_with_PagedQuery(self):
		
		from he3.db.tower.paging import PagedQuery
		pq = PagedQuery(self.prefetchingQuery, 2)
		post_page = pq.fetch_page(1)
		
	def util_create_posts_PrefetchingQuery(self):
		'''Creates a new PrefetchingQuery object of bills posts based on 
		a normal db.Query object'''
		return PrefetchingQuery(PostTestEntity.all().ancestor(self.bill)
								, (PostTestEntity.topic,'parent'))
	
	def util_create_posts_GQL_PrefetchingQuery(self):
		'''creates a new PrefetchingQuery object of bills posts using GQL'''
		gqlQuery = PostTestEntity.gql(
									'WHERE ANCESTOR IS :parent ORDER BY created DESC', 
									parent=self.bill)
		return PrefetchingQuery(gqlQuery)
	
	def util_create_test_post_data(self):
		'''creates a set of test data'''
		
		self.admin = SecurityRoleTestEntity(role_name = 'admin')
		self.admin.put()
		
		self.bill = UserTestEntity(name='bill', role=self.admin)
		self.bill.put()
		
		self.topic1 = PostTopicTestEntity(parent=self.bill, topic_name="topic1")
		self.topic1.put()
		
		self.topic2 = PostTopicTestEntity(parent=self.bill, topic_name="topic2")
		self.topic2.put()
		
		self.topic3 = PostTopicTestEntity(parent=self.bill, topic_name="topic3")
		self.topic3.put()
		
		self.post1 = PostTestEntity(parent=self.bill, title="no topic"
								, posted_on = date(2010,1,1))
		self.post1.put()
		
		self.post2 = PostTestEntity(parent=self.bill, title="about topic 1"
								, topic = self.topic1, posted_on = date(2010,2,1))
		self.post2.put()
		
		self.post3 = PostTestEntity(parent=self.bill, title="about topic 1 again"
								, topic = self.topic1, posted_on = date(2010,3,1))
		self.post3.put()
		
		self.post4 = PostTestEntity(parent=self.bill, title="about topic 2"
								, topic = self.topic2, posted_on = date(2010,4,1))
		self.post4.put()
		
	def util_log_post_titles(self, posts):
		logging.info([x.title for x in posts])

	def util_log_cursors(self,cursors):
		logging.info([x[:6] if x else None for x in cursors])
	
class SecurityRoleTestEntity(db.Model):
	''' this is an entity to be used for testing purposed that represents a 
	security role'''
	
	properties_to_prefetch =('parent',)
	
	role_name = db.StringProperty(required=True)	
	
class UserTestEntity(db.Model):
	'''This is an entity to be used for testing purposes. It is intended to be
	application agnostic'''
	
	number_of_inits = 0
	
	def __init__(self, parent=None, key_name=None, _app=None, _from_entity=False
				,**kwds):
		UserTestEntity.number_of_inits += 1
		db.Model.__init__(self, parent, key_name, _app,_from_entity, **kwds)	
	
	name = db.StringProperty(required=True)
	role = db.ReferenceProperty(required=True
							, reference_class=SecurityRoleTestEntity
							, collection_name='members')
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)

class PostTopicTestEntity(db.Model):
	'''This is an entity for testing purposes modelling a single topic to be
	applied to posts'''
	
	number_of_inits = 0
	
	def __init__(self, parent=None, key_name=None, _app=None, _from_entity=False
				,**kwds):
		PostTopicTestEntity.number_of_inits += 1
		db.Model.__init__(self, parent, key_name, _app,_from_entity, **kwds)
	
	topic_name = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)

class PostTestEntity(db.Model):
	'''This is an entity for testing purposes modeling a single post record
	'''
	title = db.StringProperty(required=True)
	topic = db.ReferenceProperty(required=False, reference_class=PostTopicTestEntity,
								collection_name='posts')
	posted_on = db.DateProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
