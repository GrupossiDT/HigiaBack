'''
Created on 22/01/2018

@author: ROBIN.VALENCIA,EDISON.BEJARANO

Clase para la gestion de usuarios del sistema
'''
from _codecs import decode

from flask_restful import Resource
import jwt, json  # @UnresolvedImport

from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
import Static.config as conf  # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.config_DB as confDB # @UnresolvedImport

# clase para manejo de permisos por usuario menu
class ValidacionSeguridad(Resource):
    Utils = Utils()
    C = ConnectDB()

    def Principal(self, key, id_mnu_ge, sttc_mnu):
        if not key and id_mnu_ge:
            return False
        DatosUsuario =  self.ValidacionToken(key)
        if DatosUsuario:
            if int(sttc_mnu) == int(id_mnu_ge):
                lo_datos = self.validaUsuario(DatosUsuario['lgn'])
                return self.ValidaOpcionMenu(lo_datos['id_prfl_scrsl'], id_mnu_ge)
            else:
                return False
        else:
            False

    def validaUsuario(self, usuario):
        IdUsuarioGe = json.loads(json.dumps(self.ObtenerDatosUsuario(usuario)[0], indent=2))
        strQuery = "SELECT "\
                    " a.id as id_prfl_scrsl,"\
                    " b.nmbre_scrsl as nmbre_scrsl,"\
                    " c.estdo as estdo ,"\
                    " b.id as id_scrsl "\
                    " FROM "+confDB.DB_SHMA+".tblogins_perfiles_sucursales a"\
                    " left JOIN  "+confDB.DB_SHMA+".tbsucursales b on a.id_scrsl=b.id"\
                    " left join "+confDB.DB_SHMA+".tblogins_ge c on c.id = a.id_lgn_ge"\
                    " WHERE  a.id_lgn_ge = " + str(IdUsuarioGe['id_lgn_ge']) + " and a.mrca_scrsl_dfcto is true"
        Cursor = self.C.queryFree(strQuery)

        if Cursor :
            data = json.loads(json.dumps(Cursor[0], indent=2))
            if data['estdo']:
                return data
            else:
                return errors.ERR_NO_USRO_INCTVO
        else:
            return errors.ERR_NO_TNE_PRFL

    def ValidacionToken(self, key):
        try:
            token = self.C.querySelect(confDB.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
            decode = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
            return decode
        except jwt.exceptions.ExpiredSignatureError:
            return  None

    def ValidaOpcionMenu(self, id_lgn_prfl_scrsl, id_mnu_ge):
            Cursor = self.C.queryFree(" select a.id "\
                                 " from "+confDB.DB_SHMA+".tblogins_perfiles_menu a inner join "\
                                     " "+confDB.DB_SHMA+".tblogins_perfiles_sucursales b "\
                                     " on a.id_lgn_prfl_scrsl = b.id inner join "\
                                     " "+confDB.DB_SHMA+".tblogins_ge c on c.id = b.id_lgn_ge inner join "\
                                     " "+confDB.DB_SHMA+".tbmenu_ge d on d.id = a.id_mnu_ge inner join "\
                                     " "+confDB.DB_SHMA+".tbmenu e on e.id = d.id_mnu "\
                                     " where c.estdo=true "\
                                     " and b.estdo=true "\
                                     " and a.estdo=true "\
                                     " and d.id = " + str(id_mnu_ge) + " and a.id_lgn_prfl_scrsl = " + str(id_lgn_prfl_scrsl))
            if Cursor:
                return True
            else:
                return False

    def ObtenerDatosUsuario(self, usuario):
        cursor = self.C.queryFree(" select "\
                             " case when emplds_une.id is not null then "\
                             " concat_ws("\
                             " ' ',"\
                             " emplds.prmr_nmbre,"\
                             " emplds.sgndo_nmbre,"\
                             " emplds.prmr_aplldo,"\
                             " emplds.sgndo_aplldo)"\
                             " else"\
                             " prstdr.nmbre_rzn_scl"\
                             " end as nmbre_cmplto,"\
                             " case when emplds_une.id is not null then"\
                             " emplds.crro_elctrnco"\
                             " else" \
                             " prstdr.crro_elctrnco"\
                             " end as crro_elctrnco,"\
                             " lgn_ge.id as id_lgn_ge, "\
                             " lgn.lgn as lgn, "\
                             " crgo.dscrpcn as crgo, "\
                             " lgn.fto_usro as fto_usro, "\
                             "(Case when emplds_une.id_undd_ngco is null THEN "\
                             "prfl_une.id_undd_ngco "\
                             " ELSE "\
                             " emplds_une.id_undd_ngco "\
                               " END "\
                             " ) as id_undd_ngco,"\
                             " lgn_ge.id_grpo_emprsrl as id_grpo_emprsrl, "
                             " lgn_ge.cmbo_cntrsna as cmbo_cntrsna "
                             " from "+confDB.DB_SHMA+".tblogins_ge lgn_ge " \
                             " left join "+confDB.DB_SHMA+".tblogins lgn on lgn.id = lgn_ge.id_lgn " \
                             " left join "+confDB.DB_SHMA+".tbempleados_une emplds_une on emplds_une.id_lgn_accso_ge = lgn_ge.id " \
                             " left join "+confDB.DB_SHMA+".tbempleados emplds on emplds.id = emplds_une.id_empldo " \
                             " left join "+confDB.DB_SHMA+".tbprestadores prstdr on prstdr.id_lgn_accso_ge = lgn_ge.id " \
                             " left join "+confDB.DB_SHMA+".tbcargos_une crgo_une on crgo_une.id = emplds_une.id_crgo_une " \
                             " left join "+confDB.DB_SHMA+".tbcargos crgo on crgo.id = crgo_une.id_crgo " \
                             " left join "+confDB.DB_SHMA+".tbunidades_negocio undd_ngco on undd_ngco.id = emplds_une.id_undd_ngco " \
                             " inner join "+confDB.DB_SHMA+".tblogins_perfiles_sucursales as prfl_scrsls on prfl_scrsls.id_lgn_ge = lgn_ge.id and prfl_scrsls.mrca_scrsl_dfcto is true "\
                             " inner join "+confDB.DB_SHMA+".tbperfiles_une as prfl_une on prfl_une.id = prfl_scrsls.id_prfl_une "\
                             " where lgn.lgn = '" + usuario + "' and id_mtvo_rtro_une is null")
        return cursor
