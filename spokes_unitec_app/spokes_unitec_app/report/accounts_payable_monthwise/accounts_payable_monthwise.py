

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
    # No Total Row
    # -----------------------------------------------------

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
    Invoice-wise outstanding calculation.

    RECEIVABLE
    ----------
    Invoice  = positive
    Payment  = negative

    Example:

        Invoice       +100
        Payment        -60
        -----------------
        Outstanding    40


    PAYABLE
    -------
    Invoice  = negative
    Payment  = positive

    Example:

        Invoice       -100
        Payment        +60
        -----------------
        Balance       -40

    For Payable we reverse the sign so the report
    displays 40 as outstanding.

    IMPORTANT:
    -----------
    Payment is NOT shown in the payment month.

    Instead, the final outstanding is assigned to
    the ORIGINAL INVOICE MONTH.

    Example:

        September Purchase Invoice = 58
        November Payment            = 58

        September = 0
        October    = 0
        November   = 0
    """

    party_type = (
        "Customer"
        if account_type == "Receivable"
        else "Supplier"
    )

    invoice_type = (
        "Sales Invoice"
        if account_type == "Receivable"
        else "Purchase Invoice"
    )

    result = {}

    # =====================================================
    # FISCAL YEAR DATE RANGE
    # =====================================================

    fy_start_date = months[0]["start_date"]

    fy_end_date = months[-1]["end_date"]

    # =====================================================
    # PARTY FILTER
    # =====================================================

    party_filter = None

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

        party_filter = parties

    # =====================================================
    # 1. GET INVOICES CREATED IN FY
    # =====================================================

    invoice_conditions = {

        "company": filters.company,

        "account_type": account_type,

        "party_type": party_type,

        "voucher_type": invoice_type,

        "posting_date": [
            "between",
            [
                fy_start_date,
                fy_end_date
            ]
        ],

        "delinked": 0
    }

    if party_filter:

        invoice_conditions["party"] = [
            "in",
            party_filter
        ]

    invoice_rows = frappe.db.get_all(

        "Payment Ledger Entry",

        filters=invoice_conditions,

        fields=[
            "voucher_no",
            "posting_date",
            "party",
            "party_type"
        ],

        order_by="posting_date asc"
    )

    if not invoice_rows:

        return result

    # =====================================================
    # 2. UNIQUE INVOICE NUMBERS
    # =====================================================

    invoice_names = list({

        row.voucher_no

        for row in invoice_rows

        if row.voucher_no
    })

    if not invoice_names:

        return result

    # =====================================================
    # 3. GET ALL PLE ENTRIES FOR THESE INVOICES
    # =====================================================
    #
    # IMPORTANT:
    #
    # Do NOT filter posting_date here.
    #
    # Because payment can happen in a later month.
    #
    # Example:
    #
    # Invoice    = September
    # Payment    = November
    #
    # November payment must clear September invoice.
    #
    # =====================================================

    linked_rows = frappe.db.sql(
        """
        SELECT

            name,

            posting_date,

            voucher_type,

            voucher_no,

            against_voucher_type,

            against_voucher_no,

            account_type,

            party_type,

            party,

            amount,

            delinked

        FROM `tabPayment Ledger Entry`

        WHERE

            company = %(company)s

            AND account_type = %(account_type)s

            AND party_type = %(party_type)s

            AND delinked = 0

            AND
            (
                (
                    voucher_type = %(invoice_type)s

                    AND voucher_no IN %(invoice_names)s
                )

                OR

                (
                    against_voucher_type = %(invoice_type)s

                    AND against_voucher_no IN %(invoice_names)s
                )
            )

        ORDER BY
            posting_date,
            creation
        """,

        {
            "company": filters.company,

            "account_type": account_type,

            "party_type": party_type,

            "invoice_type": invoice_type,

            "invoice_names": tuple(invoice_names)
        },

        as_dict=True
    )

    # =====================================================
    # 4. CALCULATE NET BALANCE FOR EACH INVOICE
    # =====================================================

    invoice_balance = {}

    invoice_party = {}

    for row in linked_rows:

        invoice_name = None

        # -------------------------------------------------
        # Payment / adjustment against invoice
        # -------------------------------------------------

        if (
            row.against_voucher_type == invoice_type

            and row.against_voucher_no in invoice_names
        ):

            invoice_name = (
                row.against_voucher_no
            )

        # -------------------------------------------------
        # Invoice's own PLE
        # -------------------------------------------------

        elif (
            row.voucher_type == invoice_type

            and row.voucher_no in invoice_names
        ):

            invoice_name = (
                row.voucher_no
            )

        if not invoice_name:

            continue

        # -------------------------------------------------
        # Initialize
        # -------------------------------------------------

        invoice_balance.setdefault(
            invoice_name,
            0
        )

        # -------------------------------------------------
        # Add PLE amount
        # -------------------------------------------------

        invoice_balance[
            invoice_name
        ] += flt(
            row.amount
        )

        # -------------------------------------------------
        # Store party
        # -------------------------------------------------

        if row.party:

            invoice_party[
                invoice_name
            ] = {

                "party": row.party,

                "party_type": row.party_type
            }

    # =====================================================
    # 5. PROCESS EACH ORIGINAL INVOICE
    # =====================================================

    processed_invoices = set()

    for invoice in invoice_rows:

        invoice_name = invoice.voucher_no

        # -------------------------------------------------
        # Avoid duplicate processing
        # -------------------------------------------------

        if invoice_name in processed_invoices:

            continue

        processed_invoices.add(
            invoice_name
        )

        # -------------------------------------------------
        # Get final net balance
        # -------------------------------------------------

        net_balance = flt(
            invoice_balance.get(
                invoice_name,
                0
            )
        )

        # -------------------------------------------------
        # Convert to displayed outstanding
        # -------------------------------------------------

        if account_type == "Receivable":

            # Receivable:
            #
            # Invoice +100
            # Payment -100
            #
            # = 0

            outstanding = net_balance

        else:

            # Payable:
            #
            # Invoice -100
            # Payment +100
            #
            # = 0
            #
            # Reverse sign for display.

            outstanding = net_balance

        # -------------------------------------------------
        # Remove tiny rounding difference
        # -------------------------------------------------

        if abs(outstanding) < 0.01:

            outstanding = 0

        # -------------------------------------------------
        # Find original invoice month
        # -------------------------------------------------

        posting_date = getdate(
            invoice.posting_date
        )

        invoice_month = None

        for month in months:

            if (
                month["start_date"]
                <= posting_date
                <= month["end_date"]
            ):

                invoice_month = month

                break

        if not invoice_month:

            continue

        # -------------------------------------------------
        # Party
        # -------------------------------------------------

        party = invoice.party

        if not party:

            continue

        key = (
            party_type,
            party
        )

        # -------------------------------------------------
        # Create party row
        # -------------------------------------------------

        if key not in result:

            result[key] = frappe._dict({

                "party_type": party_type,

                "party": party,

                "party_name": get_party_name(
                    party_type,
                    party
                )
            })

            # Initialize all months

            for month in months:

                result[key][
                    f"{month['fieldname']}_outstanding"
                ] = 0

            result[key][
                "total_outstanding"
            ] = 0

        # -------------------------------------------------
        # Add balance to ORIGINAL invoice month
        # -------------------------------------------------

        fieldname = invoice_month[
            "fieldname"
        ]

        result[key][
            f"{fieldname}_outstanding"
        ] += flt(
            outstanding
        )

    # =====================================================
    # 6. ROUND VALUES
    # =====================================================

    for key, row in result.items():

        for month in months:

            fieldname = month[
                "fieldname"
            ]

            value = flt(
                row.get(
                    f"{fieldname}_outstanding",
                    0
                )
            )

            if abs(value) < 0.01:

                value = 0

            row[
                f"{fieldname}_outstanding"
            ] = value

    # =====================================================
    # 7. TOTAL OUTSTANDING
    # =====================================================

    for key, row in result.items():

        row[
            "total_outstanding"
        ] = flt(
            sum(
                flt(
                    row.get(
                        f"{month['fieldname']}_outstanding",
                        0
                    )
                )

                for month in months
            )
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

    # -----------------------------------------------------
    # Customer
    # -----------------------------------------------------

    if party_type == "Customer":

        return (
            frappe.db.get_value(
                "Customer",
                party,
                "customer_name"
            )
            or party
        )

    # -----------------------------------------------------
    # Supplier
    # -----------------------------------------------------

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
                f"{month['short_label']}"
            ),

            "fieldname": (
                f"{month['fieldname']}"
                "_outstanding"
            ),

            "fieldtype": "Currency",

            "width": 140
        })

    # -----------------------------------------------------
    # Total Outstanding
    # -----------------------------------------------------

    columns.append({

        "label": _("Total Outstanding"),

        "fieldname": "total_outstanding",

        "fieldtype": "Currency",

        "width": 160
    })

    return columns
