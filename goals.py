import tornado.ioloop
import tornado.web
import os.path
import logging
import pymongo
import datetime

from bson.objectid import ObjectId
from tornado.options import define,options

define("port", default=8000, help="run on the given port", type=int)

#Globals
db = None
coll = None
database_name = 'goals'
collection_name = 'goals'

#Notes
#Quick pymongo reference: http://www.youlikeprogramming.com/2010/12/python-and-mongodb-using-pymongo-quick-reference/

class Application(tornado.web.Application):
  def __init__(self):
    handlers=[
      (r"/([\w]*)", MainHandler),
      (r"/add/([\w]*)", AddHandler),
      (r"/delete/([\w]+)", DeleteHandler),
      (r"/activate/([\w]+)", ActivateHandler),
      (r"/deactivate/([\w]+)", DeactivateHandler),
      (r"/complete/([\w]*)", CompleteHandler),
    ]
    
    settings = dict(
      template_path = os.path.join(os.path.dirname(__file__), "templates"),
      static_path = os.path.join(os.path.dirname(__file__), "static"),
      debug = True,
    )
    tornado.web.Application.__init__(self,handlers,**settings)

class MainHandler(tornado.web.RequestHandler):
  def get(self,collection):
    if collection == "collections":
      self.write(str(get_collection_list()))
      return
    #goals is a cursor object
    print "collection: %s" % str(collection)
    if collection:
      goals_cursor = coll.find(
        {'$and': [
          {'title' : {'$exists':True}}, #title is required in goals.html
          {'deleted':0},
          {'done':0},
          {'collection': {'$exists':True}},
          {'collection': collection},
        ]}
      )
    else:
      #if no collection is specified in the url
      goals_cursor = coll.find(
        {'$and': [
          {'title' : {'$exists':True}}, #title is required in goals.html
          {'deleted':0},
          {'done':0},
          {'$or': [
            {'collection': {'$exists':False}},
            {'collection': collection},
          ]}
        ]}
      )
    print "found %s goals" % str(goals_cursor.count())
    
    #Build list of goals, active ones at the top
    goals = list()
    for goal in goals_cursor:
      if 'active' in goal and goal['active']:
        goals.insert(0,goal)
      else:
        goals.append(goal)
    print "goals list: %s" % goals
    self.render(
      "index.html",
      page_title = "Here's a page",
      collection = collection,
      header_text = "Goal List",
      footer_text = "Site by Matt Parlette",
      goals = goals,
    )

class AddHandler(tornado.web.RequestHandler):
  def post(self,collection):
    goal = self.get_argument('goal','')
    print str(goal)
    insert_id = coll.insert({
      'title': goal,
      'created': datetime.datetime.utcnow(),
      'done': 0,
      'deleted': 0,
      'active': 0,
      'collection': collection,
    })
    print "Successfully added %s" % (str(insert_id))
    self.redirect("/%s" % collection)

class DeleteHandler(tornado.web.RequestHandler):
  def post(self,id):
    print "deleting goal (id %s)" % str(id)
    coll.update(
      { #where
        '_id': ObjectId(id)
      },
      { #action
        '$set': {'deleted': 1},
      }
    )

class ActivateHandler(tornado.web.RequestHandler):
  def post(self,id):
    print "activating goal (id %s)" % str(id)
    coll.update(
      { #where
        '_id': ObjectId(id)
      },
      { #action
        '$set': {'active': 1},
      }
    )

class DeactivateHandler(tornado.web.RequestHandler):
  def post(self,id):
    print "deactivating goal (id %s)" % str(id)
    coll.update(
      { #where
        '_id': ObjectId(id)
      },
      { #action
        '$set': {'active': 0},
      }
    )

class CompleteHandler(tornado.web.RequestHandler):
  def post(self,id):
    #Get the complete argument, defaults to 1 (true)
    done = int(self.get_argument('complete',1,True))
    print "checked 'done' argument: %s" % str(done)
    print "toggling goal done status (id %s)" % str(id)
    coll.update(
      { #where
        '_id': ObjectId(id)
      },
      { #action
        '$set': {'done': done},
      }
    )

def get_collection_list():
  """Reply with a list of collections available for the user"""
  print "retrieving collections"
  
  #goals is a cursor object
  cursor = coll.find(
    {'collection':{'$exists':True}},
  )
  
  print "found %s goals" % str(cursor.count())
  
  #Build list of collections
  collections = list()
  for entry in cursor:
    if entry['collection'] not in collections:
      collections.append(entry['collection'])
  print "collections list: %s" % collections
  return tornado.escape.json_encode(collections)

if __name__ == "__main__":
  db = pymongo.Connection()[database_name]
  coll = db[database_name][collection_name]
  
  app = Application()
  app.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()
