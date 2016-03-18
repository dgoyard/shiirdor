##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import re

# Cubicweb import
from cubicweb.view import View
from logilab.common.decorators import monkeypatch


@monkeypatch(View)
def page_title(self):
    """ Returns a title according to the result set - used for the
    title in the HTML header.
    """
    rset = self.cw_rset
    regex = "Any [a-zA-Z] Where [a-zA-Z] is [a-zA-Z]{1,20}"
    rql = ""
    if rset is not None:
        rql = rset.rql
    if rset is not None and rset.rowcount and rset.rowcount == 1:
        try:
            entity = rset.complete_entity(0, 0)
            title = entity.cw_etype
        except NotAnEntity:
            title = _("NotAnEntity")
    elif hasattr(self, "title"):
        title = self.title
    elif len(re.findall(regex, rql)) == 1:
        title = rql.split()[-1]
    else:
        title = _("NoMatch")

    return title

