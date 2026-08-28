

import frappe

@frappe.whitelist()
def get_series_for_doctypeedit(doctype):
	naming_series = frappe.get_meta(doctype).get_field("naming_series").options or ""
	naming_series= naming_series.split("\n")
	return naming_series


@frappe.whitelist()
def get_series_for_doctype(doctype,currentdoctype,username=None):
	series=[];
	if frappe.get_meta(doctype).get_field("naming_series"):
		naming_series = frappe.get_meta(doctype).get_field("naming_series").options or ""
		name=''
		if currentdoctype == 'Naming Series Manager':
			name=frappe.get_value('Naming Series Manager',{"allow": doctype,"username": username });
		if currentdoctype == 'Naming Series Definition':
			name=frappe.get_value('Naming Series Definition',{"allow":doctype});
		if name:
			series.append({'name': name})
			return series
		elif naming_series:
			seriesname= naming_series.split("\n")
			series.append({'seriesname':seriesname})
			return series
	else:
		return None

@frappe.whitelist()
def set_anotherdoctype_fieldvalue(doctype,docname,fieldname, fieldvalue):
    frappe.db.set_value(doctype, docname, fieldname, fieldvalue)


@frappe.whitelist()
def get_series_definition_list(doctype):
	definition_list = frappe.db.sql("""
                select *
                from `tabSeries List Definition` so
                where so.parent = %(doctype)s
                """.format(doctype =doctype), {
                        "doctype": doctype
                }, as_dict=1)
	return definition_list
