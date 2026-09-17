# -*- coding: utf-8 -*-
#
# This file is part of BIKA.REPORTS.
#
# BIKA.REPORTS is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2019-2021 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api as bika_api
from bika.reports import PROJECTNAME
from bika.reports import PROFILE_ID
from bika.reports import logger
from plone import api as plone_api
from senaite.core.catalog import ANALYSIS_CATALOG
from senaite.core.upgrade import upgradestep
from senaite.core.upgrade.utils import UpgradeUtils
import transaction

version = "1.0.1"


@upgradestep(PROJECTNAME, version)
def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    setup = portal.portal_setup
    ut = UpgradeUtils(portal)
    ver_from = ut.getInstalledVersion(PROJECTNAME)

    if ut.isOlderVersion(PROJECTNAME, version):
        logger.info(
            "Skipping upgrade of {0}: {1} > {2}".format(
                PROJECTNAME, ver_from, version
            )
        )
        return True

    logger.info(
        "Upgrading {0}: {1} -> {2}".format(PROJECTNAME, ver_from, version)
    )

    # -------- ADD YOUR STUFF BELOW --------
    reindex_analysis_catalog(setup)

    logger.info("{0} upgraded to version {1}".format(PROJECTNAME, version))
    return True


def get_valid_objects(brains):
    """Generate a list of objects associated with valid brains."""
    for b in brains:
        try:
            obj = b.getObject()
        except KeyError:
            obj = None

        if obj is None:  # warn on broken entries in the catalog
            logger.warn("Invalid reference: {0}".format(b.getPath()))
            continue
        yield obj


def reindex_analysis_catalog(setup_tool):
    """Reindex catalog to include new indexes."""
    setup_tool.runImportStepFromProfile(PROFILE_ID, "catalog")
    test = "test" in setup_tool.REQUEST  # used to ignore transactions on tests
    logger.info("Reindexing the catalog. ")
    catalog = plone_api.portal.get_tool(ANALYSIS_CATALOG)
    query = {"portal_type": "Analysis"}
    brains = bika_api.search(query, ANALYSIS_CATALOG)
    logger.info("Found {0} analyses".format(len(brains)))
    n = 0
    for obj in get_valid_objects(brains):
        catalog.catalog_object(
            obj,
            idxs=["getSamplePointUID", "getAnalysisSpecUID"],
            update_metadata=False,
        )
        n += 1
        if n % 1000 == 0 and not test:
            transaction.commit()
            logger.info("{0} items processed.".format(n))

    if not test:
        transaction.commit()
    logger.info("Done.")
