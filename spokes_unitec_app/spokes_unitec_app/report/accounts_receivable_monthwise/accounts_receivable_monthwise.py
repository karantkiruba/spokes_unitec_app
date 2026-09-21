

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from frappe import _
from frappe.utils import getdate, add_to_date, get_last_day, flt


# =========================================================
# EXECUTE
# =========================================================

def execute(filters=None):

	filters = frappe._dict(filters or {})

	validate_filters(filters)

	# -----------------------------------------------------
	# Get Fiscal Year
	# -----------------------------------------------------

	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		filters.fiscal_year,
		[
			"year_start_date",
			"year_end_date"
		],
		as_dict=True
	)

	if not fiscal_year:
		frappe.throw(
			_("Fiscal Year {0} not found").format(
				filters.fiscal_year
			)
		)

	# -----------------------------------------------------
	# Generate FY months
	# -----------------------------------------------------

	months = get_fiscal_year_months(
		fiscal_year.year_start_date,
		fiscal_year.year_end_date
	)

	# -----------------------------------------------------
	# Columns
	# -----------------------------------------------------

	columns = get_columns(months)

	# -----------------------------------------------------
	# Data
	# -----------------------------------------------------

	data = get_data(
		filters,
		months
	)

	return columns, data


# =========================================================
# VALIDATE FILTERS
# =========================================================

def validate_filters(filters):

	if not filters.get("company"):
		frappe.throw(
			_("Company is mandatory")
		)

	if not filters.get("fiscal_year"):
		frappe.throw(
			_("Fiscal Year is mandatory")
		)

	if not frappe.db.exists(
		"Fiscal Year",
		filters.fiscal_year
	):
		frappe.throw(
			_("Invalid Fiscal Year: {0}").format(
				filters.fiscal_year
			)
	)


# =========================================================
# FISCAL YEAR MONTHS
# =========================================================

def get_fiscal_year_months(
	start_date,
	end_date
):

	start_date = getdate(start_date)
	end_date = getdate(end_date)

	months = []

	current_date = start_date

	while current_date <= end_date:

		month_end = get_last_day(
			current_date
		)

		if month_end > end_date:
			month_end = end_date

		months.append({
			"label": current_date.strftime("%B"),
			"short_label": current_date.strftime("%b"),
			"fieldname": current_date.strftime("%b").lower(),
			"start_date": current_date,
			"end_date": month_end
		})

		current_date = getdate(
			add_to_date(
				current_date,
				months=1,
				as_string=True
			)
		)

	return months


# =========================================================
# GET DATA
# =========================================================

def get_data(
	filters,
	months
):

	account_type = (
		filters.get("account_type")
		or "Both"
	)

	account_types = []

	if account_type in (
		"Both",
		"Receivable"
	):

		account_types.append(
			"Receivable"
		)

	if account_type in (
		"Both",
		"Payable"
	):

		account_types.append(
			"Payable"
		)

	final_data = {}

	# -----------------------------------------------------
	# Receivable / Payable
	# -----------------------------------------------------

	for current_account_type in account_types:

		party_data = get_monthly_ledger_amount(
			filters,
			months,
			current_account_type
		)

		for key, row in party_data.items():

			if key not in final_data:

				final_data[key] = frappe._dict({
					"party_type": row.party_type,
					"party": row.party,
					"party_name": row.party_name
				})

			# ---------------------------------------------
			# Monthly outstanding
			# ---------------------------------------------

			for month in months:

				fieldname = month["fieldname"]

				final_data[key][
					f"{fieldname}_outstanding"
				] = flt(
					row.get(
						f"{fieldname}_outstanding",
						0
					)
				)

			# ---------------------------------------------
			# FY Total
			# ---------------------------------------------

			final_data[key][
				"total_outstanding"
			] = flt(
				row.get(
					"total_outstanding",
					0
				)
			)

	# -----------------------------------------------------
	# Convert dictionary to list
	# -----------------------------------------------------

	data = list(
		final_data.values()
	)

	# -----------------------------------------------------
	# Sort
	# -----------------------------------------------------

	data.sort(
		key=lambda row: (
			row.get("party_type") or "",
			row.get("party") or ""
		)
	)

	# -----------------------------------------------------
	# Total Row
	# -----------------------------------------------------

	#total_row = frappe._dict({
	#	"party_type": _("Total"),
	#	"party": "",
	#	"party_name": ""
	#})

	#for month in months:

	#	fieldname = month["fieldname"]

	#	total_row[
	#		f"{fieldname}_outstanding"
	#	] = sum(
	#		flt(
	#			row.get(
	#				f"{fieldname}_outstanding",
	#				0
	#			)
	#		)
	#		for row in data
	#	)

	# -----------------------------------------------------
	# Total Outstanding
	# -----------------------------------------------------

	#total_row[
	#	"total_outstanding"
	#] = sum(
	#	flt(
	#		row.get(
	#			"total_outstanding",
	#			0
	#		)
	#	)
	#	for row in data
	#)

	#data.append(
	#	total_row
	#)

	return data


# =========================================================
# MONTHLY PAYMENT LEDGER AMOUNT
# =========================================================

def get_monthly_ledger_amount(
	filters,
	months,
	account_type
):

	"""
	Receivable:

	Invoice amount = positive
	Payment amount = negative

	Therefore:

	Monthly Outstanding =
	SUM(Payment Ledger Entry.amount)


	Payable:

	Invoice amount = negative
	Payment amount = positive

	Therefore we multiply by -1 so that:

	Monthly Outstanding =
	Invoice - Payment
	"""

	party_type = (
		"Customer"
		if account_type == "Receivable"
		else
		"Supplier"
	)

	result = {}

	# =====================================================
	# PROCESS MONTH BY MONTH
	# =====================================================

	for month in months:

		conditions = {
			"company": filters.company,
			"account_type": account_type,
			"party_type": party_type,
			"posting_date": [
				"between",
				[
					month["start_date"],
					month["end_date"]
				]
			],
			"delinked": 0
		}

		# -------------------------------------------------
		# Party filter
		# -------------------------------------------------

		if filters.get("party"):

			parties = filters.party

			if isinstance(parties, str):

				try:
					parties = frappe.parse_json(
						parties
					)
				except Exception:
					parties = [
						parties
					]

			conditions["party"] = [
				"in",
				parties
			]

		# -------------------------------------------------
		# Query Payment Ledger
		# -------------------------------------------------

		rows = frappe.db.get_all(
			"Payment Ledger Entry",

			filters=conditions,

			fields=[
				"party",
				"party_type",
				"SUM(amount) AS amount"
			],

			group_by="party"
		)

		# -------------------------------------------------
		# Process rows
		# -------------------------------------------------

		for row in rows:

			party = row.get(
				"party"
			)

			if not party:
				continue

			key = (
				party_type,
				party
			)

			# ---------------------------------------------
			# Create party
			# ---------------------------------------------

			if key not in result:

				result[key] = frappe._dict({
					"party_type": party_type,

					"party": party,

					"party_name": get_party_name(
						party_type,
						party
					)
				})

			# ---------------------------------------------
			# Amount
			# ---------------------------------------------

			amount = flt(
				row.get("amount")
			)

			# -------------------------------------------------
			# Receivable
			# -------------------------------------------------

			if account_type == "Receivable":

				monthly_outstanding = amount

			# -------------------------------------------------
			# Payable
			# -------------------------------------------------

			else:

				monthly_outstanding = amount

			fieldname = month[
				"fieldname"
			]

			result[key][
				f"{fieldname}_outstanding"
			] = flt(
				monthly_outstanding
			)

	# =====================================================
	# FILL ZERO FOR MISSING MONTHS
	# =====================================================

	for key, row in result.items():

		for month in months:

			fieldname = month[
				"fieldname"
			]

			row.setdefault(
				f"{fieldname}_outstanding",
				0
			)

	# =====================================================
	# FY TOTAL
	# =====================================================

	for key, row in result.items():

		row[
			"total_outstanding"
		] = sum(
			flt(
				row.get(
					f"{month['fieldname']}_outstanding",
					0
				)
			)
			for month in months
		)

	return result


# =========================================================
# PARTY NAME
# =========================================================

def get_party_name(
	party_type,
	party
):

	if not party:
		return ""

	if party_type == "Customer":

		return (
			frappe.db.get_value(
				"Customer",
				party,
				"customer_name"
			)
			or party
		)

	if party_type == "Supplier":

		return (
			frappe.db.get_value(
				"Supplier",
				party,
				"supplier_name"
			)
			or party
		)

	return party


# =========================================================
# COLUMNS
# =========================================================

def get_columns(months):

	columns = []

	# -----------------------------------------------------
	# Party Type
	# -----------------------------------------------------

	columns.append({
		"label": _("Party Type"),
		"fieldname": "party_type",
		"fieldtype": "Data",
		"width": 100
	})

	# -----------------------------------------------------
	# Party
	# -----------------------------------------------------

	columns.append({
		"label": _("Party"),
		"fieldname": "party",
		"fieldtype": "Dynamic Link",
		"options": "party_type",
		"width": 160
	})

	# -----------------------------------------------------
	# Party Name
	# -----------------------------------------------------

	columns.append({
		"label": _("Party Name"),
		"fieldname": "party_name",
		"fieldtype": "Data",
		"width": 220
	})

	# -----------------------------------------------------
	# Monthly Outstanding
	# -----------------------------------------------------

	for month in months:

		columns.append({
			"label": _(
				f"{month['short_label']} Outstanding"
			),

			"fieldname": (
				f"{month['fieldname']}"
				"_outstanding"
			),

			"fieldtype": "Currency",

			"width": 140
		})

	columns.append({
		"label": _("Total Outstanding"),

		"fieldname": "total_outstanding",

		"fieldtype": "Currency",

		"width": 160
	})

	return columns
