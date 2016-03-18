##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import base64
import ldap

# CubicWeb import
from cubicweb.web import formwidgets
from yams.schema import role_name
from cubicweb import mail
from cubicweb import crypto
from cubicweb.web import formfields
from cubicweb.web.views import forms
from cubicweb.web import captcha
from cubicweb.web import form
from cubicweb.view import View
from cubicweb.web import controller
from cubicweb.web import Redirect, ValidationError, ProcessFormError
from cubicweb.web.httpcache import NoHTTPCacheManager
from cubicweb.web.views import urlrewrite

# Cubes import
from cubes.schiirdor.ldapfeed import LDAPConnection
from cubes.trustedauth.cryptutils import build_cypher


class RegistrationFormView(form.FormViewMixIn, View):
    """ Display an anonymous registration view.
    """
    __regid__ = "registration"
    title = _("Registration form")
    templatable = True
    http_cache_manager = NoHTTPCacheManager

    def call(self):
        if "_message" in self._cw.form:
            components = self._cw.vreg["components"]
            msgcomp = components.select_or_none("applmessages", self._cw,
                                                rset=self.cw_rset)
            if msgcomp:
                msgcomp.render(w=self.w, msg=self._cw.form["_message"])
        form = self._cw.vreg["forms"].select("registration", self._cw)
        form.render(w=self.w, display_progress_div=False)


class RegistrationForm(forms.FieldsForm):
    """ Create an anonymous registration form.
    """
    __regid__ = "registration"
    domid = "registrationForm"
    title = _("Registration form")
    form_buttons = [formwidgets.SubmitButton()]

    @property
    def action(self):
        return self._cw.build_url(u"registration_sendmail")

    # Properly name fields according to validation errors that may be raised by
    # the register_user service
    login = formfields.StringField(
        widget=formwidgets.TextInput(),
        role="subject",
        label=_("Login"),
        help=_("Please enter your CEA login."),
        required=True)
    upassword = formfields.StringField(
        widget=formwidgets.PasswordInput(),
        role="subject",
        required=True)
    captcha = formfields.StringField(
        widget=captcha.CaptchaWidget(), required=True,
        label=_("Captcha"),
        help=_("Please copy the letters from the image"))


class RegistrationSendMailController(controller.Controller):
    """ Send an email to the new user in order to validate his account.
    """
    __regid__ = "registration_sendmail"
    content = _(u"""
        Hello %(firstname)s %(surname)s,
        thanks for registering on %(base_url)s.
        Please click on the link below to activate your account: %(url)s
        See you soon on %(base_url)s!
        """)
    subject = _(u"Confirm your registration on %(base_url)s")
    auth_rql = ("Any X WHERE X is CWUser, X login %(login)s")
    src_name = "SCHIIRDOR_SOURCE"
    src_rql = ("Any X, T, U, C Where X is CWSource, X name 'SCHIIRDOR_SOURCE', "
               "X type T, X url U, X config C")

    def publish(self, rset=None):
        """ Publish the form data.

        You will have to specify the SMTP host in the instance
        all-in-one.conf file:
            smtp-host=mx.intra.cea.fr
        """
        # Check the form content
        data = self.checked_data()

        # Send a confirmation email
        recipient = data["mail"]
        msg = self.build_email(recipient, data)
        self._cw.vreg.config.sendmails([(msg, (recipient,))])

        # Redirection
        raise Redirect(self.success_redirect_url())

    def checked_data(self):
        """ Only basic data check here (required attributes field and
        valid account).
        """
        # Get the registration form
        form = self._cw.vreg["forms"].select("registration", self._cw)

        # Create a connection configuration for the ldap resource
        cyphr = build_cypher(self._cw.vreg.config._secret)
        with self.appli.repo.internal_cnx() as cnx:
            rset = cnx.execute(self.src_rql)
        if rset.rowcount != 1:
            raise Exception("No resource attached to this RQL: "
                            "{0}.".format(self.src_rql))
        seid, stype, surl, sconfig = rset[0]

        # Check all fields
        form.formvalues = {}
        data = {}
        errors = {}
        for field in form.fields:
            try:
                for inner_field, value in field.process_posted(form):
                    data[inner_field.name] = value
            except ProcessFormError, exc:
                errors[field.role_name()] = unicode(exc)

        # Login special check
        # Check that the user is in the authentification ldap based system
        if "login" in data and "upassword" in data:
            try:
                connection = LDAPConnection(seid, self.src_name, stype, surl,
                                            sconfig, data["login"],
                                            data["upassword"])
                user_info = connection.is_valid_login(data["login"],
                                                      filter_attributes=True)
                connection.close()
                if user_info is None:
                    raise ProcessFormError("'{0}' is not a valid CEA "
                                           "account".format(data["login"]))
                # Update the form data with the ldap based system
                # information
                if "login" in user_info:
                    user_info.pop("login")
                data.update(user_info)
                data["login"] = data["login"]
                secret = cyphr.encrypt("%128s" % data["login"])
                data["upassword"] = base64.encodestring(secret)

                # Guarentee the login is not already in use
                with self.appli.repo.internal_cnx() as cnx:
                    rset = cnx.execute(self.auth_rql, {"login": value})
                if rset.rowcount != 0:
                    raise ProcessFormError(
                        "An account has already been created for user "
                        "'{0}'.".format(value))
            except ProcessFormError, exc:
                errors["login-subject"] = unicode(exc)
            except ldap.INVALID_CREDENTIALS, exc:
                errors["login-subject"] = u"Invalid credentials"

        # Display errors if detected
        if errors:
            raise ValidationError(None, errors)

        return data

    def build_email(self, recipient, data):
        """ Create the confimration email content.
        """
        # Build url before modifying data
        activationurl = self.activation_url(data)

        # Add base url and action url
        data.update({"base_url": self._cw.base_url(secure=True),
                     "url": activationurl})

        # Format mail content
        content = self._cw._(self.content) % data
        subject = self._cw._(self.subject) % data
        return mail.format_mail({}, [recipient], content=content,
                                subject=subject, config=self._cw.vreg.config)

    def activation_url(self, data):
        """ Create a crypted activation url.
        """
        key = crypto.encrypt(data, self._cw.vreg.config._secret)
        return self._cw.build_url("registration_confirm", key=key,
                                  __secure__=True)

    def success_redirect_url(self):
        """ Create a redirection with registration message.
        """
        msg = self._cw._(u"Your registration email has been sent. Follow "
                         "instructions in there to activate your account.")
        return self._cw.build_url("register", _message=msg)


class RegistrationConfirmController(controller.Controller):
    """ Create the CWUser when user confirm the account creation by clicking
    the link of the confirmation mail.
    """
    __regid__ = "registration_confirm"

    def publish(self, rset=None):
        req = self._cw
        try:
            data = crypto.decrypt(req.form["key"], self._cw.vreg.config._secret)
            login = data["login"]
            password = data.pop("upassword")
        except:
            msg = req._(u"Invalid registration data. Please try registering again.")
            raise Redirect(req.build_url("register", _message=msg))
        if self._cw.user.login == login:
            # already logged in (e.g. regstration link replayed twice in the browser)
            raise Redirect(self.success_redirect_url(self._cw.user.name()))
        # Check the user has not been created yet
        with self.appli.repo.internal_cnx() as cnx:
            msg = req._(u"Account already validated. Please try to login.")
            rset = cnx.execute(
                "Any U Where U is CWUser, U login '{0}'".format(login))
        if rset.rowcount != 0:
             raise Redirect(req.build_url("register", _message=msg))
        req.form = data # hijack for proper validation error handling
        err_raised = False
        try:
            with self.appli.repo.internal_cnx() as cnx:
                cnx.call_service("register_user",
                                 login=unicode(login), password=password,
                                 email=unicode(data.get("mail")),
                                 firstname=unicode(data.get("firstname")),
                                 surname=unicode(data.get("surname")))
                cnx.commit()
        except ValidationError, err:
            err_raised = True
            # XXX TEMPORARY HACK to allow registration links to work more than
            # once. This is required because some email clients (e.g. kmail)
            # start by downloading the url to find the mimetype of the resource
            # and then execute the appropriate action (e.g. open the url in the
            # default browser) based on the mimetype.
            if err.errors.keys() != ["login"]:
                raise
        # Try to connect using the provided credentials
        try:
            from cubicweb import repoapi
            cnx = repoapi.connect(self.appli.repo, login, password=password)
            with cnx:
                name = cnx.user.name()
            raise Redirect(self.success_redirect_url(name))
        except:
            if err_raised:
                # Both registration and login failed, re-raise the previous
                # ValidationError
                raise err
            raise

    def success_redirect_url(self, name):
        msg = self._cw._(u"Congratulations, your registration is complete. "
                         "Welcome %s !")
        return self._cw.build_url("register", _message=msg % name)


class RegistrationSimpleReqRewriter(urlrewrite.SimpleReqRewriter):
    """ Create a redirection.
    """
    rules = [("/register", dict(vid="registration")), ]

