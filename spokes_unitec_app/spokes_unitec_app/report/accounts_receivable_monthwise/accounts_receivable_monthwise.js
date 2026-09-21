// Copyright (c) 2026, SGT and contributors
// For license information, please see license.txt

frappe.query_reports["Accounts Receivable Monthwise"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},

		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.defaults.get_user_default("fiscal_year"),
			reqd: 1,

    on_change: function () {
        let fiscal_year = frappe.query_report.get_filter_value("fiscal_year");

        if (!fiscal_year) {
            frappe.query_report.set_filter_value("from_date", "");
            frappe.query_report.set_filter_value("to_date", "");
            return;
        }

        frappe.db.get_value(
            "Fiscal Year",
            fiscal_year,
            [
                "year_start_date",
                "year_end_date"
            ],
            function (r) {

                if (r && r.message) {

                    frappe.query_report.set_filter_value(
                        "from_date",
                        r.message.year_start_date
                    );

                    frappe.query_report.set_filter_value(
                        "to_date",
                        r.message.year_end_date
                    );
                }
            }
        );
    }
		},

{
    fieldname: "from_date",
    label: __("From Date"),
    fieldtype: "Date",
    read_only: 1
},
{
    fieldname: "to_date",
    label: __("To Date"),
    fieldtype: "Date",
    read_only: 1
},
		{
			fieldname: "account_type",
			label: __("Account Type"),
			fieldtype: "Select",
			options: "Payable\nReceivable",
			default: "Payable"
		},

		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Select",
			options: "\nSupplier\nCustomer"
		},

		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "MultiSelectList",
			options: "party_type",

			get_data: function(txt) {

				let party_type =
					frappe.query_report.get_filter_value(
						"party_type"
					);

				if (!party_type) {
					return [];
				}

				return frappe.db.get_link_options(
					party_type,
					txt
				);
			}
		}
	],

    onload: function (report) {

        let fiscal_year =
            report.get_filter_value("fiscal_year");

        if (!fiscal_year) {
            return;
        }

        frappe.db.get_value(
            "Fiscal Year",
            fiscal_year,
            [
                "year_start_date",
                "year_end_date"
            ]
        ).then(function (r) {

            if (r.message) {

                report.set_filter_value(
                    "from_date",
                    r.message.year_start_date
                );

                report.set_filter_value(
                    "to_date",
                    r.message.year_end_date
                );
            }
        });
    }
};
