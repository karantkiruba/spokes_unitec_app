import frappe
from frappe import _
from tms.utils import validation as tms_validate

def create_internal_purchase_invoice(doc, method=None):
    if not doc.custom_is_internal_company:
        return

    if not doc.custom_represent_company:
        frappe.throw(_("Please select Represent Company (Supplier)."))

    existing = frappe.db.exists(
        "Purchase Invoice",
        {"custom_sales_invoice": doc.name}
    )

    if existing:
        return

    series_data = get_series_definition(
        "Purchase Invoice",
        doc.custom_represent_warehouse
    )

    pi = frappe.new_doc("Purchase Invoice")
    pi.supplier = doc.custom_represent_company
    pi.company = doc.company
    pi.posting_date = doc.posting_date
    pi.due_date = doc.due_date
    pi.bill_date = doc.posting_date
    pi.bill_no = doc.name
    pi.set_warehouse = doc.custom_represent_warehouse
    pi.update_stock=1
    pi.custom_invoice_no = doc.name

    if series_data:
        pi.billing_address = series_data.get("company_address")
        pi.naming_series = series_data.get("series_name")
        pi.cost_center = series_data.get("cost_center")
        pi.branch = series_data.get("unit_type")
        pi.transfer_out_location = series_data.get("transfer_out_location")
        pi.shipping_address = series_data.get("company_address")

    for d in doc.items:
        pi.append("items", {
            "item_code": d.item_code,
            "item_name": d.item_name,
            "description": d.description,
            "qty": d.qty,
            "uom": d.uom,
            "stock_uom": d.stock_uom,
            "conversion_factor": d.conversion_factor,
            "rate": d.rate,
            "warehouse": doc.custom_represent_warehouse,
            "expense_account": d.expense_account,
            "cost_center": series_data.get("cost_center")
        })
    sup = frappe.db.get_value("Supplier",doc.custom_represent_company,"tax_category")
    if sup:
        purchase_tax_template = frappe.db.get_value("Purchase Taxes and Charges Template",{"tax_category": sup},"name")
        if purchase_tax_template:
            pi.taxes_and_charges = purchase_tax_template

            taxes = frappe.get_all("Purchase Taxes and Charges",filters={"parent": purchase_tax_template},
                fields=["charge_type","account_head","description","rate","row_id"],
                order_by="idx"
            )
            for tax in taxes:
                pi.append("taxes", tax)

    pi.flags.ignore_permissions = True
    pi.insert()
    #pi.submit()

def create_internal_purchase_receipt(doc, method=None):
    if not doc.custom_is_internal_company:
        return

    if not doc.custom_represent_company:
        frappe.throw(_("Please select Represent Company (Supplier)."))

    existing = frappe.db.exists(
        "Purchase Receipt",
        {"custom_delivery_note": doc.name}
    )

    if existing:
        return

    series_data = get_series_definition(
        "Purchase Receipt",
        doc.custom_represent_warehouse
    )

    pi = frappe.new_doc("Purchase Receipt")
    pi.supplier = doc.custom_represent_company
    pi.company = doc.company
    pi.posting_date = doc.posting_date
    pi.supplier_delivery_note = doc.name
    pi.bill_date = doc.posting_date
    pi.bill_no = doc.name
    pi.set_warehouse = doc.custom_represent_warehouse
    #pi.update_stock=1
    pi.custom_delivery_note = doc.name

    if series_data:
        pi.billing_address = series_data.get("company_address")
        pi.naming_series = series_data.get("series_name")
        pi.cost_center = series_data.get("cost_center")
        pi.branch = series_data.get("unit_type")
        pi.transfer_out_location = series_data.get("transfer_out_location")
        pi.shipping_address = series_data.get("company_address")
    for d in doc.items:
        pi.append("items", {
            "item_code": d.item_code,
            "item_name": d.item_name,
            "description": d.description,
            "qty": d.qty,
            "uom": d.uom,
            "stock_uom": d.stock_uom,
            "conversion_factor": d.conversion_factor,
            "rate": d.rate,
            "warehouse": doc.custom_represent_warehouse,
            "expense_account": d.expense_account,
            "cost_center": series_data.get("cost_center")
        })
    sup = frappe.db.get_value("Supplier",doc.custom_represent_company,"tax_category")
    if sup:
        purchase_tax_template = frappe.db.get_value("Purchase Taxes and Charges Template",{"tax_category": sup},"name")
        if purchase_tax_template:
            pi.taxes_and_charges = purchase_tax_template

            taxes = frappe.get_all("Purchase Taxes and Charges",filters={"parent": purchase_tax_template},
                fields=["charge_type","account_head","description","rate","row_id"],
                order_by="idx"
            )
            for tax in taxes:
                pi.append("taxes", tax)

    pi.flags.ignore_permissions = True
    pi.insert()

def get_series_definition(doctype, warehouse):
    if not warehouse:
        return {}

    result = frappe.db.sql("""
        SELECT
            b.series_name,
            b.definition,
            b.unit_type,
            b.source_warehouse,
            b.target_warehouse,
            b.cost_center,
            b.company_address,
            b.transfer_out_location
        FROM `tabNaming Series Definition` a
        INNER JOIN `tabSeries List Definition` b
            ON a.name = b.parent
        WHERE b.source_warehouse = %(warehouse)s
          AND a.allow = %(doctype)s
        LIMIT 1
    """, {
        "warehouse": warehouse,
        "doctype": doctype
    }, as_dict=True)

    return result[0] if result else {}


@frappe.whitelist()
def stock_details_pos(product_code, warehouse):
	date_field = ""
	warehouse_field = ""
	if product_code is not 'a':
		date_field += " BI.item_code = %(product_code)s"
	if warehouse is not 'a':
		warehouse_field += " and BI.warehouse = %(warehouse)s"
	stock = frappe.db.sql("""SELECT
        BI.item_code,
        BI.actual_qty as actual_qty
        FROM `tabBin` BI
        WHERE {0}{1}
        """.format(date_field,warehouse_field), {
        "product_code": product_code,
        "warehouse": warehouse
        }, as_dict=1)
	return stock


@frappe.whitelist()
def transss_out_submit(self, method):
	stock_entry = frappe.new_doc("Stock Entry")
	transfer_in = frappe.new_doc("Transfer In")
	stock_entry.company = self.company
	stock_entry.stock_entry_type = 'Material Transfer'
	stock_entry.add_to_transit = 1
	stock_entry.out_reference_no = self.name
	for dtl in self.items:
		stock_entry.append("items", {
			"s_warehouse": self.set_warehouse,
			"t_warehouse": self.to_warehouse,
			"item_code": dtl.item_code,
			"qty": dtl.qty,
			"uom": dtl.uom,
			"cost_center":dtl.cost_center,
			"allow_zero_valuation_rate": 0
		})
		transfer_in.append("items", {
			"warehouse": self.to_warehouse,
			"item_code": dtl.item_code,
			"quantity": dtl.qty,
			"rate": dtl.rate,
			#"sales_price": dtl.sales_price,
			"item_name": dtl.item_name,
			"uom": dtl.uom
		})
	stock_entry.save()
	stock_entry.submit()
	naming_series = get_namingseriesdetail("Transfer In", self.target_warehouse)
	if not naming_series:
		frappe.throw(
			f"No Naming Series found for Transfer In and Warehouse {self.to_warehouse}"
	)
	transfer_in.naming_series = naming_series[0].series_name
	transfer_in.naming_series_definition = naming_series[0].definition
	transfer_in.company = self.company
	transfer_in.get_from_material_request = self.get_from_material_request
	transfer_in.source_warehouse = self.set_warehouse
	transfer_in.from_branch = self.from_branch
	transfer_in.out_reference_no = self.name
	transfer_in.transfer_out_location = naming_series[0].transfer_out_location
	transfer_in.set_warehouse = self.to_warehouse
	transfer_in.date = self.posting_date
	transfer_in.cost_center = naming_series[0].cost_center
	transfer_in.to_warehouse = naming_series[0].target_warehouse
	transfer_in.flags.ignore_permissions = 1
	transfer_in.total = self.total
	transfer_in.total_qty = self.total_qty
	transfer_in.save()

	if self.get_from_material_request:
		material_request = frappe.get_doc("Material Request", self.get_from_material_request)

		for material_item in self.items:
			if material_item.material_request_item:
				existing_qty = frappe.db.get_value("Material Request Item", material_item.material_request_item, "transfered_qty") or 0

				new_qty = existing_qty + (material_item.qty or 0)
				frappe.db.set_value("Material Request Item",material_item.material_request_item,"transfered_qty",new_qty)


@frappe.whitelist()
def transs_out_submit(self, method):

        stock_entry = frappe.new_doc("Stock Entry")

        stock_entry.company = self.company
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.add_to_transit = 1
        stock_entry.out_reference_no = self.name

        for dtl in self.items:
                stock_entry.append("items", {
                        "s_warehouse": self.set_warehouse,
                        "t_warehouse": self.to_warehouse,
                        "item_code": dtl.item_code,
                        "qty": dtl.qty,
                        "uom": dtl.uom,
                        "cost_center": dtl.cost_center,
                        "allow_zero_valuation_rate": 0,
                        "use_serial_batch_fields":1,
                        "serial_no":dtl.serial_no
                })

        stock_entry.flags.ignore_permissions = 1
        stock_entry.save()
        stock_entry.submit()
        if self.is_tms_regrind == 1:
            create_regrinding_return_from_transfer_out(self)

        if self.is_tms == 1:

                tms_receipt = frappe.new_doc("TMS Tool Receipt")

                tms_receipt.company = self.company
                #tms_receipt.source_warehouse = self.set_warehouse
                tms_receipt.source_warehouse = self.to_warehouse
                tms_receipt.target_warehouse = self.target_warehouse
                tms_receipt.receipt_type = "Head Office Transfer"
                tms_receipt.transfer_reference = self.name
                tms_receipt.receipt_date = self.posting_date
                tms_receipt.posting_date = self.posting_date
                tms_receipt.transfer_out_location = self.to_branch
                for dtl in self.items:

                        tms_receipt.append("items", {
                                "item_code": dtl.item_code,
                                "item_name": dtl.item_name,
                                "condition": "New",
                                "qty": dtl.qty,
                                "rate": dtl.rate,
                                "amount": (dtl.qty or 0) * (dtl.rate or 0),
                                "uom": dtl.uom,
                                "serial_no":dtl.serial_no,
                        })

                tms_receipt.flags.ignore_permissions = 1
                tms_receipt.insert()

        else:


                transfer_in = frappe.new_doc("Transfer In")

                for dtl in self.items:
                        transfer_in.append("items", {
                                "warehouse": self.to_warehouse,
                                "item_code": dtl.item_code,
                                "quantity": dtl.qty,
                                "rate": dtl.rate,
                                "item_name": dtl.item_name,
                                "uom": dtl.uom
                        })

                naming_series = get_namingseriesdetail(
                        "Transfer In",
                        self.target_warehouse
                )

                if not naming_series:
                        frappe.throw(
                                f"No Naming Series found for Transfer In and Warehouse {self.to_warehouse}"
                        )

                transfer_in.naming_series = naming_series[0].series_name
                transfer_in.naming_series_definition = naming_series[0].definition

                transfer_in.company = self.company
                transfer_in.get_from_material_request = self.get_from_material_request
                transfer_in.source_warehouse = self.set_warehouse
                transfer_in.from_branch = self.from_branch
                transfer_in.out_reference_no = self.name
                transfer_in.transfer_out_location = naming_series[0].transfer_out_location
                transfer_in.set_warehouse = self.to_warehouse
                transfer_in.date = self.posting_date
                transfer_in.cost_center = naming_series[0].cost_center
                transfer_in.to_warehouse = naming_series[0].target_warehouse

                transfer_in.flags.ignore_permissions = 1

                transfer_in.total = self.total
                transfer_in.total_qty = self.total_qty

                transfer_in.save()

        if self.get_from_material_request:

                material_request = frappe.get_doc(
                        "Material Request",
                        self.get_from_material_request
                )

                for material_item in self.items:

                        if material_item.material_request_item:

                                existing_qty = frappe.db.get_value(
                                        "Material Request Item",
                                        material_item.material_request_item,
                                        "transfered_qty"
                                ) or 0

                                new_qty = existing_qty + (material_item.qty or 0)

                                frappe.db.set_value(
                                        "Material Request Item",
                                        material_item.material_request_item,
                                        "transfered_qty",
                                        new_qty
                                )

def create_regrinding_return_from_transfer_out(self):

    if frappe.db.exists(
        "TMS Regrinding Return",
        {"transfer_reference": self.name}
    ):
        return

    regrind_return = frappe.new_doc("TMS Regrinding Return")

    regrind_return.company = self.company
    #regrind_return.tms_location = self.tms_location
    #regrind_return.customer = self.customer

    regrind_return.posting_date = self.posting_date
    regrind_return.dispatch_date = self.posting_date

    regrind_return.skip_stock_entry = 1

    regrind_return.transfer_out = self.name

    # Target warehouse for Head Office
    regrind_return.target_warehouse = self.target_warehouse
    regrind_return.source_warehouse = self.set_warehouse

    for dtl in self.items:

        info = tms_validate.get_item_tool_info(dtl.item_code)

        regrind_return.append("items", {
            "item_code": dtl.item_code,
            "qty": dtl.qty,
            "uom": dtl.uom,

            "serial_no": dtl.serial_no,

            "physical_tool_code": info.get("tms_physical_tool_code"),

            "tms_tool_registration": info.get(
                "custom_tms_tool_registration"
            ),

            "tool_type": info.get("tms_tool_type"),

            "cpc_component_last_used": getattr(
                dtl,
                "cpc_component_last_used",
                None
            ),
        })

    regrind_return.flags.ignore_permissions = True
    regrind_return.insert(ignore_permissions=True)
    regrind_return.submit()

    return regrind_return.name

@frappe.whitelist()
def get_namingseriesdetail(doctype, target_warehouse=None):
    return frappe.db.sql("""
        SELECT 
            b.series_name,
            b.definition,
            b.target_warehouse,b.transfer_out_location
        FROM `tabNaming Series Definition` a
        INNER JOIN `tabSeries List Definition` b 
            ON a.name = b.parent
        WHERE b.target_warehouse = %(warehouse)s
        AND a.allow = %(doctype)s
    """, {
        "warehouse": target_warehouse,
        "doctype": doctype
    }, as_dict=1)


@frappe.whitelist()
def trans_in_submit(self, method):
	stock_entry = frappe.new_doc("Stock Entry")
	#stock_entry.company = self.company
	stock_entry.stock_entry_type = 'Material Transfer'
	stock_entry.add_to_transit=1
	stock_entry.in_reference_no = self.name
	#for dtl in self.items:
	#	item_code = dtl.item_code
	#	serial_numbers_dict[item_code] = []
	#for vehicle_row in self.get("vehicle_detail"):
	#	if vehicle_row.item == item_code:
	#		serial_numbers_dict[item_code].append(vehicle_row.serial_no)
	#stock_entry.append("items", {
	#	"s_warehouse": self.set_warehouse,
	#	"t_warehouse": self.to_warehouse,
	#	"item_code": item_code,
	#	"qty": dtl.qty,
	#	"uom": "Nos",
	#	"allow_zero_valuation_rate": 0,
	#	"serial_no": "\n".join(serial_numbers_dict[item_code])
	#})
	for dtl in self.items:
		stock_entry.append("items", {
			"s_warehouse": self.set_warehouse,
			"t_warehouse": self.to_warehouse,
			"item_code": dtl.item_code,
			"qty": dtl.quantity,
			"uom": dtl.uom,
			#"cost_center":dtl.cost_center,
			"allow_zero_valuation_rate": 0
		})
	stock_entry.save()
	stock_entry.submit()
	frappe.db.commit()


@frappe.whitelist()
def createbom(item_code,item_name,item_group,brand,gst_hsn_code,stock_uom,description,mother_item_code,tool_type,tool_material,line_name):
	fitem = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_code+ "-" + "F",
			"item_name": item_code+ "-" + "F",
			"stock_uom": stock_uom,
			"item_group": item_group,
			"brand": brand,
			"gst_hsn_code": gst_hsn_code,
			"is_stock_item": 1,
			"include_item_in_manufacturing": 0,
			"description": description,
			"tool_type":tool_type,
			"tool_material":tool_material,
			"line_name":line_name,
			"mother_item_code":mother_item_code,
			"is_sub_contracted_item":1,
			})
	current_item = frappe.get_doc("Item", item_code)
	Tax = []
	for ctaxes in current_item.taxes:
		item_tax_template = ctaxes.item_tax_template
		if "18%" in item_tax_template:
			item_tax_template = item_tax_template.replace("18%", "18%")

		Tax.append({
			'item_tax_template': item_tax_template,
			'tax_category': ctaxes.tax_category
		})
	fitem.set("taxes", Tax)
	fitem.save()

	ritem = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_code+ "-" + "R",
			"item_name": item_code+ "-" + "R",
			"stock_uom": stock_uom,
			"item_group": item_group,
			"brand": brand,
			"gst_hsn_code": gst_hsn_code,
			"is_stock_item": 1,
			"include_item_in_manufacturing": 0,
			"description": description,
			"tool_type":tool_type,
			"tool_material":tool_material,
			"line_name":line_name,
			"mother_item_code":mother_item_code,

			})
	current_item = frappe.get_doc("Item", item_code)
	Tax = []
	for ctaxes in current_item.taxes:
		item_tax_template = ctaxes.item_tax_template
		if "18%" in item_tax_template:
			item_tax_template = item_tax_template.replace("18%", "18%")

		Tax.append({
			'item_tax_template': item_tax_template,
			'tax_category': ctaxes.tax_category
		})
	ritem.set("taxes", Tax)
	ritem.save()

	item = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_code+ "-" + "S",
			"item_name": item_code+ "-" + "S",
			"stock_uom": stock_uom,
			"item_group": item_group,
			"brand": brand,
			"gst_hsn_code": gst_hsn_code,
			"is_stock_item": 0,
			"include_item_in_manufacturing": 0,
			"description": description,
			"tool_type":tool_type,
			"tool_material":tool_material,
			"line_name":line_name,
			"mother_item_code":mother_item_code,

			})
	current_item = frappe.get_doc("Item", item_code)
	Tax = []
	for ctaxes in current_item.taxes:
		item_tax_template = ctaxes.item_tax_template
		if "18%" in item_tax_template:
			item_tax_template = item_tax_template.replace("18%", "18%")

		Tax.append({
			'item_tax_template': item_tax_template,
			'tax_category': ctaxes.tax_category
		})
	item.set("taxes", Tax)
	item.save()

	BOMdtl=[]
	BOMinsert = frappe.get_doc({
			"doctype": "BOM",
			"item": fitem.name,
			"uom":stock_uom,
			"is_active":1,
			"is_default":1,
			"set_rate_of_sub_assembly_item_based_on_bom":1,
			"quantity":1,
			"currency":"INR",
			"rm_cost_as_per":"Valuation Rate",
			"description":description
		})
	BOMdtl.append({"item_code": ritem.name,
				"description" : description,
				"qty":1,
				"uom" : stock_uom,
				"include_item_in_manufacturing" : 1
			})

	BOMinsert.set("items",BOMdtl)
	BOMinsert.save()
	BOMinsert.submit()
	frappe.db.set_value('Item',item_code, 'custom_item_and_bom_created', 1)
	frappe.msgprint("Item and BOM Created");


@frappe.whitelist()
def make_initial_inspection(source_name, target_doc=None):

    source = frappe.get_doc("Transfer In", source_name)

    doc = frappe.new_doc("Initial Inspection")
    doc.transfer_in_doc_no = source.name
    doc.date = source.transaction_date
    doc.transfer_out_location = source.transfer_out_location
    for d in source.items:

        # Original Item
        doc.append("initial_inspection_list", {
            "source_warehouse": source.to_warehouse,
            #"target_warehouse": source.to_warehouse,
            "item": d.item_code,
            "quantity": d.qty,
            "uom":d.uom
        })

        # RGP Item
        doc.append("initial_inspection_list", {
            #"source_warehouse": source.to_warehouse,
            "target_warehouse": source.to_warehouse,
            "item": f"{d.item_code}RGP",
            "quantity": d.qty,
            "uom":d.uom
        })

    return doc


def create_repack_stock_entry(doc, method=None):
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Repack"
    se.initial_inspection = doc.name
    se.posting_date = doc.date

    for d in doc.initial_inspection_list:
        se.append("items", {
            "item_code": d.item,
            "s_warehouse": d.source_warehouse,
            "t_warehouse": d.target_warehouse,
            "qty": d.quantity,
            "uom": d.uom,
            "stock_uom": d.uom,
            "allow_zero_valuation_rate":1
        })

    se.insert(ignore_permissions=True)
    se.submit()

    doc.db_set("stock_entry", se.name)

@frappe.whitelist()
def proformainvoice(customer):
	query=frappe.db.sql(""" select S.name,T.charge_type,T.account_head
				FROM `tabSales Taxes and Charges Template` S inner join `tabSales Taxes and Charges` T on S.name = T.parent
				Left Outer join `tabCustomer` C on C.tax_category = S.tax_category WHERE C.tax_category = S.tax_category
				and C.name='{customer}' """.format(customer=customer),as_dict=1)
	return query


@frappe.whitelist()
def get_warehouse_address(branch_name):
	warehouse = frappe.get_value('Warehouse',filters ={"custom_branch":branch_name})
	if warehouse:
		warehouse_address= frappe.db.sql("""SELECT CM.parent,ad.gstin
                                                FROM  `tabDynamic Link` CM
						inner join `tabAddress` ad on  ad.name=CM.parent
                                                WHERE CM.link_name='{warehouse}' and CM.link_doctype='Warehouse' limit 1""".format(warehouse=warehouse),as_dict=1)
		return warehouse_address

import frappe
from frappe import _


def create_stock_entry(doc, method=None):

    # =========================================================
    # SOURCE WAREHOUSE
    # =========================================================

    source_warehouse = doc.get("source_warehouse")

    if not source_warehouse:
        source_warehouse = doc.get("set_warehouse")

    if not source_warehouse:
        frappe.throw(
            _("Source Warehouse is required.")
        )


    # =========================================================
    # TARGET WAREHOUSE
    # =========================================================

    target_warehouse = "Scrap HO- UTM"


    # =========================================================
    # FIND TOOL STOCK WRITE OFF ITEM CHILD TABLE
    # =========================================================

    child_table_fieldname = None

    for df in frappe.get_meta("Tool Stock Write Off").fields:

        if (
            df.fieldtype == "Table"
            and df.options == "Tool Stock Write Off Item"
        ):
            child_table_fieldname = df.fieldname
            break


    if not child_table_fieldname:
        frappe.throw(
            _(
                "Child table <b>Tool Stock Write Off Item</b> "
                "is not found in Tool Stock Write Off."
            )
        )


    # =========================================================
    # GET CHILD TABLE ROWS
    # =========================================================

    items = doc.get(child_table_fieldname) or []


    if not items:
        frappe.throw(
            _(
                "No items found in Tool Stock Write Off Item table."
            )
        )


    # =========================================================
    # CREATE STOCK ENTRY
    # =========================================================

    stock_entry = frappe.new_doc("Stock Entry")

    stock_entry.stock_entry_type = "Material Issue"

    stock_entry.posting_date = (
        doc.posting_date
        if doc.get("posting_date")
        else frappe.utils.today()
    )

    if doc.get("posting_time"):
        stock_entry.posting_time = doc.posting_time

    stock_entry.set_posting_time = 1


    # =========================================================
    # ADD ITEMS
    # =========================================================

    for row in items:

        if not row.item_code:
            continue

        if not row.qty or row.qty <= 0:
            continue


        stock_item = stock_entry.append("items", {})


        # -----------------------------------------------------
        # ITEM CODE
        # -----------------------------------------------------

        stock_item.item_code = row.item_code


        # -----------------------------------------------------
        # QUANTITY
        # -----------------------------------------------------

        stock_item.qty = row.qty


        # -----------------------------------------------------
        # SOURCE WAREHOUSE
        # -----------------------------------------------------

        stock_item.s_warehouse = source_warehouse


        # -----------------------------------------------------
        # TARGET / SCRAP WAREHOUSE
        # -----------------------------------------------------

        stock_item.t_warehouse = target_warehouse


        # -----------------------------------------------------
        # VALUATION RATE
        # -----------------------------------------------------

        if row.valuation_rate:

            stock_item.basic_rate = row.valuation_rate


        # -----------------------------------------------------
        # STOCK VALUE / AMOUNT
        # -----------------------------------------------------

        if row.stock_value is not None:

            stock_item.amount = row.stock_value


        # -----------------------------------------------------
        # SERIAL NUMBERS
        # -----------------------------------------------------

        if row.serial_no:

            stock_item.serial_no = row.serial_no.strip()


    # =========================================================
    # CHECK STOCK ENTRY ITEMS
    # =========================================================

    if not stock_entry.items:

        frappe.throw(
            _(
                "No valid items found in "
                "<b>Tool Stock Write Off Item</b>."
            )
        )


    # =========================================================
    # INSERT STOCK ENTRY
    # =========================================================

    stock_entry.insert(
        ignore_permissions=True
    )


    # =========================================================
    # SUBMIT STOCK ENTRY
    # =========================================================

    stock_entry.submit()


    # =========================================================
    # MESSAGE
    # =========================================================

    frappe.msgprint(
        _(
            "Stock Entry <b>{0}</b> "
            "created and submitted successfully."
        ).format(stock_entry.name),
        title=_("Stock Entry Created"),
        indicator="green"
    )
