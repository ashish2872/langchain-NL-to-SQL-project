from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Numeric, ForeignKey, DateTime, func, Index, DDL, event, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# RLS Policy Helper
def create_rls_policy(table_name):
    return DDL(f'''
        ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
        CREATE POLICY company_isolation_policy ON {table_name}
            USING (company_id = current_setting('app.current_company_id')::uuid);
    ''')

# Event listener to apply RLS policies after table creation
@event.listens_for(Base.metadata, 'after_create')
def receive_after_create(target, connection, **kw):
    for table in target.sorted_tables:
        if hasattr(table.columns, 'company_id'):
            connection.execute(create_rls_policy(table.name))

def get_tables_in_order():
    """Returns tables in the correct order for creation based on dependencies."""
    return [
        # First level - No foreign key dependencies
        Company,
        Role,
        # Second level - Depend on first level
        Address,
        UserCompanyRole,
        Department,
        Account,
        Customer,
        Vendor,
        Product,
        CompanyGSTIN,
        # Third level - Depend on second level
        Transaction,
        Inventory,
        SalesOrder,
        PurchaseOrder,
        FixedAsset,
        Employee,
        # Fourth level - Depend on third level
        SalesOrderItem,
        PurchaseOrderItem,
        Invoice,
        Payable,
        Payroll,
        AuditLog,
        Subscription,
        Payment,
        EmailVerification,
        PhoneVerification,
        FileExport
    ]

class Address(Base):
    __tablename__ = 'addresses'
    
    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default='India')
    pin_code = Column(String(10), nullable=False)
    latitude = Column(Float)  # Google Maps latitude
    longitude = Column(Float)  # Google Maps longitude
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    company = relationship('Company', back_populates='addresses')
    inventory = relationship('Inventory', back_populates='address')
    fixed_assets = relationship('FixedAsset', back_populates='address')

    __table_args__ = (
        Index('idx_addresses_company_id', 'company_id'),
        Index('idx_addresses_city_state', 'city', 'state'),
        Index('idx_addresses_pin_code', 'pin_code'),
    )

class CompanyGSTIN(Base):
    __tablename__ = 'company_gstins'
    
    gstin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    gstin = Column(String(15), nullable=False)
    address_id = Column(UUID(as_uuid=True), ForeignKey('addresses.address_id'), nullable=False)  # Registered address for this GSTIN
    is_primary = Column(Boolean, default=False)  # To mark the primary GSTIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    company = relationship('Company', back_populates='gstins')
    address = relationship('Address')

    __table_args__ = (
        Index('idx_company_gstins_company_id', 'company_id'),
        Index('idx_company_gstins_gstin', 'gstin'),
        Index('idx_company_gstins_address', 'address_id'),
    )

class Company(Base):
    __tablename__ = 'companies'
    
    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    cin = Column(String(21))  # Corporate Identity Number (21 characters)
    pan = Column(String(10))  # Permanent Account Number (10 characters)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    addresses = relationship('Address', back_populates='company')
    gstins = relationship('CompanyGSTIN', back_populates='company')
    user_roles = relationship('UserCompanyRole', back_populates='company')
    departments = relationship('Department', back_populates='company')
    customers = relationship('Customer', back_populates='company')
    vendors = relationship('Vendor', back_populates='company')
    products = relationship('Product', back_populates='company')
    subscriptions = relationship('Subscription', back_populates='company')

    __table_args__ = (
        Index('idx_companies_name', 'name'),
        Index('idx_companies_cin', 'cin'),
        Index('idx_companies_pan', 'pan'),
    )

class UserCompanyRole(Base):
    __tablename__ = 'user_company_roles'
    
    erp_user_id = Column(UUID(as_uuid=True), primary_key=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    company = relationship('Company', back_populates='user_roles')
    role = relationship('Role', back_populates='user_company_roles')

    __table_args__ = (
        Index('idx_user_company_roles_erp_user_id', 'erp_user_id'),
        Index('idx_user_company_roles_company_id', 'company_id'),
        Index('idx_user_company_roles_role_id', 'role_id'),
    )

class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    role_name = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    user_company_roles = relationship('UserCompanyRole', back_populates='role')

    __table_args__ = (
        Index('idx_roles_company_id', 'company_id'),
        Index('idx_roles_name', 'role_name'),
    )

class Department(Base):
    __tablename__ = 'departments'
    
    department_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company', back_populates='departments')
    employees = relationship('Employee', back_populates='department')

    __table_args__ = (
        Index('idx_departments_company_id', 'company_id'),
    )

class Account(Base):
    __tablename__ = 'accounts'
    
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20))  # asset, liability, expense, income, equity
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.account_id'))
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)

    # Relationships
    company = relationship('Company')
    transactions = relationship('Transaction', back_populates='account')
    parent = relationship('Account', remote_side=[account_id])
    children = relationship('Account')

    __table_args__ = (
        Index('idx_accounts_company_id', 'company_id'),
        Index('idx_accounts_code', 'code'),
        Index('idx_accounts_type', 'type'),
    )

class Transaction(Base):
    __tablename__ = 'transactions'
    
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.account_id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(String(10))  # debit, credit
    description = Column(Text)
    reference_type = Column(String(50))  # invoice, payment, journal, etc.
    reference_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))  # erp_user_id
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    account = relationship('Account', back_populates='transactions')

    __table_args__ = (
        Index('idx_transactions_company_id', 'company_id'),
        Index('idx_transactions_account_id', 'account_id'),
        Index('idx_transactions_date', 'date'),
        Index('idx_transactions_reference', 'reference_type', 'reference_id'),
        Index('idx_transactions_created_by', 'created_by'),
    )

class Customer(Base):
    __tablename__ = 'customers'
    
    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default='India')
    contact_person = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    credit_limit = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    company = relationship('Company', back_populates='customers')
    sales_orders = relationship('SalesOrder', back_populates='customer')
    invoices = relationship('Invoice', back_populates='customer')

    __table_args__ = (
        Index('idx_customers_company_id', 'company_id'),
        Index('idx_customers_name', 'name'),
        Index('idx_customers_gstin', 'gstin'),
    )

class Vendor(Base):
    __tablename__ = 'vendors'
    
    vendor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default='India')
    contact_person = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    credit_limit = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)

    # Relationships
    company = relationship('Company', back_populates='vendors')
    purchase_orders = relationship('PurchaseOrder', back_populates='vendor')
    payables = relationship('Payable', back_populates='vendor')

    __table_args__ = (
        Index('idx_vendors_company_id', 'company_id'),
        Index('idx_vendors_name', 'name'),
        Index('idx_vendors_gstin', 'gstin'),
    )

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True)
    hsn_code = Column(String(10))
    description = Column(Text)
    unit = Column(String(20))  # pcs, kg, etc.
    sale_price = Column(Numeric(15, 2))
    purchase_price = Column(Numeric(15, 2))
    min_stock_level = Column(Numeric(12, 2))
    max_stock_level = Column(Numeric(12, 2))
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)

    # Relationships
    company = relationship('Company', back_populates='products')
    inventory = relationship('Inventory', back_populates='product')
    sales_order_items = relationship('SalesOrderItem', back_populates='product')
    purchase_order_items = relationship('PurchaseOrderItem', back_populates='product')

    __table_args__ = (
        Index('idx_products_company_id', 'company_id'),
        Index('idx_products_sku', 'sku'),
        Index('idx_products_hsn', 'hsn_code'),
    )

class Inventory(Base):
    __tablename__ = 'inventory'
    
    inventory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    address_id = Column(UUID(as_uuid=True), ForeignKey('addresses.address_id'), nullable=False) # location of warehouse
    quantity = Column(Numeric(12, 2))
    last_updated = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    product = relationship('Product', back_populates='inventory')
    address = relationship('Address', back_populates='inventory')

    __table_args__ = (
        Index('idx_inventory_company_id', 'company_id'),
        Index('idx_inventory_product_address', 'product_id', 'address_id'),
    )

class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    
    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.customer_id'), nullable=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date)
    status = Column(String(50))  # draft, confirmed, processing, shipped, delivered, cancelled
    subtotal = Column(Numeric(15, 2))
    # GST fields
    cgst_amount = Column(Numeric(15, 2), default=0)  # Central GST
    sgst_amount = Column(Numeric(15, 2), default=0)  # State GST
    igst_amount = Column(Numeric(15, 2), default=0)  # Integrated GST
    total_amount = Column(Numeric(15, 2))
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))  # erp_user_id
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    customer = relationship('Customer', back_populates='sales_orders')
    items = relationship('SalesOrderItem', back_populates='order')
    invoice = relationship('Invoice', back_populates='sales_order')

    __table_args__ = (
        Index('idx_sales_orders_company_id', 'company_id'),
        Index('idx_sales_orders_customer_id', 'customer_id'),
        Index('idx_sales_orders_order_date', 'order_date'),
        Index('idx_sales_orders_status', 'status'),
    )

class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.order_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    # GST fields
    gst_rate = Column(Numeric(5, 2))  # Total GST rate
    cgst_rate = Column(Numeric(5, 2))  # Central GST rate
    sgst_rate = Column(Numeric(5, 2))  # State GST rate
    igst_rate = Column(Numeric(5, 2))  # Integrated GST rate
    cgst_amount = Column(Numeric(15, 2), default=0)  # Central GST amount
    sgst_amount = Column(Numeric(15, 2), default=0)  # State GST amount
    igst_amount = Column(Numeric(15, 2), default=0)  # Integrated GST amount
    total_amount = Column(Numeric(15, 2))

    # Relationships
    company = relationship('Company')
    order = relationship('SalesOrder', back_populates='items')
    product = relationship('Product', back_populates='sales_order_items')

    __table_args__ = (
        Index('idx_sales_order_items_company_id', 'company_id'),
        Index('idx_sales_order_items_order_id', 'order_id'),
        Index('idx_sales_order_items_product_id', 'product_id'),
    )

class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    
    po_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey('vendors.vendor_id'), nullable=False)
    po_date = Column(Date, nullable=False)
    expected_date = Column(Date)
    status = Column(String(50))  # draft, confirmed, received, cancelled
    subtotal = Column(Numeric(15, 2))
    # GST fields
    cgst_amount = Column(Numeric(15, 2), default=0)  # Central GST
    sgst_amount = Column(Numeric(15, 2), default=0)  # State GST
    igst_amount = Column(Numeric(15, 2), default=0)  # Integrated GST
    total_amount = Column(Numeric(15, 2))
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))  # erp_user_id
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    vendor = relationship('Vendor', back_populates='purchase_orders')
    items = relationship('PurchaseOrderItem', back_populates='purchase_order')
    payable = relationship('Payable', back_populates='purchase_order')

    __table_args__ = (
        Index('idx_purchase_orders_company_id', 'company_id'),
        Index('idx_purchase_orders_vendor_id', 'vendor_id'),
        Index('idx_purchase_orders_po_date', 'po_date'),
        Index('idx_purchase_orders_status', 'status'),
    )

class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_items'
    
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.po_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    # GST fields
    gst_rate = Column(Numeric(5, 2))  # Total GST rate
    cgst_rate = Column(Numeric(5, 2))  # Central GST rate
    sgst_rate = Column(Numeric(5, 2))  # State GST rate
    igst_rate = Column(Numeric(5, 2))  # Integrated GST rate
    cgst_amount = Column(Numeric(15, 2), default=0)  # Central GST amount
    sgst_amount = Column(Numeric(15, 2), default=0)  # State GST amount
    igst_amount = Column(Numeric(15, 2), default=0)  # Integrated GST amount
    total_amount = Column(Numeric(15, 2))

    # Relationships
    company = relationship('Company')
    purchase_order = relationship('PurchaseOrder', back_populates='items')
    product = relationship('Product', back_populates='purchase_order_items')

    __table_args__ = (
        Index('idx_purchase_order_items_company_id', 'company_id'),
        Index('idx_purchase_order_items_po_id', 'po_id'),
        Index('idx_purchase_order_items_product_id', 'product_id'),
    )

class Invoice(Base):
    __tablename__ = 'invoices'
    
    invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.order_id'), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.customer_id'), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default='unpaid')  # unpaid, partially_paid, paid, overdue
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    sales_order = relationship('SalesOrder', back_populates='invoice')
    customer = relationship('Customer', back_populates='invoices')

    __table_args__ = (
        Index('idx_invoices_company_id', 'company_id'),
        Index('idx_invoices_customer', 'customer_id'),
        Index('idx_invoices_dates', 'invoice_date', 'due_date'),
        Index('idx_invoices_status', 'status'),
    )

class Payable(Base):
    __tablename__ = 'payables'
    
    payable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.po_id'), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey('vendors.vendor_id'), nullable=False)
    invoice_date = Column(Date, nullable=False)
    # shoulld be with po or vendor
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default='unpaid')  # unpaid, partially_paid, paid, overdue
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    purchase_order = relationship('PurchaseOrder', back_populates='payable')
    vendor = relationship('Vendor', back_populates='payables')

    __table_args__ = (
        Index('idx_payables_company_id', 'company_id'),
        Index('idx_payables_vendor', 'vendor_id'),
        Index('idx_payables_dates', 'invoice_date', 'due_date'),
        Index('idx_payables_status', 'status'),
    )

class FixedAsset(Base):
    __tablename__ = 'fixed_assets'
    
    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    asset_number = Column(String(50), unique=True)
    purchase_date = Column(Date)
    purchase_value = Column(Numeric(15, 2))
    vendor_id = Column(UUID(as_uuid=True), ForeignKey('vendors.vendor_id'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('addresses.address_id'))
    asset_class = Column(String(100))
    useful_life_years = Column(Integer)
    depreciation_method = Column(String(50))
    salvage_value = Column(Numeric(15, 2))
    current_value = Column(Numeric(15, 2))
    last_depreciation_date = Column(Date)
    depreciation_rate = Column(Numeric(5, 2))
    status = Column(String(50))  # active, disposed, written-off
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    vendor = relationship('Vendor')
    address = relationship('Address', back_populates='fixed_assets')

    __table_args__ = (
        Index('idx_fixed_assets_company_id', 'company_id'),
        Index('idx_fixed_assets_number', 'asset_number'),
        Index('idx_fixed_assets_class', 'asset_class'),
    )

class Employee(Base):
    __tablename__ = 'employees'
    
    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.department_id'))
    employee_code = Column(String(50), unique=True)
    name = Column(String(255), nullable=False)
    pan = Column(String(10))
    pf_number = Column(String(20))
    esi_number = Column(String(20))
    uan = Column(String(12))
    doj = Column(Date)  # Date of joining
    dol = Column(Date)  # Date of leaving
    salary = Column(Numeric(15, 2))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default='India')
    status = Column(String(20))  # active, inactive, terminated
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    department = relationship('Department', back_populates='employees')
    payrolls = relationship('Payroll', back_populates='employee')

    __table_args__ = (
        Index('idx_employees_company_id', 'company_id'),
        Index('idx_employees_department', 'department_id'),
        Index('idx_employees_code', 'employee_code'),
    )

class Payroll(Base):
    __tablename__ = 'payroll'
    
    payroll_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.employee_id'), nullable=False)
    pay_period = Column(Date, nullable=False)  # First day of the month
    basic_salary = Column(Numeric(15, 2))
    hra = Column(Numeric(12, 2))
    conveyance = Column(Numeric(12, 2))
    medical_allowance = Column(Numeric(12, 2))
    special_allowance = Column(Numeric(12, 2))
    gross_salary = Column(Numeric(15, 2))
    pf_deduction = Column(Numeric(12, 2))
    esi_deduction = Column(Numeric(12, 2))
    tds_deduction = Column(Numeric(12, 2))
    other_deductions = Column(Numeric(12, 2))
    net_salary = Column(Numeric(15, 2))
    payment_status = Column(String(20))  # pending, paid
    payment_date = Column(Date)
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')
    employee = relationship('Employee', back_populates='payrolls')

    __table_args__ = (
        Index('idx_payroll_company_id', 'company_id'),
        Index('idx_payroll_employee', 'employee_id'),
        Index('idx_payroll_period', 'pay_period'),
    )

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    erp_user_id = Column(UUID(as_uuid=True))
    action = Column(String(255))
    table_name = Column(String(100))
    record_id = Column(UUID(as_uuid=True))
    old_values = Column(Text)  # JSON string of old values
    new_values = Column(Text)  # JSON string of new values
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    company = relationship('Company')

    __table_args__ = (
        Index('idx_audit_logs_company_id', 'company_id'),
        Index('idx_audit_logs_erp_user_id', 'erp_user_id'),
        Index('idx_audit_logs_table', 'table_name'),
        Index('idx_audit_logs_created', 'created_at'),
    )

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False) # User who initiated the subscription
    plan_type = Column(String(50), nullable=False) # e.g., "monthly", "annual"
    start_date = Column(DateTime, default=func.current_timestamp())
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    price_per_user_per_month = Column(Numeric(15, 2), nullable=False)
    total_users = Column(Integer, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    payment_status = Column(String(50), default='pending') # e.g., "paid", "pending", "failed"
    razorpay_payment_id = Column(String(255))
    trial_start_date = Column(DateTime)
    trial_end_date = Column(DateTime)
    is_trial_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    company = relationship('Company', back_populates='subscriptions')
    payments = relationship('Payment', back_populates='subscription')

    __table_args__ = (
        Index('idx_subscriptions_company_id', 'company_id'),
        Index('idx_subscriptions_user_id', 'user_id'),
        Index('idx_subscriptions_status', 'is_active', 'payment_status'),
    )

class Payment(Base):
    __tablename__ = 'payments'
    
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.subscription_id', ondelete='CASCADE'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime, default=func.current_timestamp())
    status = Column(String(50), default='completed') # e.g., "completed", "pending", "failed"
    razorpay_order_id = Column(String(255))
    razorpay_payment_id = Column(String(255))
    created_at = Column(DateTime, default=func.current_timestamp())

    # Relationships
    subscription = relationship('Subscription', back_populates='payments')

    __table_args__ = (
        Index('idx_payments_subscription_id', 'subscription_id'),
        Index('idx_payments_status', 'status'),
    )

class EmailVerification(Base):
    __tablename__ = 'email_verifications'
    
    verification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    otp = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_email_verifications_user_id', 'user_id'),
        Index('idx_email_verifications_email', 'email'),
    )

class PhoneVerification(Base):
    __tablename__ = 'phone_verifications'
    
    verification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    otp = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_phone_verifications_user_id', 'user_id'),
        Index('idx_phone_verifications_phone_number', 'phone_number'),
    )

class FileExport(Base):
    __tablename__ = 'file_exports'
    
    export_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False) # ERP user ID who requested the export
    user_email = Column(String(255)) # Email of the user who requested the export
    file_type = Column(String(10), nullable=False) # e.g., 'xlsx', 'pdf'
    status = Column(String(20), default='pending') # 'pending', 'processing', 'completed', 'failed'
    file_path = Column(String(255)) # Path or URL to the generated file
    requested_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime)
    email_sent = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_file_exports_company_id', 'company_id'),
        Index('idx_file_exports_user_id', 'user_id'),
        Index('idx_file_exports_status', 'status'),
    )
