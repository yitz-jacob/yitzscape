import cgi
import wsgiref.handlers
import os
import logging
from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class HomePage(db.Model):
	content = db.TextProperty()
	author = db.StringProperty(multiline=False)
	lastmod = db.DateTimeProperty(auto_now_add=True)
	name = db.StringProperty(multiline=False)
	public = db.BooleanProperty()
	
class doList(webapp.RequestHandler):
	def get(self):
		pageq = db.GqlQuery("SELECT * FROM HomePage")

		pages = pageq.fetch(100)
		
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'pages': pages,
			'url': url,
			'url_linktext': url_linktext,
		}

		path = os.path.join(os.path.dirname(__file__), 'list.html')
		self.response.out.write(template.render(path, template_values))
	
class MainPage(webapp.RequestHandler):
	def get(self):
		handlePage(self,'home')
		
class doPage(webapp.RequestHandler):
	def get(self,id):
		handlePage(self,id)

class doLogin(webapp.RequestHandler):
	def get(self):
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'url': url,
			'url_linktext': url_linktext,
		}

		path = os.path.join(os.path.dirname(__file__), 'login.html')
		self.response.out.write(template.render(path, template_values))

class doEdit(webapp.RequestHandler):
	def get(self,page):
		if len(page) > 0:
			pageName = page
		else:
			pageName = 'home'

		homepages = db.GqlQuery("SELECT * FROM HomePage WHERE name = :1",
				pageName)
		if homepages.count(1) > 0:
			homepage = homepages.fetch(1)[0]
		else:
			homepage = HomePage(content='New page..')

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'page': homepage,
			'url': url,
			'url_linktext': url_linktext,
			'pageName':pageName,
		}
	
		if users.is_current_user_admin():
			path = os.path.join(os.path.dirname(__file__), 'edit.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))

	def post(self,page):
		if users.is_current_user_admin():
			if len(page) > 0:
				pageName = page
			else:
				pageName = 'home'

			homepages = db.GqlQuery("SELECT * FROM HomePage WHERE name = :1",
				pageName)
			if homepages.count(1) > 0:
				homepage = homepages.fetch(1)[0]
			else:
				homepage = HomePage()

			if users.get_current_user():
				homepage.author = users.get_current_user().nickname()


			if len(self.request.get('con')) > 0:
				homepage.name = pageName
				homepage.content = self.request.get('con')
				latestTime = datetime.now()
				homepage.lastmod = latestTime
				homepage.put()
				if pageName == 'home':
					self.redirect('/')
				else:
					self.redirect('/'+pageName)
			else:
				if users.get_current_user():
					url = users.create_logout_url(self.request.uri)
					url_linktext = 'Logout'
				else:
					url = users.create_login_url(self.request.uri)
					url_linktext = 'Login'

				template_values = {
					'page': homepage,
					'url': url,
					'url_linktext': url_linktext,
				}

				path = os.path.join(os.path.dirname(__file__), 'edit.html')
				self.response.out.write(template.render(path, template_values))
		else:
			self.response.out.write('forebidden');

def handlePage(handler, page):
	if len(page) > 0:
		pageName = page
	else:
		pageName = 'home'

	homepages = db.GqlQuery("SELECT * FROM HomePage WHERE name = :1",
			pageName)

	if homepages.count(1) > 0:
		homepage = homepages.fetch(1)[0]
	else:
		homepage = HomePage(content='page does not exist')

	if users.get_current_user():
		url = users.create_logout_url(handler.request.uri)
		url_linktext = 'Logout'
	else:
		url = users.create_login_url(handler.request.uri)
		url_linktext = 'Login'

	template_values = {
		'page': homepage,
		'url': url,
		'url_linktext': url_linktext,
	}

	path = os.path.join(os.path.dirname(__file__), 'index.html')
	handler.response.out.write(template.render(path, template_values))

	
def main():
	application = webapp.WSGIApplication(
                                       [('/', MainPage),
                                        ('/page/([\w0-9_\-\.]+)/edit', doEdit),
                                        ('/login',doLogin),
                                        ('/list',doList),
                                        ('/page/([\w0-9_\-\.]+)', doPage),
                                        ('/([\w0-9_\-\.]+)/edit', doEdit),
                                        ('/([\w0-9_\-\.]+)', doPage)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
	main()