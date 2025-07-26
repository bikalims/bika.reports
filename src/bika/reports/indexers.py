from bika.lims.interfaces import IAnalysis
from plone.indexer import indexer
from senaite.core import logger
from senaite.core.interfaces import IAnalysisCatalog


@indexer(IAnalysis, IAnalysisCatalog)
def getSamplePointUID(instance):
    sample = instance.aq_parent
    if sample.portal_type != "AnalysisRequest":
        return
    if not hasattr(sample, "getSamplePointUID"):
        return
    logger.debug("----------- Sample: {}".format(sample.getSamplePointUID()))
    return sample.getSamplePointUID()


@indexer(IAnalysis, IAnalysisCatalog)
def getAnalysisSpecUID(instance):
    logger.info("----------- getAnalysisSpecUID")
    sample = instance.aq_parent
    if sample.portal_type != "AnalysisRequest":
        return
    logger.info("----------- Sample: {}".format(sample.getSpecification().UID()))
    return sample.getSpecification().UID()
