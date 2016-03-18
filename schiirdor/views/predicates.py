##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CubicWeb import
from logilab.common.registry import objectify_predicate


@objectify_predicate
def trust_authenticated(cls, req, rset=None, **kwargs):
    """ A predicate use to detect single signe on 'SSO' users.
    """
    return int(getattr(req.session, "trusted_cwuser", False))
