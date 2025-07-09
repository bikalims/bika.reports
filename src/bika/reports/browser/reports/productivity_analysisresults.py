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

import csv
import datetime
import json

from six import StringIO
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import api
from bika.lims import bikaMessageFactory as _
from bika.lims.browser import BrowserView
from bika.lims.catalog.analysis_catalog import CATALOG_ANALYSIS_LISTING
from bika.lims.utils import formatDateQuery, formatDateParms
from plone.app.layout.globals.interfaces import IViewView
from senaite.core.i18n import translate as t
from senaite.core import logger
from zope.interface import implements


class Report(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile("templates/report_out.pt")

    def __init__(self, context, request, report=None):
        BrowserView.__init__(self, context, request)
        self.report = report
        self.headings = {
            "header": _("Analysis Results"),
            "subheader": _("The results of an analysis plotted over time"),
        }
        self.formats = {
            "columns": 2,
            "col_heads": [_("Date"), _("Result")],
            "class": "",
        }
        self.plot_enabled = False

    def __call__(self):
        parms = []
        # HACK - which sort data
        query = dict(
            portal_type="Analysis", sort_on="getDateReceived", sort_order="ascending"
        )
        # # HACK testing
        # analyses = api.search(query, CATALOG_ANALYSIS_LISTING)
        # logger.info("Select analysis-results found {} results".format(len(analyses)))
        # for analysis in analyses:
        #     logger.info("Select analysis-results {} ".format(analysis.getServiceUID))

        # Filter by Service UID
        self.add_filter_by_service(query=query, out_params=parms)

        # Filter by Specification UID
        self.add_filter_by_specification(query=query, out_params=parms)

        # # Filter by Analyst
        # self.add_filter_by_analyst(query=query, out_params=parms)

        # Filter by date range
        self.add_filter_by_date_range(query=query, out_params=parms)

        # Filter by SampleType
        self.add_filter_by_sampletype(query=query, out_params=parms)

        # Fetch the data
        data_lines = []
        total_count = 0
        logger.info("Select analysis-results query: {}".format(query))
        analyses = api.search(query, CATALOG_ANALYSIS_LISTING)
        logger.info("Select analysis-results found {} results".format(len(analyses)))
        plot_points = []
        for analysis in analyses:
            analysis = api.get_object(analysis)
            if not analysis.getResult():
                continue
            # HACK
            # TODO - using Sample date for testing - change to getDateReceived
            data_point = [
                {
                    "value": analysis.Title(),
                    "class": "text",
                },
                {
                    # "value": str(analysis.getdatereceived())[:16],
                    "value": str(analysis.getDateSampled())[:16],
                    "class": "date",
                },
                {
                    "value": analysis.getResult(),
                    "class": "float",
                },
            ]
            data_lines.append(data_point)
            plot_points.append({"x": data_point[1], "y": data_point[2]})
            total_count += 1

        query = dict(
            portal_type="Analysis", sort_on="getDateReceived", sort_order="ascending"
        )
        # filter by Secondary Service UID
        self.add_filter_by_secondservice(query=query, out_params=parms)

        # filter by specification uid
        self.add_filter_by_specification(query=query, out_params=parms)

        #  # filter by analyst
        #  self.add_filter_by_analyst(query=query, out_params=parms)

        # filter by date range
        self.add_filter_by_date_range(query=query, out_params=parms)

        # Filter by SampleType
        self.add_filter_by_sampletype(query=query, out_params=parms)

        # Fetch the data
        logger.info("Select analysis-results query: {}".format(query))
        analyses = api.search(query, CATALOG_ANALYSIS_LISTING)
        logger.info("Select analysis-results found {} results".format(len(analyses)))
        second_plot_points = []
        for analysis in analyses:
            analysis = api.get_object(analysis)
            if not analysis.getResult():
                continue
            # HACK
            # TODO - using Sample date for testing - change to getDateReceived
            data_point = [
                {
                    "value": analysis.Title(),
                    "class": "text",
                },
                {
                    # "value": str(analysis.getDateReceived())[:16],
                    "value": str(analysis.getDateSampled())[:16],
                    "class": "date",
                },
                {
                    "value": analysis.getResult(),
                    "class": "float",
                },
            ]
            data_lines.append(data_point)
            second_plot_points.append({"x": data_point[1], "y": data_point[2]})
            total_count += 1

        if self.request.get("output_format", "") == "CSV":
            return self.generate_csv(data_lines)

        self.report_content = {
            "headings": self.headings,
            "parms": parms,
            "formats": self.formats,
            "datalines": data_lines,
            "footings": [],
        }
        if self.plot_enabled:
            # Set up plot data
            plot_data = [
                {
                    "plot_color": "red",
                    "plot_type": "line",
                    "show_points": True,
                    "plot_points": plot_points,
                    "y_axis": "left",
                    "line_style": "solid",
                    "left_axis_title": "LHS",
                }
            ]
            if len(second_plot_points):
                plot_data.append(
                    {
                        "plot_color": "blue",
                        "plot_type": "line",
                        "show_points": True,
                        "plot_points": second_plot_points,
                        "y_axis": "right",
                        "line_style": "solid",
                        "right_axis_title": "RHS",
                    }
                )
            if self.request.form.get("spec", ""):
                # get specification for analaysis
                # find upper and lower limits
                # create hlines for them
                # append to plot_data
                spec = api.get_object(self.request.form.get("spec"))
                results_range = spec.getResultsRange()
                if results_range:
                    an_range = []
                    for ar in results_range:
                        logger.info(
                            "ResultsRange: looking at {} for matching analysis {}".format(
                                ar["keyword"], analysis.getKeyword()
                            )
                        )
                        if ar["keyword"] == analysis.getKeyword():
                            an_range.append(ar)
                    logger.info(
                        "ResultsRange: found {} for analysis {}".format(
                            len(an_range), analysis.Title()
                        )
                    )
                    if an_range:
                        an_range = an_range[0]
                        spec_min = an_range.get("min")
                        if spec_min:
                            plot_data.append(
                                {
                                    "plot_color": "green",
                                    "plot_type": "hline",
                                    "show_points": False,
                                    "plot_points": [
                                        {
                                            "y": {"type": "float", "value": spec_min},
                                        },
                                    ],
                                }
                            )
                        spec_max = an_range.get("max")
                        if spec_max:
                            plot_data.append(
                                {
                                    "plot_color": "green",
                                    "plot_type": "hline",
                                    "show_points": False,
                                    "plot_points": [
                                        {
                                            "y": {"type": "float", "value": spec_max},
                                        },
                                    ],
                                }
                            )

            self.plot_data = json.dumps(plot_data)
            logger.info("Plot: {}".format(self.plot_data))

        # test_template = self.template()
        # print(test_template)
        # import pdb; pdb.set_trace()  # fmt: skip
        return {
            "report_title": t(self.headings["header"]),
            "report_data": self.template(),
        }

    def add_filter_by_service(self, query, out_params):
        if not self.request.form.get("ServiceUID", ""):
            return
        query["getServiceUID"] = self.request.form["ServiceUID"]
        service = api.get_object_by_uid(query["getServiceUID"])
        out_params.append(
            {"title": _("Analysis Service"), "value": service.Title(), "type": "text"}
        )

    def add_filter_by_secondservice(self, query, out_params):
        if not self.request.form.get("SecondServiceUID", ""):
            return
        query["getServiceUID"] = self.request.form["SecondServiceUID"]
        service = api.get_object_by_uid(query["getServiceUID"])
        out_params.append(
            {"title": _("Analysis Service"), "value": service.Title(), "type": "text"}
        )

    def add_filter_by_specification(self, query, out_params):
        if not self.request.form.get("spec", ""):
            return
        query["getSpecificationUID"] = self.request.form["spec"]
        spec = api.get_object_by_uid(query["getSpecificationUID"])
        out_params.append(
            {
                "title": _("Analysis Specification"),
                "value": spec.Title(),
                "type": "text",
            }
        )

    def add_filter_by_sampletype(self, query, out_params):
        if not self.request.form.get("SampleTypeUID", ""):
            return
        query["getSampleTypeUID"] = self.request.form["SampleTypeUID"]
        sampletype = api.get_object_by_uid(query["getSampleTypeUID"])
        out_params.append(
            {
                "title": _("SampleTypeUID"),
                "value": sampletype.Title(),
                "type": "text",
            }
        )

    def add_filter_by_analyst(self, query, out_params):
        if not self.request.form.get("Analyst", ""):
            return
        query["getAnalyst"] = self.request.form["Analyst"]
        out_params.append(
            {
                "title": _("Analyst"),
                "value": self.user_fullname(query["getAnalyst"]),
                "type": "text",
            }
        )

    def add_filter_by_instrument(self, query, out_params):
        if not self.request.form.get("getInstrumentUID", ""):
            return
        query["getInstrumentUID"] = self.request.form["getInstrumentUID"]
        instrument = api.get_object_by_uid(query["getInstrumentUID"])
        out_params.append(
            {"title": _("Instrument"), "value": instrument.Title(), "type": "text"}
        )

    def add_filter_by_date_range(self, query, out_params):
        date_query = formatDateQuery(self.context, "ar_DateReceived")
        if not date_query:
            return
        query["getDateReceived"] = date_query
        out_params.append(
            {
                "title": _("Received"),
                "value": formatDateParms(self.context, "AR_DateReceived"),
                "type": "text",
            }
        )

    def generate_csv(self, data_lines):
        fieldnames = [
            "Date",
            "Turnaround time (h)",
        ]
        output = StringIO()
        dw = csv.DictWriter(output, extrasaction="ignore", fieldnames=fieldnames)
        dw.writerow(dict((fn, fn) for fn in fieldnames))
        for row in data_lines:
            dw.writerow(
                {
                    "Date": row[0]["value"],
                    "Turnaround time (h)": row[1]["value"],
                }
            )
        report_data = output.getvalue()
        output.close()
        date = datetime.datetime.now().strftime("%Y%m%d%H%M")
        setheader = self.request.RESPONSE.setHeader
        setheader("Content-Type", "text/csv")
        setheader(
            "Content-Disposition",
            'attachment;filename="analysesperservice_%s.csv"' % date,
        )
        self.request.RESPONSE.write(report_data)
