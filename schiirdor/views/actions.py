##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.action import Action
from cubicweb.web.views.wdoc import HelpAction
from cubicweb.web.views.wdoc import AboutAction
from cubicweb.web.views.actions import PoweredByAction
from logilab.common.registry import yes


###############################################################################
# ACTIONS
###############################################################################

class SCHIIRDORPoweredByAction(Action):
    __regid__ = "poweredby"
    __select__ = yes()

    category = "footer"
    order = 3
    title = u"Powered by NSAp"

    def url(self):
        return u"https://github.com/neurospin/schiirdor"


def registration_callback(vreg):

    # Update the footer
    vreg.register(SCHIIRDORPoweredByAction)
    vreg.unregister(HelpAction)
    vreg.unregister(AboutAction)
    vreg.unregister(PoweredByAction)
