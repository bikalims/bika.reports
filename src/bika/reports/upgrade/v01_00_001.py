# -*- coding: utf-8 -*-

from bika.lims import api
from bika.reports.config import PROJECTNAME
from bika.reports.config import PROFILE_ID
from bika.reports.config import logger
from senaite.core.upgrade import upgradestep
# from senaite.core.upgrade.utils import UpgradeUtils
from senaite.core.catalog import REPORT_CATALOG

version = "1.0.1"


@upgradestep(PROJECTNAME, version)
def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    setup = portal.portal_setup
    portal = tool.aq_inner.aq_parent
    # ut = UpgradeUtils(portal)
    # ver_from = ut.getInstalledVersion(PROJECTNAME)

    # -------- ADD YOUR STUFF BELOW --------

    setup.runImportStepFromProfile(PROFILE_ID, "workflow")
    update_workflow_mappings_reports(portal)
    logger.info("{0} upgraded to version {1}".format(PROJECTNAME, version))
    return True


def update_workflow_mappings_reports(portal):
    """
    """
    logger.info("Updating role mappings for Reports ...")
    wf_id = "senaite_deactivable_type_workflow"
    query = {"portal_type": "Report"}
    brains = api.search(query, REPORT_CATALOG)
    update_workflow_mappings_for(portal, wf_id, brains)
    logger.info("Updating role mappings for Samples [DONE]")


def update_workflow_mappings_for(portal, wf_id, brains):
    wf_tool = api.get_tool("portal_workflow")
    workflow = wf_tool.getWorkflowById(wf_id)
    total = len(brains)
    for num, brain in enumerate(brains):
        if num and num % 100 == 0:
            logger.info("Updating role mappings: {0}/{1}".format(num, total))
        obj = api.get_object(brain)
        workflow.updateRoleMappingsFor(obj)
        obj.reindexObject(idxs=["allowedRolesAndUsers"])
