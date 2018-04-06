from flask_restful import  Resource
class Contratos(Resource):

    def post(self,**kwargs):

        if kwargs['page']=='crear':
            return self.crear()
        if kwargs['page']=='listar':
            return self.listar()
        if kwargs['page']=='actualizar':
            return self.actualizar()
     

    def crear(self):
            
        #ln_opcn_mnu = request.form["id_mnu_ge"]
        #ln_id_undd_ngco = request.form["id_undd_ngco"]
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad()
        print('crear')
   
    def actualizar(self):   
        
        #ln_opcn_mnu = request.form["id_mnu_ge"]
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad() 
        print('actualizar')
    
    def listar(self):   
        
        #ln_opcn_mnu = request.form["id_mnu_ge"]
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad() 
        print('listar')