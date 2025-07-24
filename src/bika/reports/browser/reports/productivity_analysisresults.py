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

import bs4
import csv
import datetime
import json

import DateTime
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
    template = ViewPageTemplateFile("templates/productivity_analysisresults.pt")

    def __init__(self, context, request, report=None):
        BrowserView.__init__(self, context, request)
        self.report = report
        self.date = DateTime.DateTime()
        today = self.date.strftime("%Y-%m-%d")
        username = self.context.portal_membership.getAuthenticatedMember().getUserName()
        self.headings = {
            "header": _("Analysis Results"),
            "subheader": _("Create on {} by {}".format(today, username)),
            "paramheader": "",
            "analysis": "",
            "analysis_unit": "",
            "second_analysis": "",
            "second_analysis_unit": "",
            "sample_point": "",
        }
        self.formats = {
            "columns": 3,
            "col_heads": [_("Analysis"), _("Date"), _("Result")],
            "class": "",
        }
        self.plot_enabled = True

    def __call__(self):
        parms = []
        query = dict(
            portal_type="Analysis",
            sort_on="getResultCaptureDate",
            sort_order="ascending",
        )
        # Filter by Service UID
        self.add_filter_by_service(query=query, out_params=parms)

        # Filter by Specification UID
        self.add_filter_by_specification(query=query, out_params=parms)

        # Filter by SamplePoint
        self.add_filter_by_samplepoint(query=query, out_params=parms)

        # # Filter by Analyst
        # self.add_filter_by_analyst(query=query, out_params=parms)

        # Filter by date range
        self.add_filter_by_date_range(query=query, out_params=parms)

        # Filter by SampleType
        self.add_filter_by_sampletype(query=query, out_params=parms)

        # Fetch the data
        data_lines = [
            [{"class": "category_heading", "colspan": 3, "value": "Results"}],
        ]
        total_count = 0
        logger.info("Select analysis-results query: {}".format(query))
        analyses = api.search(query, CATALOG_ANALYSIS_LISTING)
        logger.info("Select analysis-results found {} results".format(len(analyses)))
        plot_points = []
        for analysis in analyses:
            analysis = api.get_object(analysis)
            if not analysis.getResult():
                continue
            data_point = [
                {
                    "value": analysis.Title(),
                    "class": "text",
                },
                {
                    "value": str(analysis.getResultCaptureDate())[:16],
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

        second_plot_points = []
        if self.request.form.get("SecondServiceUID"):
            query = dict(
                portal_type="Analysis",
                sort_on="getResultCaptureDate",
                sort_order="ascending",
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
            logger.info(
                "Select analysis-results found {} results".format(len(analyses))
            )
            for analysis in analyses:
                analysis = api.get_object(analysis)
                if not analysis.getResult():
                    continue
                data_point = [
                    {
                        "value": analysis.Title(),
                        "class": "text",
                    },
                    {
                        "value": str(analysis.getResultCaptureDate())[:16],
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

        # Rework headings
        # Heading
        heading = ""
        if self.headings["sample_point"]:
            heading += "{}".format(self.headings["sample_point"])
        if self.headings["analysis"]:
            heading += " {}".format(self.headings["analysis"])
        if self.headings["second_analysis"]:
            heading += " and {}".format(self.headings["second_analysis"])
        heading += " Results {}".format(self.date.strftime("%B %Y"))
        self.headings["header"] = heading

        # ParamHeading
        param_heading = ""
        if self.headings["analysis"]:
            param_heading += " {} {}".format(
                self.headings["analysis"], self.headings["analysis_unit"]
            )
        if self.headings["second_analysis"]:
            param_heading += ", {} {}".format(
                self.headings["second_analysis"], self.headings["second_analysis_unit"]
            )
        self.headings["paramheader"] = param_heading
        self.report_content = {
            "headings": self.headings,
            "parms": parms,
            "formats": self.formats,
            "datalines": data_lines,
            "footings": [],
        }
        if self.plot_enabled:
            # Set up plot data
            title = api.get_object(self.request.form.get("ServiceUID")).title
            plot_data = [
                {
                    "plot_color": "red",
                    "plot_type": "line",
                    "show_points": True,
                    "plot_points": plot_points,
                    "y_axis": "left",
                    "line_style": "solid",
                    "left_axis_title": title,
                }
            ]
            if len(second_plot_points):
                second_title = api.get_object(
                    self.request.form.get("SecondServiceUID")
                ).title
                plot_data.append(
                    {
                        "plot_color": "blue",
                        "plot_type": "line",
                        "show_points": True,
                        "plot_points": second_plot_points,
                        "y_axis": "right",
                        "line_style": "solid",
                        "right_axis_title": second_title,
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
                    plot_data.extend(
                        self.get_hline_plot_data(results_range, "ServiceUID")
                    )
                    if self.request.form.get("SecondServiceUID"):
                        plot_data.extend(
                            self.get_hline_plot_data(
                                results_range,
                                "ServiceUID",
                                y_axis="right",
                                plot_color="blue",
                            )
                        )
            self.plot_data = json.dumps(plot_data)
            logger.info("Plot: {}".format(self.plot_data))

        # print("----------------------------------------------------")
        # test_template = self.template()
        # print(test_template)
        # print("----------------------------------------------------")

        tmpl = self.template()
        if self.request.form.get("bika-report-plot"):
            parser = bs4.BeautifulSoup(tmpl, "html.parser")

            chart = bs4.BeautifulSoup(
                self.request.form.get("bika-report-plot"), "html.parser"
            )
            parser.body.insert(len(parser.body.contents), chart)
            tmpl = parser.prettify()

        return {
            "report_title": t(self.headings["header"]),
            "report_data": tmpl,
            "report_parms": self.request.form,
            "plot_data": self.plot_data,
        }

    def get_hline_plot_data(
        self, results_range, service_fieldname, y_axis="left", plot_color="red"
    ):
        plot_data = []
        service = api.get_object(self.request.form.get(service_fieldname))
        an_range = []
        for ar in results_range:
            logger.info(
                "ResultsRange: looking at {} for matching service {}".format(
                    ar["keyword"], service.getKeyword()
                )
            )
            if ar["keyword"] == service.getKeyword():
                an_range.append(ar)
        logger.info(
            "ResultsRange: found {} for service {}".format(
                len(an_range), service.Title()
            )
        )
        if an_range:
            an_range = an_range[0]
            spec_min = an_range.get("min")
            if spec_min:
                plot_data.append(
                    {
                        "plot_color": plot_color,
                        "plot_type": "hline",
                        "y_axis": y_axis,
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
                        "plot_color": plot_color,
                        "plot_type": "hline",
                        "y_axis": y_axis,
                        "show_points": False,
                        "plot_points": [
                            {
                                "y": {"type": "float", "value": spec_max},
                            },
                        ],
                    }
                )
        return plot_data

    def add_filter_by_service(self, query, out_params):
        if not self.request.form.get("ServiceUID", ""):
            return
        query["getServiceUID"] = self.request.form["ServiceUID"]
        service = api.get_object_by_uid(query["getServiceUID"])
        self.headings["analysis"] = service.Title()
        self.headings["analysis_unit"] = service.getUnit()
        # out_params.append(
        #     {"title": _("Analysis"), "value": service.Title(), "type": "text"}
        # )

    def add_filter_by_secondservice(self, query, out_params):
        if not self.request.form.get("SecondServiceUID", ""):
            return
        query["getServiceUID"] = self.request.form["SecondServiceUID"]
        service = api.get_object_by_uid(query["getServiceUID"])
        self.headings["second_analysis"] = service.Title()
        self.headings["second_analysis_unit"] = service.getUnit()
        # # out_params.append(
        # #     {"title": _("Second Analysis"), "value": service.Title(), "type": "text"}
        # # )

    def add_filter_by_specification(self, query, out_params):
        if not self.request.form.get("spec", ""):
            return
        query["getSpecificationUID"] = self.request.form["spec"]
        spec = api.get_object_by_uid(query["getSpecificationUID"])
        if (
            len([param for param in out_params if param["title"] != _("Specification")])
            == 0
        ):
            out_params.append(
                {
                    "title": _("Specification"),
                    "value": spec.Title(),
                    "type": "text",
                }
            )

    def add_filter_by_sampletype(self, query, out_params):
        if not self.request.form.get("SampleTypeUID", ""):
            return
        query["getSampleTypeUID"] = self.request.form["SampleTypeUID"]
        sampletype = api.get_object_by_uid(query["getSampleTypeUID"])
        if (
            len([param for param in out_params if param["title"] == _("Sample Type")])
            == 0
        ):
            out_params.append(
                {
                    "title": _("Sample Type"),
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

    def add_filter_by_samplepoint(self, query, out_params):
        if not self.request.form.get("SamplePointUID", ""):
            return
        query["getSamplePointUID"] = self.request.form["SamplePointUID"]
        sample_point = api.get_object_by_uid(query["getSamplePointUID"])
        if (
            len([param for param in out_params if param["title"] == _("Sample Point")])
            == 0
        ):
            out_params.append(
                {
                    "title": _("Sample Point"),
                    "value": sample_point.Title(),
                    "type": "text",
                }
            )
        self.headings["sample_point"] = sample_point.Title()

    def add_filter_by_instrument(self, query, out_params):
        if not self.request.form.get("getInstrumentUID", ""):
            return
        query["getInstrumentUID"] = self.request.form["getInstrumentUID"]
        instrument = api.get_object_by_uid(query["getInstrumentUID"])
        out_params.append(
            {"title": _("Instrument"), "value": instrument.Title(), "type": "text"}
        )

    def add_filter_by_date_range(self, query, out_params):
        date_query = formatDateQuery(self.context, "DateResultCapture")
        if not date_query:
            return
        query["getResultCaptureDate"] = date_query
        if (
            len([param for param in out_params if param["title"] == _("Analyized")])
            == 0
        ):
            out_params.append(
                {
                    "title": _("Analyized"),
                    "value": formatDateParms(self.context, "DateResultCapture"),
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
