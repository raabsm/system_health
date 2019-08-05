**System Health & Monitoring**

Here is a scalable dashboard created in order to streamline the monitoring of both the health of VOOM's software 
infrastructure and the growth of their company.

Python web framework: **Tornado**.
Method of making API queries and to construct the relevant dashboard elements: **JavaScript**.
Information was pulled from SkyWatch's **Azure database** and from their **ELK stack**.

The design of the site was based on the [Light Bootstrap Dashboard template](https://demos.creative-tim.com/light-bootstrap-dashboard/).


Most of the front end work is handled in the JavaScript file named "dashboard.js" (File path: 
_\systemmonitor\system_health\assets\js\dashboard.js_). 
The file is split into 3 sections: 
(1) Meta Widgets, 
(2) Ping Widgets, 
(3) Graphs.

**To add a row, to add widgets, to change size of divs, etc:**
The HTML file will have to be hardcoded such that there is a new div of _class_ "row" and _id_ of your choosing.
When adding new widgets, depending on the content, take a look at the python file "monitor.py".
This is where the backend is being handled; i.e. accessing databases, managing information, etc.
Each topic has its own handler:
- ProfilesHandler
- GraphHandler
- PoliciesHandler
- RevenueHandler
- ApiHandler
- ErrorLogsHandler

If the widget you want to add falls under any of these topics, then it suffices to modify the code under each class
accordingly.

You might want to modify the front end. As previously mentioned, the js file is split into three sections. It is 
up to you to gauge within which section the widget should be formatted. NB: once you create a function that returns the
widget, be sure to set a time interval so that the information self-refreshes.

There are a number of methods already set up which might be useful:

- fill_counter_widget
- fill_error_widget
- add_timestamp
- a number of graphing methods in list "demo" (e.g. initDashboardPageCharts)







