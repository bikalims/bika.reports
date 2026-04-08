## senaite.crms

### Overview

`bika.reports` extends **Senaite** (the modern core of Bika LIMS) with 

Management Reports were discontinued in favour of Senaite DataBox and Python 3, but proves difficult to use for first-timers. We are bringing back the old reports and adding some new ones, using DataBox's query engine

At the time of writing, only a few legacy reports are available, ugly as sin

The first new one, [Analysis results per Sample Point](https://www.bikalims.org/new-manual/management-reports/results-per-sample-point-report-and-graph), which includes graphing was complete recently

### Requirements

- **Senaite** (recommended latest version) or **Ingwe Bika LIMS 4**

### Installation

#### Using Buildout (Classic Plone/Senaite)

Add the following to your `buildout.cfg`:

cfg
[buildout]
eggs =
    ...
    bika.reports

Then run:
Bashbin/buildout

#### Docker (Recommended for Ingwe Bika LIMS 4)

Add bika.reports to your custom add-ons list in the Docker-based Ingwe Bika distribution.

### Manual

[Management Reports](https://www.bikalims.org/new-manual/management-reports)

### License
This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

### Support & Professional Services
[Bika Lab Systems](www.bikalabs.com) offers professional implementation, training, custom development, and support for bika.reports.

Website: [https://www.bikalims.org](https://www.bikalims.org)
Email: info@bikalims.org (or contact Lemoene directly)

Made with ❤️ in Cape Town, South Africa
