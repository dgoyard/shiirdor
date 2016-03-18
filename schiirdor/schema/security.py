##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CubicWeb import
from cubicweb.schemas.base import CWUser
from cubicweb.schemas.bootstrap import CWGroup
from cubicweb.schemas.base import EmailAddress
from cubicweb.schemas.base import CWSource
from cubicweb.schemas.base import in_group

from yams import BASE_GROUPS
from cubicweb.schema import PUB_SYSTEM_ENTITY_PERMS
from cubicweb.schema import PUB_SYSTEM_REL_PERMS
from cubicweb.schema import PUB_SYSTEM_ATTR_PERMS
from cubicweb.schema import RO_REL_PERMS
from cubicweb.schema import RO_ATTR_PERMS


###############################################################################
# Set permissions
# 
# ['CWProperty', 'CWRelation', 'Bookmark', 'CWAttribute', 'CWConstraintType',
#  'RQLExpression', 'BigInt', 'TZTime', 'BaseTransition', 'CWEType',
#  'CWComputedRType', 'String', 'Workflow', , 'TrInfo',
#  'CWDataImport', 'CWSourceHostConfig', 'Date', 'CWRType', 'Password',
#  'CWConstraint', 'Transition', 'CWUniqueTogetherConstraint', ,
#  'Decimal', 'Interval', 'Bytes', 'TZDatetime', 'Time',
#  'SubWorkflowExitPoint', 'ExternalUri', 'CWCache', 'Int', 'Float',
#  'WorkflowTransition', 'State', 'Datetime', 'Boolean',
#  'CWSourceSchemaConfig']
#
# Secured:
# ['CWSource', 'CWGroup', 'CWUser', 'EmailAddress']
###############################################################################

IN_GROUP_PERMISSIONS = {
    "read": ("managers", "moderators"),
    "add": ("managers", "moderators"),
    "delete": ("managers", "moderators"),
}

MODERATORS_PERMISSIONS = {
    "read": ("managers", "moderators"),
    "add": ("managers",),
    "update": ("managers",),
    "delete": ("managers",),
}

BASE_GROUPS.add("moderators")
in_group.__permissions__ = IN_GROUP_PERMISSIONS
for entity in [CWUser, CWGroup, EmailAddress, CWSource]:
    entity.__permissions__ = MODERATORS_PERMISSIONS


def post_build_callback(schema):

    # Get the schema
    entities = schema.entities()

    # Set strict default permissions for unknown entities
    for entity in entities:
        entity.permissions = MODERATORS_PERMISSIONS



