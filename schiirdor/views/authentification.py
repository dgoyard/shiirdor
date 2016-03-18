##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import base64

# CubicWeb import
from cubicweb import AuthenticationError
from cubicweb.web.views import authentication, actions, basecontrollers
from cubicweb.web.views.authentication import LoginPasswordRetriever

# Cubes import
from cubes.schiirdor.ldapfeed import LDAPConnection
from cubes.trustedauth.cryptutils import build_cypher


class SSOUserRetriever(authentication.WebAuthInfoRetreiver):
    """ Single sign-on (SSO) access control of multiple related, but
    independent software systems. With this property a user logs in with a
    single ID and password to gain access to a connected system or systems
    without using different usernames or passwords.

    Special login: 'admin'.
    Special group: 'moderators'.
    """
    __regid__ = "sso-user-retriever"
    order = 0
    auth_rql = ("Any X WHERE X is CWUser, X login %(login)s")
    trusted_rql = ("Any X WHERE X is CWUser, X login %(login)s, "
                   "X in_group G, G name 'moderators'")
    src_name = "SCHIIRDOR_SOURCE"
    src_rql = ("Any X, T, U, C Where X is CWSource, X name 'SCHIIRDOR_SOURCE', "
               "X type T, X url U, X config C")

    def authentication_information(self, req):
        """ Retrieve authentication information from the given request, raise
        NoAuthInfo if expected information is not found, return login crypted
        with secret shared key.
        """
        self.debug("web authenticator building auth info")
        login, password = req.get_authorization()
        if not login:
            raise authentication.NoAuthInfo()
        cyphr = build_cypher(self._cw.config._secret)
        if login != "admin":
            secret = base64.encodestring(cyphr.encrypt("%128s" % login))
            return login, {"password": secret, "secret": password}
        else:
            return login, {"password": password}

    def authenticated(self, retriever, req, session, login, authinfo):
        """ Callback when return authentication information have opened a
        repository connection successfully. Take care req has no session
        attached yet, hence req.execute isn't available.

        Here we set a flag on the request to indicate that the user is
        _only_ kerberos authenticated (since cookie login can kick in
        if needed)
        """
        # Nothing to do for admin login
        if login == "admin":
            return
        self.debug("Web authenticator running post authentication callback.")
        # If the login is not in the CW registration instance
        with session.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.auth_rql, {"login": login})
        #if rset.rowcount != 1:
            #raise AuthenticationError()
        # 2003 Active Directory allows anonymous binds. So not providing a
        # user id at all will still pass a simple bind check, if the only
        # thing being tested is whether simple_bind_s() throws an error.
        # 2003 Active Directory does require authentication for any searches
        # that aren't attributes of the rootDSE.
        with session.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.src_rql)
        if rset.rowcount != 1:
            raise Exception("No resource attached to this RQL: "
                            "{0}.".format(self.src_rql))
        seid, stype, surl, sconfig = rset[0]
        try:
            connection = LDAPConnection(seid, self.src_name, stype, surl,
                                        sconfig, login, authinfo["secret"])
            user_info = connection.is_valid_login(login,
                                                  filter_attributes=True)
            connection.close()
        except:
            raise AuthenticationError()
        # Add a flag for remote user
        with session.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.trusted_rql, {"login": login})
        if rset.rowcount == 0:
            if "secret" not in authinfo:
                raise AuthenticationError()
            setattr(session, "trusted_cwuser", True)

    def request_has_auth_info(self, req):
        return req.get_authorization()[0] is not None

    def revalidate_login(self, req):
        return req.get_authorization()[0]


def registration_callback(vreg):
    vreg.register(SSOUserRetriever)
    vreg.unregister(LoginPasswordRetriever)
