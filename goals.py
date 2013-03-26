import tornado.ioloop
import tornado.web
import os.path
import logging
import pymongo
import datetime

from tornado.options import define,options

define("port", default=8000, help="run on the given port", type=int)

#Globals
db = None
coll = None

class Application(tornado.web.Application):
  def __init__(self):
    handlers=[
      (r"/", MainHandler),
      (r"/add", NewGoalHandler),
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
    goals = coll.find({'title' : {'$exists':True}}) #title is required in goals.html
    print "found %s goals" % str(goals.count())
    
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
    })
    #print "Successfully added %s" % (str(insert_id))
    self.redirect("/")

if __name__ == "__main__":
  db = pymongo.Connection()['test']
  coll = db['test']['goals']
  
  app = Application()
  app.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()
