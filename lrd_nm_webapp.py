import os, os.path
import cherrypy
import lrd_nm_func

cherrypy.config.update({'server.socket_host': "0.0.0.0",'server.socket_port': 80})

class Root(object):
	@cherrypy.expose
	def index(self):
		return open('webLCM.html')

if __name__ == '__main__':
	conf = {
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd())
		},
		'/basic_test': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'text/plain')],
		},
		'/definitions': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/wifi_status': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/connections': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/get_certificates': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/remove_connection': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/version': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/assets': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './assets'
		},
		'/plugins': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './plugins'
		}
	}

	webapp = Root()
	webapp.basic_test = lrd_nm_func.Basic_Type_test()
	webapp.definitions = lrd_nm_func.Definitions()
	webapp.wifi_status = lrd_nm_func.Wifi_Status()
	webapp.connections = lrd_nm_func.Connections()
	webapp.get_certificates = lrd_nm_func.Get_Certificates()
	webapp.remove_connection = lrd_nm_func.Remove_Connection()
	webapp.version = lrd_nm_func.Version()
	cherrypy.quickstart(webapp, '/', conf)

