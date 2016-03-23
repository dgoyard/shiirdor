##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views.startup import IndexView


class SCHIIRDORIndexView(IndexView):
    """ Class that defines the index view.
    """
    title = _("Index")

    def call(self, **kwargs):
        """ Create the 'index' like page of our site that propose a
        registration form.
        """
        self.w(u"<h1>Welcome to the management system.</h1>")
        #self.wview("registration")


def registration_callback(vreg):
    vreg.register_and_replace(SCHIIRDORIndexView, IndexView)
