# -*- coding: utf-8 -*-

import logging

from zope.i18nmessageid import MessageFactory
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.atapi import process_types
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.utils import ContentInit

_ = MessageFactory('bika.reports')
PROJECTNAME = "bika.reports"


# import this to log messages
logger = logging.getLogger("bika.reports")


def initialize(context):
    logger.info("*** Initializing BIKA.LIMS ***")
    from bika.reports.content.report import Report  # noqa
    from bika.reports.content.reportfolder import ReportFolder  # noqa
    from senaite.core import permissions

    content_types, constructors, ftis = process_types(
        listTypes(PROJECTNAME), PROJECTNAME)

    # Register each type with it's own Add permission
    # use "Add portal content" as default
    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: Add %s" % (PROJECTNAME, atype.portal_type)
        perm_name = "Add portal content"
        perm = getattr(permissions, perm_name, AddPortalContent)
        ContentInit(kind,
                    content_types=(atype,),
                    permission=perm,
                    extra_constructors=(constructor, ),
                    fti=ftis,
                    ).initialize(context)
