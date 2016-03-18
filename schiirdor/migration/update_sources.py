##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Configure sources
_DESTINATION_LDAP_CONFIGURATION_DETAILS = {
    "synchronize": "no",
    "synchronization-interval": "30min",
    "data-cnx-dn": u"cn={0},dc=intra,dc=cea,dc=fr",
    "data-cnx-password": u"",
    "user-base-dn": u"ou=Users,dc=intra,dc=cea,dc=fr",
    "user-attrs-map": (u"userPassword:upassword,mail:mail,uid:login,"
                       "givenName:firstname,sn:surname"),
    "group-base-dn": u"ou=Groups,dc=intra,dc=cea,dc=fr",
    "group-attrs-map": u"memberUid:members,cn:name,gidNumber:gid",
    "user-scope": "SUBTREE",
    "user-classes": "inetOrgPerson",
    "user-login-attr": "uid",
    "user-default-group": "",
    "group-scope": "SUBTREE",
    "group-classes": "posixGroup",
    "group-filter": "(cn={0})",
}
_SOURCE_LDAP_CONFIGURATION_DETAILS = {
    "synchronize": "no",
    "synchronization-interval": "30min",
    "data-cnx-dn": u"{0}@intra.cea.fr",
    "data-cnx-password": u"",
    "user-base-dn": (u"OU=NeuroSpin,OU=I2BM,OU=Utilisateurs,OU=DSV,"
                     "OU=Utilisateurs et Groupes,OU=SAC,DC=intra,DC=cea,DC=fr"),
    "user-attrs-map": (u"sAMAccountName:login,department:department,mail:mail,"
                       "givenName:firstname,sn:surname,accountExpires:active"),
    "group-base-dn": u"",
    "group-attrs-map": u"cn:name",
    "user-scope": "SUBTREE",
    "user-classes": "user",
    "user-login-attr": "sAMAccountName",
    "user-default-group": "",
    "group-scope": "SUBTREE",
    "group-classes": "",
    "group-filter": "",
}


_LDAP_CONFIGURATION = u"""
# Is the repository responsible to automatically import content from this
# source? You should say yes unless you don't want this behaviour or if you use
# a multiple repositories setup, in which case you should say yes on one
# repository, no on others.
synchronize=%(synchronize)s

# Interval in seconds between synchronization with the external source (default
# to 5 minutes, must be >= 1 min).
synchronization-interval=%(synchronization-interval)s

# Maximum time allowed for a synchronization to be run. Exceeded that time, the
# synchronization will be considered as having failed and not properly released
# the lock, hence it won't be considered
max-lock-lifetime=10min

# Should already imported entities not found anymore on the external source be
# deleted?
delete-entities=no

# Time before logs from datafeed imports are deleted.
logs-lifetime=10d

# Timeout of HTTP GET requests, when synchronizing a source.
http-timeout=1min

# authentication mode used to authenticate user to the ldap.
auth-mode=simple

# realm to use when using gssapi/kerberos authentication.
#auth-realm=

# user dn to use to open data connection to the ldap (eg used to respond to rql
# queries). Leave empty for anonymous bind
data-cnx-dn=%(data-cnx-dn)s

# password to use to open data connection to the ldap (eg used to respond to
# rql queries). Leave empty for anonymous bind.
data-cnx-password=%(data-cnx-password)s

# base DN to lookup for users; disable user importation mechanism if unset
user-base-dn=%(user-base-dn)s

# user search scope (valid values: "BASE", "ONELEVEL", "SUBTREE")
user-scope=%(user-scope)s

# classes of user (with Active Directory, you want to say "user" here)
user-classes=%(user-classes)s

# additional filters to be set in the ldap query to find valid users
user-filter=

# attribute used as login on authentication (with Active Directory, you want to
# use "sAMAccountName" here)
user-login-attr=%(user-login-attr)s

# name of a group in which ldap users will be by default. You can set multiple
# groups by separating them by a comma.
user-default-group=%(user-default-group)s

# map from ldap user attributes to cubicweb attributes (with Active Directory,
# you want to use
# sAMAccountName:login,mail:email,givenName:firstname,sn:surname)
user-attrs-map=%(user-attrs-map)s

# base DN to lookup for groups; disable group importation mechanism if unset
group-base-dn=%(group-base-dn)s

# group search scope (valid values: "BASE", "ONELEVEL", "SUBTREE")
group-scope=%(group-scope)s

# classes of group
group-classes=%(group-classes)s

# additional filters to be set in the ldap query to find valid groups
group-filter=%(group-filter)s

# map from ldap group attributes to cubicweb attributes
group-attrs-map=%(group-attrs-map)s"""


def _escape_rql(request):
    return request.replace("\\", "\\\\").replace("'", "\\'")


_DESTINATION_LDAP_ATTRIBUTES = {
    u"name": u"SCHIIRDOR_DESTINATION",
    u"type": u"ldapfeed",
    u"config": _escape_rql(
        _LDAP_CONFIGURATION % _DESTINATION_LDAP_CONFIGURATION_DETAILS),
    u"url": u"ldap://127.0.0.1/",
    u"parser": u"ldapfeed"
}
_SOURCE_LDAP_ATTRIBUTES = {
    u"name": u"SCHIIRDOR_SOURCE",
    u"type": u"ldapfeed",
    u"config": _escape_rql(
        _LDAP_CONFIGURATION % _SOURCE_LDAP_CONFIGURATION_DETAILS),
    u"url": u"ldaps://intra.cea.fr/",
    u"parser": u"ldapfeed"
}

def _create_or_update_ldap_data_source(session, update=False):
    """ Create the LDAP data source if not already created. Update the LDAP
    data if requested.
    """
    for attributes in [_DESTINATION_LDAP_ATTRIBUTES, _SOURCE_LDAP_ATTRIBUTES]:
        name = attributes[u"name"]
        req = "Any X WHERE X is CWSource, X name '%(name)s'" % {"name": name}
        rset = session.execute(req)
        if rset.rowcount == 1 and update:
            print("Updating source '%s'..." % name)
            req = "SET"
            for attribute, value in attributes.iteritems():
                req += " X %(attribute)s '%(value)s'," % {"attribute": attribute,
                                                          "value": value}
            req = req[:-1]
            req += " WHERE X is CWSource, X name '%(name)s'" % {"name": name}
        elif rset.rowcount == 0:
            print("Creating source '%s'..." % name)
            req = "INSERT CWSource X:"
            for attribute, value in attributes.iteritems():
                req += " X %(attribute)s '%(value)s'," % {"attribute": attribute,
                                                          "value": value}
            req = req[:-1]
        else:
            print("Existing source '%s' (%i)." % (name, rset[0][0]))

        rset = session.execute(req)
        session.commit()

