##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import types

# Cubicweb import
from cubicweb.web.views.primary import PrimaryView


# Add summary method for 3.20 compatibility.
def summary(self, entity):
    return u""
PrimaryView.summary= types.MethodType(summary, PrimaryView)

