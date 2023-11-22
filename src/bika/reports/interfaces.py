# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class IBikaReportsLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IReportFolder(Interface):
    """Report folder
    """


class IReportsFolder(Interface):
    """Reports Folder
    """


class IProductivityReport(Interface):
    """Reports are enumerated manually in reports/*.pt - but addional reports
    can be added to this list by extension packages using this adapter.

    The adapter must return a dictionary:

    {
     title: text (i18n translated),
     description: text (i18n translated),
     query_form: html <fieldset> of controls used to enter report
                 parameters (excluding <form> tags and <submit> button)
     module: The name of the module containing a class named "Report"
             an instance of this class will be used to create the report
    }
    """


class IAdministrationReport(Interface):
    """Reports are enumerated manually in reports/*.pt - but addional reports
    can be added to this list by extension packages using this adapter.

    The adapter must return a dictionary:

    {
     title: text (i18n translated),
     description: text (i18n translated),
     query_form: html <fieldset> of controls used to enter report
                 parameters (excluding <form> tags and <submit> button)
     module: The name of the module containing a class named "Report"
             an instance of this class will be used to create the report
    }
    """
