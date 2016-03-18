# -*- coding: utf-8 -*-
# copyright 2016 NSAp (CEA, FRANCE), all rights reserved.
# contact https://github.com/neurospin/schiirdor -- mailto:antoine.grigis@cea.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

"""cubicweb-schiirdor entity's classes"""

from cubicweb import ConfigurationError

CONFENTRY = 'trustedauth-secret-key-file'

def set_secret(config, secretfile):
    try:
        secret = open(secretfile).read().strip()
    except IOError:
        config.error("Cannot open secret key file. Check your configuration file!")
        return
    if not secret or len(secret) > 32:
        config.error('secret key must me a string 0 < len(key) <= 32')
        return
    config._secret = secret.ljust(32, '#')

# the presence of this registration callback here is a small hack to
# make sure the secret key file is loaded on both sides of cw (repo
# and web)
def registration_callback(vreg):
    secretfile = vreg.config.get(CONFENTRY, "").strip()
    if not secretfile:
        vreg.config.warning("Configuration '%s' is missing or empty. "
                            "Please check your configuration file!" % CONFENTRY)
        return
    set_secret(vreg.config, secretfile)
