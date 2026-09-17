# -*- coding: utf-8 -*-

import logging
from zope.i18nmessageid import MessageFactory

PROFILE_ID = "profile-bika.reports:default"
PROJECTNAME = "bika.reports"
_ = MessageFactory(PROJECTNAME)
logger = logging.getLogger(PROJECTNAME)
