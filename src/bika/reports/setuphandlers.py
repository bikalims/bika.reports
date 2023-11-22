# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Products.CMFPlone.interfaces import INonInstallable
from Products.GenericSetup.utils import _resolveDottedName
from zope.interface import implementer
from senaite.core.catalog import REPORT_CATALOG
from senaite.core.catalog import ReportCatalog
from senaite.core.setuphandlers import _run_import_step
from senaite.core.setuphandlers import add_catalog_index
from senaite.core.setuphandlers import add_catalog_column
from senaite.core.setuphandlers import reindex_catalog_index
from bika.lims import api
from bika.reports.config import PROFILE_ID
from bika.reports import logger

PORTAL_CATALOG = "portal_catalog"
CATALOGS = (
    ReportCatalog,
)

CATALOG_MAPPINGS = (
    # portal_type, catalog_ids
    ("Report", [REPORT_CATALOG, PORTAL_CATALOG]),
)


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'bika.reports:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # logger.info("{} setup handler [BEGIN]".format(PRODUCT_NAME.upper()))
    profile_id = PROFILE_ID
    context = context._getImportContext(profile_id)
    portal = context.getSite()
    portal = context.getSite()
    # Do something at the end of the installation of this package.
    _run_import_step(portal, "typeinfo", "profile-bika.reports:default")
    _run_import_step(portal, "browserlayer", profile=profile_id)
    _run_import_step(portal, "rolemap", profile=profile_id)
    _run_import_step(portal, "typeinfo", profile=profile_id)
    _run_import_step(portal, "workflow", "profile-bika.reports:default")
    setup_core_catalogs(portal)
    setup_catalog_mappings(portal)
    # add_reports_folder(portal)


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def setup_core_catalogs(portal, catalog_classes=None, reindex=True):
    """Setup core catalogs
    """
    logger.info("*** Setup core catalogs ***")
    at = api.get_tool("archetype_tool")

    # allow add-ons to use this handler with own catalogs
    if catalog_classes is None:
        catalog_classes = CATALOGS

    # contains tuples of (catalog, index) pairs
    to_reindex = []

    for cls in catalog_classes:
        module = _resolveDottedName(cls.__module__)

        # get the required attributes from the module
        catalog_id = module.CATALOG_ID
        catalog_indexes = module.INDEXES
        catalog_columns = module.COLUMNS
        catalog_types = module.TYPES

        catalog = getattr(aq_base(portal), catalog_id, None)
        if catalog is None:
            catalog = cls()
            catalog._setId(catalog_id)
            portal._setObject(catalog_id, catalog)

        # catalog indexes
        for idx_id, idx_attr, idx_type in catalog_indexes:
            if add_catalog_index(catalog, idx_id, idx_attr, idx_type):
                to_reindex.append((catalog, idx_id))
            else:
                continue

        # catalog columns
        for column in catalog_columns:
            add_catalog_column(catalog, column)

        if not reindex:
            logger.info("*** Skipping reindex of new indexes")
            return

        # map allowed types to this catalog in archetype_tool
        for portal_type in catalog_types:
            # check existing catalogs
            catalogs = at.getCatalogsByType(portal_type)
            if catalog not in catalogs:
                existing = list(map(lambda c: c.getId(), catalogs))
                new_catalogs = existing + [catalog_id]
                at.setCatalogsByType(portal_type, new_catalogs)
                logger.info("*** Mapped catalog '%s' for type '%s'"
                            % (catalog_id, portal_type))

    # reindex new indexes
    for catalog, idx_id in to_reindex:
        reindex_catalog_index(catalog, idx_id)


def setup_catalog_mappings(portal, catalog_mappings=None):
    """Setup portal_type -> catalog mappings
    """
    logger.info("*** Setup Catalog Mappings ***")

    # allow add-ons to use this handler with own mappings
    if catalog_mappings is None:
        catalog_mappings = CATALOG_MAPPINGS

    at = api.get_tool("archetype_tool")
    for portal_type, catalogs in catalog_mappings:
        at.setCatalogsByType(portal_type, catalogs)

def add_reports_folder(portal):
    """Adds the initial Patient folder
    """
    if portal.get("reports") is None:
        logger.info("Adding Reports Folder")
        portal.invokeFactory("ReportFolder", "reports", title="Reports")
