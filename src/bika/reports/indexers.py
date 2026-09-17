from bika.lims.interfaces import IAnalysis
from plone.indexer import indexer
from senaite.core import logger
from senaite.core.interfaces import IAnalysisCatalog


@indexer(IAnalysis, IAnalysisCatalog)
def getSamplePointUID(instance):
    if instance.portal_type != "Analysis":
        return
    if not hasattr(instance, "getSamplePointUID"):
        return
    logger.debug(
        "----------- reindex SamplePointUID: {}".format(
            instance.getSamplePointUID()
        )
    )
    return instance.getSamplePointUID()


@indexer(IAnalysis, IAnalysisCatalog)
def getAnalysisSpecUID(instance):
    if instance.portal_type != "Analysis":
        return
    if not hasattr(instance, "getSpecification"):
        return
    if not instance.get("getSpecification"):
        return
    logger.debug(
        "----------- reindex SpecUID: {}".format(
            instance.getSpecification().UID()
        )
    )
    return instance.getSpecification().UID()
