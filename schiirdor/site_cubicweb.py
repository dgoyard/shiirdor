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
      })
)
