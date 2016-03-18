##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from logilab.common.registry import yes
from cubicweb.predicates import match_user_groups
from cubicweb.predicates import anonymous_user
from cubicweb.predicates import authenticated_user
from cubicweb.web import component
from cubicweb.web.views.boxes import SearchBox
from cubicweb.web.views.bookmark import BookmarksBox
from cubicweb.web.views.basecomponents import HeaderComponent
from cubicweb.web.views.basecomponents import ApplLogo
from cubicweb.web.views.basecomponents import CookieLoginComponent
from logilab.common.decorators import monkeypatch
from cubicweb.web.views.basecomponents import AuthenticatedUserStatus

# Cubes import
from .predicates import trust_authenticated
from cubes.bootstrap.views.basecomponents import BSAuthenticatedUserStatus


try:
    from cubicweb import _
except ImportError:
    _ = unicode


class AnonRegisterButton(HeaderComponent):
    """ Build a registration button displayed in the header.
    """
    __regid__ = "anon-registration"
    __select__ = HeaderComponent.__select__ & anonymous_user()
    context = "header-right"

    def render(self, w):
        self._cw.add_css("cubicweb.pictograms.css")
        w(u"<a href='{0}' type='button' class='btn btn-default "
          "btn-sm'>".format(self._cw.build_url("register")))
        w(u"<span class='glyphicon icon-user-add'>{0}</span>"
          "</a>".format(_("Register")))


class ManagerManageButton(HeaderComponent):
    """ Build a manage button displayed in the header.
    """
    __regid__ = "manager-manage"
    __select__ = (HeaderComponent.__select__ & authenticated_user() &
                  ~trust_authenticated())
    context = "header-right"

    def render(self, w):
        w(u"<a href='{0}' type='button' class='btn btn-default "
          "btn-sm'>".format(
                self._cw.build_url("view", vid="schiirdor.users-management")))
        w(u"<span class='glyphicon glyphicon-sort'>{0}</span>"
          "</a>".format(_(" Groups")))


class ManagerSyncButton(HeaderComponent):
    """ Build a synchronisation button displayed in the header.
    """
    __regid__ = "manager-sync"
    __select__ = (HeaderComponent.__select__ & authenticated_user() &
                  ~trust_authenticated())
    context = "header-right"

    def render(self, w):
        w(u"<a href='{0}' type='button' class='btn btn-default "
          "btn-sm'>".format(
                self._cw.build_url("view", vid="schiirdor.sync-management")))
        w(u"<span class='glyphicon glyphicon-transfer'>{0}</span>"
          "</a>".format(_(" Sync")))


class AdminStatusButton(HeaderComponent):
    """ Build a status button displayed in the header.

    Only the managers have accessed to this functionality.
    """
    __regid__ = "admin-status"
    __select__ = (HeaderComponent.__select__ & authenticated_user() &
                  match_user_groups("managers"))
    context = "header-right"

    def render(self, w):
        w(u"<a href='{0}' type='button' class='btn btn-default "
          "btn-sm'>".format(self._cw.build_url(
                "view", vid="shiirdor.groups-management")))
        w(u"<span class='glyphicon glyphicon-lock'>{0}</span>"
          "</a>".format(_(" Create groups")))


class LogOutButton(AuthenticatedUserStatus):
    """ Close the current session.
    """
    divider_html = u'<li class="divider"></li>'
    def render(self, w):
        w(u"<a href='{0}' type='button' class='btn btn-default "
          "btn-sm'>".format(self._cw.build_url("logout")))
        w(u"<span class='glyphicon glyphicon-log-out'>{0}</span>"
          "</a>".format(_(" Logout")))

    def render_actions(self, w, action):
        w(u'<li>')
        self.action_link(action).render(w=w)
        w(u'</li>')


@monkeypatch(CookieLoginComponent)
def call(self):
    """ Change the login button in the header.
    """
    self._cw.add_css("cubicweb.pictograms.css")
    self._html = u"""
        <a type='button'
           class='btn btn-default btn-sm'
           title="%s"
           data-toggle="modal"
           href="#loginModal">%s</a>"""
    title = u"<span class='glyphicon icon-login'>%s</span>" %  _("Login")
    self.w(self._html % (_("login / password"), title))
    self._cw.view("logform", rset=self.cw_rset, id=self.loginboxid,
                  klass="%s hidden" % self.loginboxid, title=False,
                  showmessage=False, w=self.w, showonload=False)


@monkeypatch(CookieLoginComponent)
def render(self, w):
    # XXX bw compat, though should warn about subclasses redefining call
    self.w = w
    self.call()


@monkeypatch(ApplLogo)
def render(self, w):
    """ Change the logo.
    """
    w(u'<a class="navbar-brand" href="%s"><img id="logo" src="%s" '
      'alt="logo"/></a>' % (
            self._cw.base_url(),
            self._cw.data_url(self._cw.vreg.config.get("logo"))))


def registration_callback(vreg):

    for bclass in [AnonRegisterButton, ManagerManageButton, AdminStatusButton,
                   LogOutButton, ManagerSyncButton]:
        vreg.register(bclass)

    vreg.unregister(BookmarksBox)
    vreg.unregister(SearchBox)
    vreg.unregister(BSAuthenticatedUserStatus)
