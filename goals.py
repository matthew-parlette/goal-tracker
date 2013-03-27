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

#Notes
#Quick pymongo reference: http://www.youlikeprogramming.com/2010/12/python-and-mongodb-using-pymongo-quick-reference/

class Application(tornado.web.Application):
  def __init__(self):
    handlers=[
      (r"/", MainHandler),
      (r"/add", NewGoalHandler),
      (r"/delete/([\w]+)", DeleteGoalHandler),
      (r"/activate/([\w]+)", ActivateHandler),
      #(r"/deactivate/([\w]+)", DeactivateHandler),
    ]
    
    settings = dict(
      template_path = os.path.join(os.path.dirname(__file__), "templates"),
      static_path = os.path.join(os.path.dirname(__file__), "static"),
      debug = True,
    )
    tornado.web.Application.__init__(self,handlers,**settings)

class MainHandler(tornado.web.RequestHandler):
  def get(self):
    #goals is a cursor object
    goals_cursor = coll.find({'title' : {'$exists':True}},{'deleted':0}) #title is required in goals.html
    print "found %s goals" % str(goals_cursor.count())
    
    #Build list of goals, active ones at the top
    goals = list()
    for goal in goals_cursor:
      if 'active' in goal and goal['active']:
        goals.insert(0,goal)
      else:
        goals.append(goal)
    
    self.render(
      "index.html",
      page_title = "Here's a page",
      header_text = "Goal List",
      footer_text = "footer",
      goals = goals,
    )

class NewGoalHandler(tornado.web.RequestHandler):
  def post(self):
    goal = self.get_argument('goal','')
    print str(goal)
    insert_id = coll.insert({
      'title': goal,
      'created': datetime.datetime.utcnow(),
      'done': 0,
      'deleted': 0,
      'active': 0,
    })
    print "Successfully added %s" % (str(insert_id))
    self.redirect("/")

class DeleteGoalHandler(tornado.web.RequestHandler):
  def post(self,id):
    print "deleting goal (id %s)" % str(id)
    coll.update(
      { #where
        '_id': ObjectId(id)
      },
      { #action
        '$set': {'deleted': '1'},
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
        '$set': {'active': '1'},
      }
    )

if __name__ == "__main__":
  db = pymongo.Connection()['test']
  coll = db['test']['goals']
  
  app = Application()
  app.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()
