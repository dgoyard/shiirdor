##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import getpass
import base64

# CW import
from cubicweb.server import hook
from cubicweb import ConfigurationError
from cubicweb.predicates import match_user_groups
from cubicweb.server.sources.ldapfeed import LDAPFeedSource

# Cubes import
from cubes.schiirdor.migration.update_sources import _create_or_update_ldap_data_source
from cubes.schiirdor.migration.update_sources import _DESTINATION_LDAP_ATTRIBUTES
from cubes.schiirdor.migration.update_sources import _SOURCE_LDAP_ATTRIBUTES
from cubes.trustedauth.cryptutils import build_cypher
from cubes.trustedauth.authplugin import XRemoteUserAuthentifier


# Desacitvate ldap sources
LDAPFeedSource.disabled = True
# Define key entry
KEYCONFENTRY = "registration-cypher-seed"


class InGroupHook(hook.Hook):
    """ Set moderators rights when they administrate groups through the
    'in_group' relation.
    """
    __regid__ = "in-group-hook"
    __select__ = (hook.Hook.__select__ & hook.match_rtype("in_group") &
        ~match_user_groups("managers"))
    events = ("before_add_relation", "before_delete_relation")

    def __call__(self):
        """ Before an 'in_group' relation deletion or addition, check the
        assocaited group name: can't modifiy managers, users, guests and
        moderators group associated unless you are administrator.
        """
        parent = self._cw.entity_from_eid(self.eidto)
        child = self._cw.entity_from_eid(self.eidfrom)
        group_name = parent.name
        moderator_name = child.firstname + " " + child.surname
        if group_name in ["managers", "users", "guests", "moderators"]:
            raise ConfigurationError(
                "%s you do not have sufficient permissions to administrate "
                "the '%s' group." % (moderator_name, group_name))


class ExternalAuthSourceHook(hook.Hook):
    """ On startup ask for a login/password to contact the external destination
    authentification ldap based system. If not already specified create
    a 'SCHIIRDOR_SOURCE' and a 'SCHIIRDOR_DESTINATION' sources.

    This class raise a 'ConfigurationError' if a secret key with
    0 < len(key) <= 32 is not specified.
    """
    __regid__ = "external-auth-source-hook"
    events = ("server_startup", )

    def __call__(self):
        """ Important registery parameters are the 'dest_authlogin' and
        'dest_authpassword' used to contact the authentification ldap based
        system.
        """
        # Small hack copied from the trustedauth cube to make sure the secret
        # key file is loaded on both sides of cw (repo and web)
        secretfile = self.repo.vreg.config.get(KEYCONFENTRY, "").strip()
        if not secretfile:
            raise ConfigurationError(
                "Configuration '%s' is missing or empty. "
                "Please check your configuration file!" % KEYCONFENTRY)
        set_secret(self.repo.vreg.config, secretfile)

        # Make sure a login and password is provided to contact the external
        # sources on both sides of cw (repo and web)
        cyphr = build_cypher(self.repo.vreg.config._secret)
        login = raw_input("Enter the destination LDAP based system login: ")
        password = getpass.getpass(
            "Enter the destination LDAP based system password: ")
        self.repo.vreg.dest_authlogin = base64.encodestring(
            cyphr.encrypt("%128s" % login))
        self.repo.vreg.dest_authpassword = base64.encodestring(
            cyphr.encrypt("%128s" % password))

        # Create or update source
        with self.repo.internal_cnx() as cnx:
            _create_or_update_ldap_data_source(cnx)


def set_secret(config, secretfile):
    """ Set a '_secret' config parameter with the 32 bytes key available in the
    'registration-cypher-seed' configuration file.
    """
    try:
        secret = open(secretfile).read().strip()
    except IOError:
        raise ConfigurationError(
            "Cannot open secret key file. Check your configuration file!")
        return
    if not secret or len(secret) > 32:
        raise ConfigurationError(
            "Secret key must me a string 0 < len(key) <= 32.")
    config._secret = secret.ljust(32, "#")

