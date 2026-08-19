app_name = "spokes_unitec_app"
app_title = "spokes_unitec_app"
app_publisher = "SGT"
app_description = "spokes_unitec_app"
app_email = "karantkiruba@hotmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

doc_events = {
	"Sales Invoice": {
		"on_submit": "spokes_unitec_app.script.create_internal_purchase_invoice"
	},
	"Delivery Note":{
		"on_submit": "spokes_unitec_app.script.create_internal_purchase_receipt"
	},
	"Transfer Out":{
		"on_submit": "spokes_unitec_app.script.transs_out_submit"
	},
	"Transfer In":{
		"on_submit": "spokes_unitec_app.script.trans_in_submit"
	},
	"Initial Inspection":{
		"on_submit": "spokes_unitec_app.script.create_repack_stock_entry"
	}
}
fixtures = [
	"Custom Field", "Client Script", "Property Setter", "Print Format"]

doctype_js = {
	"Sales Order": "public/js/Fetch_NamingSeries_Onload.js",
	"Purchase Invoice": "public/js/Fetch_NamingSeries_Onload.js",
        "Sales Invoice": "public/js/Fetch_NamingSeries_Onload.js",
	"Purchase Receipt":"public/js/Fetch_NamingSeries_Onload.js",
	"Purchase Order": "public/js/Fetch_NamingSeries_Onload.js",
	"Transfer Out": "public/js/Fetch_NamingSeries_Onload.js",
	"Transfer IN" : "public/js/Fetch_NamingSeries_Onload.js",
        "Delivery Note": "public/js/Fetch_NamingSeries_Onload.js",
	"Work Order": "public/js/Fetch_NamingSeries_Onload.js",
	"Material Request": "public/js/Fetch_NamingSeries_Onload.js"
}
# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "spokes_unitec_app",
# 		"logo": "/assets/spokes_unitec_app/logo.png",
# 		"title": "spokes_unitec_app",
# 		"route": "/spokes_unitec_app",
# 		"has_permission": "spokes_unitec_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/spokes_unitec_app/css/spokes_unitec_app.css"
# app_include_js = "/assets/spokes_unitec_app/js/spokes_unitec_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/spokes_unitec_app/css/spokes_unitec_app.css"
# web_include_js = "/assets/spokes_unitec_app/js/spokes_unitec_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "spokes_unitec_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "spokes_unitec_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "spokes_unitec_app.utils.jinja_methods",
# 	"filters": "spokes_unitec_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "spokes_unitec_app.install.before_install"
# after_install = "spokes_unitec_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "spokes_unitec_app.uninstall.before_uninstall"
# after_uninstall = "spokes_unitec_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "spokes_unitec_app.utils.before_app_install"
# after_app_install = "spokes_unitec_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "spokes_unitec_app.utils.before_app_uninstall"
# after_app_uninstall = "spokes_unitec_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "spokes_unitec_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"spokes_unitec_app.tasks.all"
# 	],
# 	"daily": [
# 		"spokes_unitec_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"spokes_unitec_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"spokes_unitec_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"spokes_unitec_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "spokes_unitec_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "spokes_unitec_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "spokes_unitec_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["spokes_unitec_app.utils.before_request"]
# after_request = ["spokes_unitec_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["spokes_unitec_app.utils.before_job"]
# after_job = ["spokes_unitec_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"spokes_unitec_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

