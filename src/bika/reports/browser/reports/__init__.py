# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE.
#
# SENAITE.CORE is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
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
# Copyright 2018-2021 by it's authors.
# Some rights reserved, see README and LICENSE.

import importlib
import os

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from datetime import datetime
from plone.app.layout.globals.interfaces import IViewView
from zope.component import getAdapters
from zope.interface import implements

from bika.lims import api
from bika.lims.browser import BrowserView
from bika.lims.browser.bika_listing import BikaListingView
from bika.lims.utils import createPdf
from bika.lims.utils import getUsers
from bika.lims.utils import logged_in_client
from bika.reports import _
from bika.reports.browser.reports.selection_macros import SelectionMacrosView
from bika.reports.interfaces import IAdministrationReport
from bika.reports.interfaces import IProductivityReport
from senaite.core.catalog import REPORT_CATALOG


class ProductivityView(BrowserView):
    """ Productivity View form
    """
    implements(IViewView)
    template = ViewPageTemplateFile("templates/productivity.pt")

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.context = context
        self.request = request

    def __call__(self):
        self.selection_macros = SelectionMacrosView(self.context, self.request)
        self.icon = self.portal_url + "/++resource++bika.lims.images/report_big.png"
        self.getAnalysts = getUsers(self.context,
                                    ['Manager', 'LabManager', 'Analyst'])

        self.additional_reports = []
        adapters = getAdapters((self.context, ), IProductivityReport)
        for name, adapter in adapters:
            report_dict = adapter(self.context, self.request)
            report_dict['id'] = name
            self.additional_reports.append(report_dict)

        return self.template()


class AdministrationView(BrowserView):
    """ Administration View form
    """
    implements(IViewView)
    template = ViewPageTemplateFile("templates/administration.pt")

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.context = context
        self.request = request

    def __call__(self):
        self.selection_macros = SelectionMacrosView(self.context, self.request)
        self.icon = self.portal_url + "/++resource++bika.lims.images/report_big.png"

        self.additional_reports = []
        adapters = getAdapters((self.context, ), IAdministrationReport)
        for name, adapter in adapters:
            report_dict = adapter(self.context, self.request)
            report_dict['id'] = name
            self.additional_reports.append(report_dict)

        return self.template()


class ReportHistoryView(BikaListingView):
    """ Report history form
    """
    implements(IViewView)

    def __init__(self, context, request):
        super(ReportHistoryView, self).__init__(context, request)

        self.catalog = REPORT_CATALOG

        self.context_actions = {}

        self.show_select_row = False
        self.show_select_column = False
        self.show_column_toggles = False
        self.show_workflow_action_buttons = False
        self.show_select_all_checkbox = False
        self.pagesize = 50

        self.icon = self.portal_url + "/++resource++bika.lims.images/report_big.png"
        self.title = self.context.translate(_("Reports"))
        self.description = ""

        # this is set up in call where member is authenticated
        self.columns = {}
        self.review_states = []

    def __call__(self):
        self.columns = {
            'Title': {
                'title': _('Title'),
                'attr': 'Title',
                'index': 'title', },
            'file_size': {
                'title': _("Size"),
                'attr': 'getFileSize',
                'sortable': False, },
            'created': {
                'title': _("Created"),
                'attr': 'created',
                'index': 'created', },
            'creator': {
                'title': _("By"),
                'attr': 'getCreatorFullName',
                'index': 'Creator', }, }
        self.review_states = [
            {'id': 'default',
             'title': 'All',
             'contentFilter': {},
             'columns': ['Title',
                         'file_size',
                         'created',
                         'creator']},
        ]

        self.contentFilter = {
            'portal_type': 'Report',
            'sort_order': 'reverse'}

        this_client = logged_in_client(self.context)
        if this_client:
            self.contentFilter['getClientUID'] = this_client.UID()
        else:
            self.columns['client'] = {
                'title': _('Client'),
                'attr': 'getClientTitle',
                'replace_url': 'getClientURL', }

        return super(ReportHistoryView, self).__call__()

    def lookupMime(self, name):
        mimetool = getToolByName(self, 'mimetypes_registry')
        mimetypes = mimetool.lookup(name)
        if len(mimetypes):
            return mimetypes[0].name()
        else:
            return name

    def folderitem(self, obj, item, index):
        item = BikaListingView.folderitem(self, obj, item, index)
        # https://github.com/collective/uwosh.pfg.d2c/issues/20
        # https://github.com/collective/uwosh.pfg.d2c/pull/21
        item['replace']['Title'] = \
             "<a href='%s/ReportFile'>%s</a>" % \
             (item['url'], item['Title'])
        item['replace']['created'] = self.ulocalized_time(item['created'])
        return item


class SubmitForm(BrowserView):
    """ Redirect to specific report
    """
    implements(IViewView)
    frame_template = ViewPageTemplateFile("templates/report_frame.pt")
    # default and errors use this template:
    template = ViewPageTemplateFile("templates/productivity.pt")

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.context = context
        self.request = request

    def __call__(self):
        """Create and render selected report
        """

        # if there's an error, we return productivity.pt which requires these.
        self.selection_macros = SelectionMacrosView(self.context, self.request)
        self.additional_reports = []
        adapters = getAdapters((self.context, ), IProductivityReport)
        for name, adapter in adapters:
            report_dict = adapter(self.context, self.request)
            report_dict['id'] = name
            self.additional_reports.append(report_dict)

        report_id = self.request.get('report_id', '')
        if not report_id:
            message = _("No report specified in request")
            self.logger.error(message)
            self.context.plone_utils.addPortalMessage(message, 'error')
            return self.template()

        self.date = DateTime()
        username = self.context.portal_membership.getAuthenticatedMember().getUserName()
        self.reporter = self.user_fullname(username)
        self.reporter_email = self.user_email(username)

        # signature image
        self.reporter_signature = ""
        c = [x for x in self.senaite_catalog_setup(portal_type='LabContact')
             if x.getObject().getUsername() == username]
        if c:
            sf = c[0].getObject().getSignature()
            if sf:
                self.reporter_signature = sf.absolute_url() + "/Signature"

        lab = self.context.bika_setup.laboratory
        self.laboratory = lab
        self.lab_title = lab.getName()
        self.lab_address = lab.getPrintAddress()
        self.lab_email = lab.getEmailAddress()
        self.lab_url = lab.getLabURL()

        client = logged_in_client(self.context)
        if client:
            clientuid = client.UID()
            self.client_title = client.Title()
            self.client_address = client.getPrintAddress()
        else:
            clientuid = None
            self.client_title = None
            self.client_address = None

        # Render form output

        # the report can add file names to this list; they will be deleted
        # once the PDF has been generated.  temporary plot image files, etc.
        self.request['to_remove'] = []

        if "report_module" in self.request:
            module = self.request["report_module"]
        else:
            module = "bika.reports.browser.reports.%s" % report_id
        try:
            Report = getattr(importlib.import_module(module), "Report")
            # required during error redirect: the report must have a copy of
            # additional_reports, because it is used as a surrogate view.
            Report.additional_reports = self.additional_reports
        except (ImportError, AttributeError):
            message = "Report %s.Report not found (shouldn't happen)" % module
            self.logger.error(message)
            self.context.plone_utils.addPortalMessage(message, 'error')
            return self.template()

        # Report must return dict with:
        # - report_title - title string for pdf/history listing
        # - report_data - rendered report
        output = Report(self.context, self.request)()

        # if CSV output is chosen, report returns None
        if not output:
            return

        if type(output) in (str, unicode, bytes):
            # remove temporary files
            for f in self.request['to_remove']:
                os.remove(f)
            return output

        # The report output gets pulled through report_frame.pt
        self.reportout = output['report_data']
        framed_output = self.frame_template()

        # this is the good part
        pdf = createPdf(framed_output)

        # remove temporary files
        for f in self.request['to_remove']:
            os.remove(f)

        if not pdf:
            return

        # Create new report object
        title = output["report_title"]
        data = {"title": title, "Client": clientuid, "ReportFile": pdf}
        api.create(self.context, "Report", **data)

        now = datetime.now().strftime("%y%m%d%H%M%S")
        fn = "{}-{}.pdf".format(now, title)

        setheader = self.request.response.setHeader
        setheader("Content-Type", "application/pdf")
        setheader("Content-Disposition", "attachment; filename=\"%s\"" % fn)
        setheader("Content-Length", len(pdf))
        setheader("Cache-Control", "no-store")
        setheader("Pragma", "no-cache")
        self.request.response.write(pdf)
