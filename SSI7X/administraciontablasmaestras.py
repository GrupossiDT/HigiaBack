'''
Created on 02/05/2018

@author: EDISON.BEJARANO
'''

from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
from flask_restful import request, Resource
from wtforms import Form, validators, StringField , IntegerField
from ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport
import Static.labels as labels # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.opciones_higia as optns  # @UnresolvedImport
import Static.config_DB as dbConf # @UnresolvedImport
import Static.config as conf  # @UnresolvedImport
import time,json,jwt
import datetime

#Declaracion de variables globales
Utils = Utils()
lc_cnctn = ConnectDB()
fecha_act = time.ctime()

class AdministracionTablasMaestras(Resource):

    def post(self,**kwargs):
        if kwargs['page']=='UnidadesNegocio':
            return self.UnidadesNegocio()
        if kwargs['page']=='Sucursales':
            return self.Sucursales()
        if kwargs['page']=='Perfiles':
            return self.Perfiles()
        if kwargs['page']=='Genero':
            return self.Genero()
        if kwargs['page']=='Departamento':
            return self.Departamento()
        if kwargs['page']=='Municipios':
            return self.Municipios()
        if kwargs['page']=='Barrios':
            return self.Barrios()
        if kwargs['page']=='FormasPago':
            return self.FormasPago()
        if kwargs['page']=='CanalRecaudo':
            return self.CanalRecaudo()

    def UnidadesNegocio(self):
        ln_id_grpo_emprsrl = request.form["id_grpo_emprsrl"]

        strSql = " select id as id,nmbre_rzn_scl as dscrpcn"\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbunidades_negocio "\
                 " where "\
                 " id_grpo_emprsrl = "+str(ln_id_grpo_emprsrl)+""\
                 " and estdo = true "\
                 " order by nmbre_rzn_scl"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def Sucursales(self):
        ln_id_undd_ngco = request.form["id_undd_ngco"]
        strSql = " select id as id,nmbre_scrsl as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbsucursales "\
                 " where "\
                 " id_undd_ngco = "+str(ln_id_undd_ngco)+""\
                 " and estdo = true "\
                 " order by nmbre_scrsl"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def Perfiles(self):
        ln_id_undd_ngco = request.form["id_undd_ngco"]

        strSql = " select a.id as id, trim(b.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbperfiles_une as a "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbperfiles as b"\
                 " on a.id_prfl=b.id "\
                 " where "\
                 " a.id_undd_ngco = "+str(ln_id_undd_ngco)+""\
                 " and a.estdo= true and b.estdo= true "\
                 " order by trim(b.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def Genero(self):
        ln_id_grpo_emprsrl = request.form["id_grpo_emprsrl"]

        strSql = " select a.id , trim(b.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbsexos_ge as a "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbsexos as b"\
                 " on a.id_sxo = b.id "\
                 " where "\
                 " a.id_grpo_emprsrl = "+str(ln_id_grpo_emprsrl)+""\
                 " and a.estdo= true and b.estdo= true "\
                 " order by trim(b.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)


    def Departamento(self):
        ln_id_ps_ge = request.form["id_ps_ge"]

        strSql = " select a.id,trim(b.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbdepartamentos_ge as a "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbdepartamentos as b"\
                 " on a.id_dprtmnto = b.id "\
                 " where "\
                 " a.id_ps_ge = "+str(ln_id_ps_ge)+""\
                 " and a.estdo= true and b.estdo= true "\
                 " order by trim(b.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def Municipios(self):
        ln_id_dprtmnto_ge = request.form["id_dprtmnto_ge"]

        strSql = " select a.id,trim(b.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbmunicipios_ge as a "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbmunicipios as b"\
                 " on a.id_mncpo = b.id "\
                 " where "\
                 " a.id_dprtmnto_ge = "+str(ln_id_dprtmnto_ge)+""\
                 " and a.estdo= true and b.estdo= true "\
                 " order by trim(b.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def Barrios(self):
        ln_id_mncpo_ge = request.form["id_mncpo_ge"]

        strSql = " select a.id,trim(b.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbbarrios_ge as a "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbbarrios as b"\
                 " on a.id_brro = b.id "\
                 " where "\
                 " a.id_mncpo_ge = "+str(ln_id_mncpo_ge)+""\
                 " and a.estdo= true and b.estdo= true "\
                 " order by trim(b.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def FormasPago(self):
        ln_id_undd_ngco = request.form["id_undd_ngco"]

        strSql = " select frms_pgo_une.id,trim(frms_pgo.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbformas_pago_une as frms_pgo_une  "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbformas_pago as frms_pgo "\
                 " on frms_pgo_une.id_frma_pgo = frms_pgo.id "\
                 " where frms_pgo_une.id_undd_ngco =  "+str(ln_id_undd_ngco)+""\
                 " and frms_pgo_une.estdo = true and frms_pgo.estdo = true "\
                 " order by trim(frms_pgo.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def CanalRecaudo(self):
        ln_id_undd_ngco = request.form["id_undd_ngco"]

        strSql = " select cnls_rcdo_une.id,trim(cnls_rcdo.dscrpcn) as dscrpcn "\
                 " from "\
                 " "+str(dbConf.DB_SHMA)+".tbcanales_recaudo_une as cnls_rcdo_une  "\
                 " Inner Join "+str(dbConf.DB_SHMA)+".tbcanales_recaudo as cnls_rcdo"\
                 " on cnls_rcdo_une.id_cnl_rcdo = cnls_rcdo.id "\
                 " where cnls_rcdo_une.id_undd_ngco = "+str(ln_id_undd_ngco)+""\
                 " and cnls_rcdo.estdo = true and cnls_rcdo_une.estdo = true "\
                 "order by trim(cnls_rcdo.dscrpcn)"

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)
