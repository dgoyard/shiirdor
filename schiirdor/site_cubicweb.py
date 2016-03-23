##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

options = (
    ('registration-cypher-seed',
     {'type' : 'string',
      'default': u'',
      'help': 'seed used to cypher registration data in confirmation email link',
      'group': 'schiirdor',
      'level': 1,
      }),
    ('logo',
     {'type': 'string',
      'default': 'images/nsap.png',
      'help': 'Navigation bar logo',
      'group': 'schiirdor',
      'level': 2,
      }),
    ('disable-ldapfeed',
     {'type' : 'yn',
      'default': True,
      'help': 'If true disable the CubicWeb LDAPFEED connection.',
      'group': 'schiirdor',
      'level': 3,
      }),
    ('restricted-groups',
     {'type' : 'csv',
      'default': 'managers,users,guests,moderators',
      'help': 'A list of groups the moderators cannot administrate.',
      'group': 'schiirdor',
      'level': 4,
      })
)
