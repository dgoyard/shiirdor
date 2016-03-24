##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import collections
import base64
import re
import json

# CubicWeb import
from cubicweb import tags
from cubicweb.view import StartupView
from cubicweb.web.views.tableview import EntityTableView
from cubicweb.web.views.tableview import EntityTableColRenderer
from cubicweb.web.views.tableview import MainEntityColRenderer
from cubicweb.predicates import match_user_groups
from cubicweb.predicates import is_instance
from cubicweb.web.views import add_etype_button
from cubicweb.web.views.ajaxcontroller import ajaxfunc
from cubicweb.web.views.reledit import reledit_form as cw_reledit_form
from cubicweb.web.views.reledit import AutoClickAndEditFormView
from logilab.common.decorators import monkeypatch

# Cubes import
from .predicates import trust_authenticated
from cubes.schiirdor.ldapfeed import LDAPConnection
from cubes.trustedauth.cryptutils import build_cypher


class SCHIIRDORSyncManagementView(StartupView):
    """ Synchronize users and groups to the 'SCHIIRDOR_DESTINATION' ldap based
    resource.
    """
    __regid__ = "schiirdor.sync-management"
    __select__ = (StartupView.__select__ &
                  match_user_groups("managers", "moderators"))
    title = _("Synchronize Users & Groups")
    cache_max_age = 0 # disable caching
    rql = ("Any F, S, UAA, L, USN, GN WHERE U is CWUser, "
           "U login L, NOT U login IN ('anon', 'admin'), U in_group G, "
           "NOT G name IN ('managers', 'users', 'guests', 'moderators'), "
           "G name GN, U firstname F, U surname S, U in_state US, "
           "US name USN, U primary_email UA?, UA address UAA")
    src_name = "SCHIIRDOR_DESTINATION"
    src_rql = ("Any X, T, U, C Where X is CWSource, X name 'SCHIIRDOR_DESTINATION', "
               "X type T, X url U, X config C")

    def call(self, **kwargs):
        """ Start synchronisation with destination source: users and associated
        groups.
        """
        # Create a connection to the ldap resource
        cyphr = build_cypher(self._cw.vreg.config._secret)
        login = cyphr.decrypt(
            base64.decodestring(self._cw.vreg.dest_authlogin)).strip()
        password = cyphr.decrypt(
            base64.decodestring(self._cw.vreg.dest_authpassword)).strip()
        with self._cw.session.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.src_rql)
        if rset.rowcount != 1:
            raise Exception("No resource attached to this RQL: "
                            "{0}.".format(self.src_rql))
        seid, stype, surl, sconfig = rset[0]
        if stype != "ldapfeed":
            raise Exception("Source '{0}' must be of 'ldapfeed' "
                            "type.".format(self.src_name))
        connection = LDAPConnection(seid, self.src_name, stype, surl, sconfig,
                                    login, password)    

        # Display title
        self.w(u"<h1>{0}</h1>".format(self.title))
        self.w(u"</br>")

        # Extract managed users and synchronized
        rset = self._cw.execute(self.rql)
        errors = []
        syncs = []
        users = []
        for firstname, surname, mail, login, status, group in rset.rows:
            if status == "activated":
            
                # Create/get tyhe group
                grp = connection.is_valid_group(group, filter_attributes=True)
                if grp is None:
                    connection.create_group(group)
                    grp = connection.is_valid_group(group,
                                                    filter_attributes=True)

                # Get the group members
                members = grp.get("members", [])
                if not isinstance(members, list):
                    members = [members]

                # Create/get the user
                user = connection.is_valid_login(login)
                if user is None:
                    secret = cyphr.encrypt("%128s" % login)
                    connection.create_user(login, secret, firstname,
                                           surname)

                # Update the group members if necessary               
                if login not in members:
                    connection.add_user_in_group(group, login)
                    syncs.append("{0} ({1})".format(login, group))
                else:
                    users.append("{0} ({1})".format(login, group))
            else:
                errors.append(login)

        # Close connection
        connection.close()
        
        # Display goodbye message
        if len(syncs) == 0:
            syncs.append("No data.")
        if len(errors) == 0:
            errors.append("No data.")
        if len(users) == 0:
            users.append("No data.")
        self.w(u"<h3>Newly synchronized users</h3>")
        self.w(u"{0}".format("-".join(syncs)))
        self.w(u"<h3>Existing users in destination LDAP</h3>")
        self.w(u"{0}".format("-".join(users)))
        self.w(u"<h3>Desactivated users</h3>")
        self.w(u"{0}".format("-".join(errors)))


class SCHIIRDORUserManagementView(StartupView):
    """ Manage user associated groups.
    """
    __regid__ = "schiirdor.users-management"
    __select__ = (StartupView.__select__ &
                  match_user_groups("managers", "moderators"))
    title = _("Manage User associated Groups")
    cache_max_age = 0 # disable caching
    rql = ("Any U,US,F,S,U,UAA,UDS, L,UAA,USN,UDSN ORDERBY L WHERE "
           "U is CWUser, U login L, NOT U login IN ('anon', 'admin'), "
           "U firstname F, U surname S, U in_state US, US name USN, "
           "U primary_email UA?, UA address UAA, "
           "U cw_source UDS, US name UDSN")

    def call(self, **kwargs):
        self.w(u"<h1>{0}</h1>".format(self.title))
        rset = self._cw.execute(self.rql)
        if rset.rowcount > 0:
            self.wview("schiirdor.users-table", rset)
        else:
            self.w(u"No user to manage.".format(self.title))


@monkeypatch(AutoClickAndEditFormView)
def _compute_formid_value(self, rschema, role, rvid, formid):
    """  Filter the user associed groups that will be displayed in the edit view.
    """
    if (self.entity.__class__.__name__ == "CWUser" and rschema == "in_group"
            and "managers" not in [grp.name for grp in self._cw.user.in_group]):
        restriction = tuple(self._cw.vreg.config["restricted-groups"])
        related_rset = self._cw.session.execute(
            "Any G Where U eid '{0}', U in_group G, NOT G name IN {1}".format(
                self.entity.eid, repr(restriction)))
    else:
        related_rset = self.entity.related(rschema.type, role)
    if related_rset:
        value = self._cw.view(rvid, related_rset)
    else:
        value = self._compute_default_value(rschema, role)
    if not self._should_edit_relation(rschema, role):
        return None, value
    return formid, value


@ajaxfunc(output_type="xhtml")
def reledit_form(self):
    """ Filter the groups that will be displayed in the edit view.
    """
    req = self._cw
    args = dict((x, req.form[x])
                for x in ('formid', 'rtype', 'role', 'reload', 'action'))
    rset = req.eid_rset(int(self._cw.form['eid']))
    try:
        args['reload'] = json.loads(args['reload'])
    except ValueError: # not true/false, an absolute url
        assert args['reload'].startswith('http')
    view = req.vreg['views'].select('reledit', req, rset=rset, rtype=args['rtype'])

    html = self._call_view(view, **args)
    if "managers" not in [grp.name for grp in self._cw.user.in_group]:
        for name in req.vreg.config["restricted-groups"]:
            regex = '<option value="[0-9]*">{1}.*</option>'.format(
                self._cw.form['eid'], name)
            html = re.sub(regex, "", html)
    
    return html


class SCHIIRDORUsersTable(EntityTableView):
    """ Display a table with the user information to be managed.
    """
    __regid__ = "schiirdor.users-table"
    __select__ = (is_instance("CWUser") &
                  match_user_groups("managers", "moderators"))
    columns = ["user", "in_state", "firstname", "surname",
               "in_group", "primary_email", "cw_source"]
    finalvid = "editable-final"

    column_renderers = {
        "user": EntityTableColRenderer(
            renderfunc=lambda w,x: w(x.login),
            sortfunc=lambda x: x.login),
        "in_state": EntityTableColRenderer(
            renderfunc=lambda w,x: w(
                x.cw_adapt_to("IWorkflowable").printable_state),
            sortfunc=lambda x: x.cw_adapt_to(
                "IWorkflowable").printable_state),
        "in_group": EntityTableColRenderer(
            renderfunc=lambda w,x: x.view(
                "reledit", rtype="in_group", role="subject", w=w)),
        "primary_email": EntityTableColRenderer(
            renderfunc=lambda w,x: w(x.primary_email and x.primary_email[0].display_address() or u""),
            sortfunc=lambda x: x.primary_email and x.primary_email[0].display_address() or u""),
        "cw_source": EntityTableColRenderer(
            renderfunc=lambda w,x: w(x.cw_source[0].name),
            sortfunc=lambda x: x.cw_source[0].name)
    }


class SCHIIRDORGroupsManagementView(StartupView):
    """ Manage groups.
    """
    __regid__ = "shiirdor.groups-management"
    title = _("Manage Groups")
    __select__ = StartupView.__select__ & match_user_groups("managers")
    cache_max_age = 0 # disable caching
    rql = ("Any G,GN ORDERBY GN WHERE G is CWGroup, G name GN, NOT G "
           "name 'owners'")

    def call(self, **kwargs):
        self.w(u"<h1>{0}</h1>".format(self.title))
        self.w(add_etype_button(self._cw, "CWGroup"))
        self.w(u"<div class='clear'></div>")
        self.wview('shiirdor.groups-table', self._cw.execute(self.rql))


class SCHIIRDORImportView(StartupView):
    """ Import users and groups from the 'SCHIIRDOR_DESTINATION' ldap resource.

    This mechanism can be used as a backup system in case the database is
    corrupted.
    """
    __regid__ = "shiirdor.users-groups-import"
    title = _("Import Users&Groups")
    __select__ = StartupView.__select__ & match_user_groups("managers")
    cache_max_age = 0 # disable caching
    src_name = "SCHIIRDOR_DESTINATION"
    src_rql = ("Any X, T, U, C Where X is CWSource, X name 'SCHIIRDOR_DESTINATION', "
               "X type T, X url U, X config C")

    def call(self, **kwargs):
        # Display a title
        self.w(u"<h1>{0}</h1>".format(self.title))

        # Create a connection to the ldap resource
        cyphr = build_cypher(self._cw.vreg.config._secret)
        login = cyphr.decrypt(
            base64.decodestring(self._cw.vreg.dest_authlogin)).strip()
        password = cyphr.decrypt(
            base64.decodestring(self._cw.vreg.dest_authpassword)).strip()
        with self._cw.session.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.src_rql)
        if rset.rowcount != 1:
            raise Exception("No resource attached to this RQL: "
                            "{0}.".format(self.src_rql))
        seid, stype, surl, sconfig = rset[0]
        if stype != "ldapfeed":
            raise Exception("Source '{0}' must be of 'ldapfeed' "
                            "type.".format(self.src_name))
        connection = LDAPConnection(seid, self.src_name, stype, surl, sconfig,
                                    login, password)

        # Create missing users and groups entities and in_group relation.
        groups_data, users_data = connection.dump_users_and_groups()
        with self._cw.session.repo.internal_cnx() as cnx:
            for user_info in users_data:
                req = "Any X WHERE X is CWUser, X login '{0}'".format(
                    user_info["login"])
                rset = cnx.execute(req)
                if rset.rowcount == 0:
                    print("Creating user '{0}'...".format(user_info["login"]))
                    req = "INSERT CWUser X: "
                    for attribute, value in user_info.items():
                        req += " X %(attribute)s '%(value)s'," % {
                            "attribute": attribute, "value": value}
                    req += "X in_group G WHERE G name 'users'"
                    rset = cnx.execute(req)
            for group_info in groups_data:
                grpname = group_info["name"]
                req = "Any X WHERE X is CWGroup, X name '{0}'".format(grpname)
                rset = cnx.execute(req)
                if rset.rowcount == 0:
                    print("Creating group '{0}'...".format(grpname))
                    req = "INSERT CWGroup X: X name '{0}'".format(grpname)
                    rset = cnx.execute(req)
                members = group_info.get("members", [])
                if not isinstance(members, list):
                    members = [members]
                for login in members:
                    req = ("Any X WHERE X is CWUser, X login '{0}', "
                           "X in_group G, G name '{1}'".format(login, grpname))
                    rset = cnx.execute(req) 
                    if rset.rowcount == 0:
                        print("Adding relation '{0}' in_group '{1}'...".format(
                            login, grpname))
                        req = ("SET X in_group G WHERE X is CWUser, "
                               "X login '{0}', G is CWGroup, "
                               "G name '{1}'".format(login, grpname))
                        rset = cnx.execute(req)
            cnx.commit()

        # Close connection
        connection.close()


class SCHIIRDORGroupsTable(EntityTableView):
    """ Display a table with the groups information to be managed.
    """
    __regid__ = "shiirdor.groups-table"
    __select__ = is_instance("CWGroup") & match_user_groups("managers")
    columns = ["group", "nb_users"]

    column_renderers = {
        "group": MainEntityColRenderer(),
        "nb_users": EntityTableColRenderer(
            header=_('num. users'),
            renderfunc=lambda w,x: w(unicode(x.num_users())),
            sortfunc=lambda x: x.num_users()),
    }


class SCHIIRDORAdminUsersManagementView(StartupView):
    """ Manage users.
    """
    __regid__ = "shiirdor.admin-users-management"
    title = _("Manage Users")
    __select__ = StartupView.__select__ & match_user_groups("managers")
    cache_max_age = 0 # disable caching
    rql = ("Any U,UL ORDERBY UL WHERE U is CWUser, U login UL, NOT U "
           "login 'admin'")

    def call(self, **kwargs):
        self.w(u"<h1>{0}</h1>".format(self.title))
        self.w(add_etype_button(self._cw, "CWUser"))
        self.w(u"<div class='clear'></div>")
        self.wview('shiirdor.admin-users-table2', self._cw.execute(self.rql))


class SCHIIRDORAdminUsersTable(EntityTableView):
    """ Display a table with the users information to be managed.
    """
    __regid__ = "shiirdor.admin-users-table"
    __select__ = is_instance("CWUser") & match_user_groups("managers")
    columns = ["user"]

    column_renderers = {
        "user": MainEntityColRenderer(),
    }


def registration_callback(vreg):
    
    for klass in [SCHIIRDORSyncManagementView, SCHIIRDORUserManagementView,
                  SCHIIRDORUsersTable, SCHIIRDORGroupsManagementView,
                  SCHIIRDORImportView, SCHIIRDORGroupsTable,
                  SCHIIRDORAdminUsersManagementView, SCHIIRDORAdminUsersTable]:
        vreg.register(klass)
    vreg.register_and_replace(reledit_form, cw_reledit_form)
