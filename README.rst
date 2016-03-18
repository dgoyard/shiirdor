
==========
SCHIIRDOR
==========


Summary
=======

This cube provides a way to administrate LDAP user in a CubicWeb instance.
The mechanism works as follow:

* anonymous users ask to be administrate through a web form.
* users must be created in a source LDAP resource.
* users validate their account following a link sent by mail.
* a CubicWeb user is created
* moderators can then give a CubicWeb user specific permissions.
* moderators synchronized their work with a destination LDAP resource.

