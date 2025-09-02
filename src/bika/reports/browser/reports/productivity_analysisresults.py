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
from senaite.core.catalog import ANALYSIS_CATALOG
from bika.lims.utils import formatDateQuery, formatDateParms, logged_in_client
from bika.lims.utils import get_link
from plone.app.layout.globals.interfaces import IViewView
from senaite.core.i18n import translate as t
from senaite.core import logger
from zope.interface import implements


class Report(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile(
        "templates/productivity_analysisresults.pt"
    )

    def __init__(self, context, request, report=None):
        BrowserView.__init__(self, context, request)
        self.report = report
        self.date = DateTime.DateTime()
        today = self.date.strftime("%Y-%m-%d %H:%M")
        username = (
            self.context.portal_membership.getAuthenticatedMember().getUserName()
        )
        self.headings = {
            "header": _("Analysis Results"),
            "subheader": _("Created on {} by {}".format(today, username)),
            "paramheader": "",
            "analysis": "",
            "analysis_unit": "",
            "second_analysis": "",
            "second_analysis_unit": "",
            "sample_point": "",
        }
        self.formats = {
            "columns": 7,
            "col_heads": [
                _("Analysis"),
                _("Date"),
                _("Result"),
                _("Sample ID"),
                _("Batch ID"),
                _("Client Batch ID"),
            ],
            "class": "",
        }
        self.plot_enabled = True
        self.analysis_color = "red"
        self.second_analysis_color = "blue"
        self.ldl_color = "brown"
        self.udl_color = "brown"
        self.second_ldl_color = "green"
        self.second_udl_color = "green"
        self.specification_color = "black"

    def __call__(self):
        parms = []
        query = dict(
            portal_type="Analysis",
            sort_on="getResultCaptureDate",
            sort_order="ascending",
        )
        # Filter by Client
        self.add_filter_by_client(query=query, out_params=parms)

        # Filter by Service UID
        self.add_filter_by_service(query=query, out_params=parms)

        # Filter by Specification UID
        spec_range = None
        if self.request.form.get("analysis_spec", ""):
            # get specification for analaysis
            # find upper and lower limits
            # create hlines for them
            # append to plot_data
            analysis_spec = api.get_object(
                self.request.form.get("analysis_spec")
            )
            results_range = analysis_spec.getResultsRange()
            spec_range = self.get_spec_range(results_range, "ServiceUID")
            # self.add_filter_by_specification(query=query, out_params=parms)

        # Filter by SamplePoint
        self.add_filter_by_samplepoint(query=query, out_params=parms)

        # # Filter by Analyst
        # self.add_filter_by_analyst(query=query, out_params=parms)

        # Filter by date range
        self.add_filter_by_date_range(query=query, out_params=parms)

        # Filter by SampleType
        self.add_filter_by_sampletype(query=query, out_params=parms)

        # Get lower and upper liimits
        service = api.get_object_by_uid(self.request.form["ServiceUID"])
        plot_ldl_line = False
        plot_ldl_value = service.getLowerDetectionLimit()
        plot_udl_line = False
        plot_udl_value = service.getUpperDetectionLimit()

        # Fetch the data
        data_lines = []
        total_count = 0
        logger.info("Select analysis-results query: {}".format(query))
        analyses = api.search(query, ANALYSIS_CATALOG)
        logger.info(
            "Select analysis-results found {} results".format(len(analyses))
        )
        plot_points = []
        for analysis in analyses:
            analysis = api.get_object(analysis)
            if not analysis.getResult():
                continue

            # Links
            link_style = "color:{}".format(self.analysis_color)
            analysis_link = self.get_styled_link(
                analysis.absolute_url(), analysis.Title(), link_style
            )

            sample = analysis.aq_parent
            sample_link = self.get_styled_link(
                sample.absolute_url(), sample.Title(), link_style
            )

            batch_id_link = ""
            client_batch_id_link = ""
            if analysis.aq_parent.getBatch():
                batch = analysis.aq_parent.getBatch()
                batch_id_link = self.get_styled_link(
                    batch.absolute_url(), batch.getId(), link_style
                )
                if batch.getClientBatchID():
                    client_batch_id_link = self.get_styled_link(
                        batch.absolute_url(),
                        batch.getClientBatchID(),
                        link_style,
                    )

            # plot limit line if outside limits
            bare_value = analysis.getResult()
            if plot_ldl_value:
                if float(bare_value) < float(plot_ldl_value):
                    plot_ldl_line = True
            if plot_udl_value:
                if float(bare_value) > float(plot_udl_value):
                    plot_udl_line = True

            data_point = [
                {
                    "value": analysis_link,
                    "class": "text",
                },
                {
                    "value": str(analysis.getResultCaptureDate())[:16],
                    "class": "date",
                },
                {
                    "value": analysis.getFormattedResult(),
                    "bare_value": bare_value,
                    "class": "text",
                    "style": "text-align:right",
                },
                {
                    "value": sample_link,
                    "class": "text",
                },
                {
                    "value": batch_id_link,
                    "class": "text",
                },
                {
                    "value": client_batch_id_link,
                    "class": "text",
                },
            ]
            data_lines.append(data_point)
            plot_points.append({"x": data_point[1], "y": data_point[2]})
            total_count += 1

        # Get lower and upper liimits
        second_plot_ldl_line = False
        second_plot_udl_line = False
        if self.request.form.get("SecondServiceUID"):
            secondary_service = api.get_object_by_uid(
                self.request.form["SecondServiceUID"]
            )
            second_plot_ldl_value = secondary_service.getLowerDetectionLimit()
            second_plot_udl_value = secondary_service.getUpperDetectionLimit()

        second_plot_points = []
        if self.request.form.get("SecondServiceUID"):
            query = dict(
                portal_type="Analysis",
                sort_on="getResultCaptureDate",
                sort_order="ascending",
            )
            # Filter by Client
            self.add_filter_by_client(query=query, out_params=parms)

            # filter by Secondary Service UID
            self.add_filter_by_secondservice(query=query, out_params=parms)

            # Filter by SamplePoint
            self.add_filter_by_samplepoint(query=query, out_params=parms)

            # filter by specification uid
            # self.add_filter_by_specification(query=query, out_params=parms)

            #  # filter by analyst
            #  self.add_filter_by_analyst(query=query, out_params=parms)

            # filter by date range
            self.add_filter_by_date_range(query=query, out_params=parms)

            # Filter by SampleType
            self.add_filter_by_sampletype(query=query, out_params=parms)

            # Get limts from Analysis Service
            # Fetch the data
            logger.info("Select analysis-results query: {}".format(query))
            analyses = api.search(query, ANALYSIS_CATALOG)
            logger.info(
                "Select analysis-results found {} results".format(
                    len(analyses)
                )
            )
            for analysis in analyses:
                analysis = api.get_object(analysis)
                if not analysis.getResult():
                    continue

                # Links
                link_style = "color:{}".format(self.second_analysis_color)
                analysis_link = self.get_styled_link(
                    analysis.absolute_url(), analysis.Title(), link_style
                )

                sample = analysis.aq_parent
                sample_link = self.get_styled_link(
                    sample.absolute_url(), sample.Title(), link_style
                )

                batch_id_link = ""
                client_batch_id_link = ""
                if analysis.aq_parent.getBatch():
                    batch = analysis.aq_parent.getBatch()
                    batch_id_link = self.get_styled_link(
                        batch.absolute_url(), batch.getId(), link_style
                    )
                    if batch.getClientBatchID():
                        client_batch_id_link = self.get_styled_link(
                            batch.absolute_url(),
                            batch.getClientBatchID(),
                            link_style,
                        )

                # plot limit line if outside limits
                second_bare_value = analysis.getResult()
                if second_plot_ldl_value:
                    if float(second_bare_value) < float(second_plot_ldl_value):
                        second_plot_ldl_line = True
                if second_plot_udl_value:
                    if float(second_bare_value) > float(second_plot_udl_value):
                        second_plot_udl_line = True

                data_point = [
                    {
                        "value": analysis_link,
                        "class": "text",
                    },
                    {
                        "value": str(analysis.getResultCaptureDate())[:16],
                        "class": "date",
                    },
                    {
                        "value": analysis.getFormattedResult(),
                        "bare_value": second_bare_value,
                        "class": "text",
                        "style": "text-align:right",
                    },
                    {
                        "value": sample_link,
                        "class": "text",
                    },
                    {
                        "value": batch_id_link,
                        "class": "text",
                    },
                    {
                        "value": client_batch_id_link,
                        "class": "text",
                    },
                ]
                data_lines.append(data_point)
                second_plot_points.append(
                    {"x": data_point[1], "y": data_point[2]}
                )
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
        self.headings["header"] = heading

        # # ParamHeading
        # param_heading = ""
        # if self.headings["analysis"]:
        #     param_heading += " {} {}".format(
        #         self.headings["analysis"], self.headings["analysis_unit"]
        #     )
        # if self.headings["second_analysis"]:
        #     param_heading += ", {} {}".format(
        #         self.headings["second_analysis"], self.headings["second_analysis_unit"]
        #     )
        # self.headings["paramheader"] = param_heading
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
                    "plot_color": self.analysis_color,
                    "plot_type": "line",
                    "show_points": True,
                    "plot_points": plot_points,
                    "y_axis": "left",
                    "line_style": "solid",
                    "left_axis_title": title,
                    "legend_label": title,
                }
            ]
            if plot_ldl_line:
                plot_data.append(
                    self.get_hline_plot_data(
                        plot_ldl_value,
                        title="{} LDL".format(title),
                        y_axis="left",
                        plot_color=self.ldl_color,
                        line_style="dashed",
                    )
                )
            if plot_udl_line:
                plot_data.append(
                    self.get_hline_plot_data(
                        plot_udl_value,
                        title="{} UDL".format(title),
                        y_axis="left",
                        plot_color=self.udl_color,
                        line_style="dashed",
                    )
                )
            if len(second_plot_points):
                second_title = api.get_object(
                    self.request.form.get("SecondServiceUID")
                ).title
                plot_data.append(
                    {
                        "plot_color": self.second_analysis_color,
                        "plot_type": "line",
                        "show_points": True,
                        "plot_points": second_plot_points,
                        "y_axis": "right",
                        "line_style": "solid",
                        "right_axis_title": second_title,
                        "legend_label": second_title,
                    }
                )
                if second_plot_ldl_line:
                    plot_data.append(
                        self.get_hline_plot_data(
                            second_plot_ldl_value,
                            title="{} LDL".format(second_title),
                            y_axis="right",
                            plot_color=self.second_ldl_color,
                            line_style="dashed",
                        )
                    )
                if second_plot_udl_line:
                    plot_data.append(
                        self.get_hline_plot_data(
                            second_plot_udl_value,
                            title="{} UDL".format(second_title),
                            y_axis="right",
                            plot_color=self.second_udl_color,
                            line_style="dashed",
                        )
                    )

            if self.request.form.get("analysis_spec", ""):
                # get specification for analaysis
                # find upper and lower limits
                # create hlines for them
                # append to plot_data
                if spec_range:
                    if spec_range.get("min"):
                        plot_data.append(
                            self.get_hline_plot_data(
                                spec_range.get("min"),
                                title="Spec Min",
                                y_axis="left",
                                plot_color=self.analysis_color,
                            )
                        )
                    if spec_range.get("max"):
                        plot_data.append(
                            self.get_hline_plot_data(
                                spec_range.get("max"),
                                title="Spec Max",
                                y_axis="left",
                                plot_color=self.analysis_color,
                            )
                        )
                    if self.request.form.get("SecondServiceUID"):
                        second_spec_range = self.get_spec_range(
                            results_range, "SecondServiceUID"
                        )
                        if second_spec_range.get("min"):
                            plot_data.append(
                                self.get_hline_plot_data(
                                    second_spec_range.get("min"),
                                    title="Spec Min",
                                    y_axis="right",
                                    plot_color=self.second_analysis_color,
                                )
                            )
                        if second_spec_range.get("max"):
                            plot_data.append(
                                self.get_hline_plot_data(
                                    second_spec_range.get("max"),
                                    title="Spec Max",
                                    y_axis="right",
                                    plot_color=self.second_analysis_color,
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

    def get_spec_range(self, results_range, service_fieldname):
        service = api.get_object(self.request.form.get(service_fieldname))
        an_range = []
        for ar in results_range:
            logger.debug(
                "ResultsRange: looking at {} for matching service {}".format(
                    ar["keyword"], service.getKeyword()
                )
            )
            if ar["keyword"] == service.getKeyword():
                an_range.append(ar)
        logger.debug(
            "ResultsRange: found {} for service {}".format(
                len(an_range), service.Title()
            )
        )
        result = {"min": None, "max": None}
        if len(an_range) > 0:
            if an_range[0].get("min"):
                result["min"] = an_range[0].get("min")
            if an_range[0].get("max"):
                result["max"] = an_range[0].get("max")
        return result

    def get_hline_plot_data(
        self,
        val,
        title="dunno",
        y_axis="left",
        plot_color="red",
        line_style="dotted",
    ):
        return {
            "plot_color": plot_color,
            "plot_type": "hline",
            "y_axis": y_axis,
            "show_points": False,
            "line_style": line_style,
            "plot_points": [
                {
                    "y": {"type": "float", "value": val},
                },
            ],
            "legend_label": title,
        }

    def add_filter_by_client(self, query, out_params):
        """Applies the filter by client to the search query"""
        current_client = logged_in_client(self.context)
        if current_client:
            query["getClientUID"] = api.get_uid(current_client)
        elif self.request.form.get("ClientUID", ""):
            query["getClientUID"] = self.request.form["ClientUID"]
            client = api.get_object_by_uid(query["getClientUID"])
            if (
                len(
                    [
                        param
                        for param in out_params
                        if param["title"] != _("Client")
                    ]
                )
                == 0
            ):
                out_params.append(
                    {
                        "title": _("Client"),
                        "value": client.Title(),
                        "type": "text",
                    }
                )

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
        if not self.request.form.get("analysis_spec", ""):
            return
        query["getAnalysisSpecUID"] = self.request.form["analysis_spec"]
        analysis_spec = api.get_object_by_uid(query["getAnalysisSpecUID"])
        if (
            len(
                [
                    param
                    for param in out_params
                    if param["title"] != _("Specification")
                ]
            )
            == 0
        ):
            out_params.append(
                {
                    "title": _("Specification"),
                    "value": analysis_spec.Title(),
                    "type": "text",
                }
            )

    def add_filter_by_sampletype(self, query, out_params):
        if not self.request.form.get("SampleTypeUID", ""):
            return
        query["getSampleTypeUID"] = self.request.form["SampleTypeUID"]
        sampletype = api.get_object_by_uid(query["getSampleTypeUID"])
        if (
            len(
                [
                    param
                    for param in out_params
                    if param["title"] == _("Sample Type")
                ]
            )
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
            len(
                [
                    param
                    for param in out_params
                    if param["title"] == _("Sample Point")
                ]
            )
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
            {
                "title": _("Instrument"),
                "value": instrument.Title(),
                "type": "text",
            }
        )

    def add_filter_by_date_range(self, query, out_params):
        date_query = formatDateQuery(self.context, "DateResultCapture")
        if not date_query:
            return
        query["getResultCaptureDate"] = date_query
        if (
            len(
                [
                    param
                    for param in out_params
                    if param["title"] == _("Analyzed")
                ]
            )
            == 0
        ):
            out_params.append(
                {
                    "title": _("Analyzed"),
                    "value": formatDateParms(
                        self.context, "DateResultCapture"
                    ),
                    "type": "text",
                }
            )

    def generate_csv(self, data_lines):
        fieldnames = [
            "Date",
            "Turnaround time (h)",
        ]
        output = StringIO()
        dw = csv.DictWriter(
            output, extrasaction="ignore", fieldnames=fieldnames
        )
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

    def get_styled_link(self, url, title, style=""):
        """
        Create an html link and apply a style if provided
        NOTE: style may have semi-colons but NO SPACES!!!!
        """
        link = get_link(url, title)
        if style:
            parts = link.split(" ")
            parts.insert(2, 'style="{}"'.format(style))
            link = " ".join(parts)
        logger.info("styled link: {}".format(link))
        return link
