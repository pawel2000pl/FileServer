import configuration
import installation
import cherrypy
import server
import models


if __name__ == "__main__":
    models.auto_update()
    installation.install_admin()
    
    cherrypy.config.update(configuration.CP_CONFIG_PATH+'global.cnf')
    cherrypy.tree.mount(server.Server(), '/')

    cherrypy.engine.start()
    cherrypy.engine.block()


