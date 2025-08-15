-- Enable extension for UUID generation (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- TABLE: companies ----------
CREATE TABLE companies (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    cin VARCHAR(21),
    pan VARCHAR(10),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_cin ON companies(cin);
CREATE INDEX idx_companies_pan ON companies(pan);

-- ---------- TABLE: roles ----------
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_roles_company_id ON roles(company_id);
CREATE INDEX idx_roles_name ON roles(role_name);

-- ---------- TABLE: addresses ----------
CREATE TABLE addresses (
    address_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    pin_code VARCHAR(10) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_addresses_company_id ON addresses(company_id);
CREATE INDEX idx_addresses_city_state ON addresses(city, state);
CREATE INDEX idx_addresses_pin_code ON addresses(pin_code);

-- ---------- TABLE: company_gstins ----------
CREATE TABLE company_gstins (
    gstin_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    gstin VARCHAR(15) NOT NULL,
    address_id UUID NOT NULL REFERENCES addresses(address_id),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_company_gstins_company_id ON company_gstins(company_id);
CREATE INDEX idx_company_gstins_gstin ON company_gstins(gstin);
CREATE INDEX idx_company_gstins_address ON company_gstins(address_id);

-- ---------- TABLE: user_company_roles ----------
CREATE TABLE user_company_roles (
    erp_user_id UUID NOT NULL,
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (erp_user_id, company_id, role_id)
);

CREATE INDEX idx_user_company_roles_erp_user_id ON user_company_roles(erp_user_id);
CREATE INDEX idx_user_company_roles_company_id ON user_company_roles(company_id);
CREATE INDEX idx_user_company_roles_role_id ON user_company_roles(role_id);

-- ---------- TABLE: departments ----------
CREATE TABLE departments (
    department_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_departments_company_id ON departments(company_id);

-- ---------- TABLE: accounts ----------
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20),
    parent_account_id UUID REFERENCES accounts(account_id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_accounts_company_id ON accounts(company_id);
CREATE INDEX idx_accounts_code ON accounts(code);
CREATE INDEX idx_accounts_type ON accounts(type);

-- ---------- TABLE: transactions ----------
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    amount NUMERIC(15,2) NOT NULL,
    type VARCHAR(10),
    description TEXT,
    reference_type VARCHAR(50),
    reference_id UUID,
    created_by UUID,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_company_id ON transactions(company_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_reference ON transactions(reference_type, reference_id);
CREATE INDEX idx_transactions_created_by ON transactions(created_by);

-- ---------- TABLE: customers ----------
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    gstin VARCHAR(15),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    credit_limit NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_customers_company_id ON customers(company_id);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_gstin ON customers(gstin);

-- ---------- TABLE: vendors ----------
CREATE TABLE vendors (
    vendor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    gstin VARCHAR(15),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    credit_limit NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_vendors_company_id ON vendors(company_id);
CREATE INDEX idx_vendors_name ON vendors(name);
CREATE INDEX idx_vendors_gstin ON vendors(gstin);

-- ---------- TABLE: products ----------
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    hsn_code VARCHAR(10),
    description TEXT,
    unit VARCHAR(20),
    sale_price NUMERIC(15,2),
    purchase_price NUMERIC(15,2),
    min_stock_level NUMERIC(12,2),
    max_stock_level NUMERIC(12,2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_products_company_id ON products(company_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_hsn ON products(hsn_code);

-- ---------- TABLE: inventory ----------
CREATE TABLE inventory (
    inventory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id),
    address_id UUID NOT NULL REFERENCES addresses(address_id),
    quantity NUMERIC(12,2),
    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_company_id ON inventory(company_id);
CREATE INDEX idx_inventory_product_address ON inventory(product_id, address_id);

-- ---------- TABLE: sales_orders ----------
CREATE TABLE sales_orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    delivery_date DATE,
    status VARCHAR(50),
    subtotal NUMERIC(15,2),
    cgst_amount NUMERIC(15,2) DEFAULT 0,
    sgst_amount NUMERIC(15,2) DEFAULT 0,
    igst_amount NUMERIC(15,2) DEFAULT 0,
    total_amount NUMERIC(15,2),
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_orders_company_id ON sales_orders(company_id);
CREATE INDEX idx_sales_orders_customer_id ON sales_orders(customer_id);
CREATE INDEX idx_sales_orders_order_date ON sales_orders(order_date);
CREATE INDEX idx_sales_orders_status ON sales_orders(status);

-- ---------- TABLE: sales_order_items ----------
CREATE TABLE sales_order_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES sales_orders(order_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id),
    quantity NUMERIC(12,2) NOT NULL,
    unit_price NUMERIC(15,2) NOT NULL,
    gst_rate NUMERIC(5,2),
    cgst_rate NUMERIC(5,2),
    sgst_rate NUMERIC(5,2),
    igst_rate NUMERIC(5,2),
    cgst_amount NUMERIC(15,2) DEFAULT 0,
    sgst_amount NUMERIC(15,2) DEFAULT 0,
    igst_amount NUMERIC(15,2) DEFAULT 0,
    total_amount NUMERIC(15,2)
);

CREATE INDEX idx_sales_order_items_company_id ON sales_order_items(company_id);
CREATE INDEX idx_sales_order_items_order_id ON sales_order_items(order_id);
CREATE INDEX idx_sales_order_items_product_id ON sales_order_items(product_id);

-- ---------- TABLE: purchase_orders ----------
CREATE TABLE purchase_orders (
    po_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    vendor_id UUID NOT NULL REFERENCES vendors(vendor_id),
    po_date DATE NOT NULL,
    expected_date DATE,
    status VARCHAR(50),
    subtotal NUMERIC(15,2),
    cgst_amount NUMERIC(15,2) DEFAULT 0,
    sgst_amount NUMERIC(15,2) DEFAULT 0,
    igst_amount NUMERIC(15,2) DEFAULT 0,
    total_amount NUMERIC(15,2),
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_purchase_orders_company_id ON purchase_orders(company_id);
CREATE INDEX idx_purchase_orders_vendor_id ON purchase_orders(vendor_id);
CREATE INDEX idx_purchase_orders_po_date ON purchase_orders(po_date);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);

-- ---------- TABLE: purchase_order_items ----------
CREATE TABLE purchase_order_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    po_id UUID NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id),
    quantity NUMERIC(12,2) NOT NULL,
    unit_price NUMERIC(15,2) NOT NULL,
    gst_rate NUMERIC(5,2),
    cgst_rate NUMERIC(5,2),
    sgst_rate NUMERIC(5,2),
    igst_rate NUMERIC(5,2),
    cgst_amount NUMERIC(15,2) DEFAULT 0,
    sgst_amount NUMERIC(15,2) DEFAULT 0,
    igst_amount NUMERIC(15,2) DEFAULT 0,
    total_amount NUMERIC(15,2)
);

CREATE INDEX idx_purchase_order_items_company_id ON purchase_order_items(company_id);
CREATE INDEX idx_purchase_order_items_po_id ON purchase_order_items(po_id);
CREATE INDEX idx_purchase_order_items_product_id ON purchase_order_items(product_id);

-- ---------- TABLE: invoices ----------
CREATE TABLE invoices (
    invoice_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES sales_orders(order_id),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    paid_amount NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'unpaid',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoices_company_id ON invoices(company_id);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_dates ON invoices(invoice_date, due_date);
CREATE INDEX idx_invoices_status ON invoices(status);

-- ---------- TABLE: payables ----------
CREATE TABLE payables (
    payable_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    po_id UUID NOT NULL REFERENCES purchase_orders(po_id),
    vendor_id UUID NOT NULL REFERENCES vendors(vendor_id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    paid_amount NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'unpaid',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payables_company_id ON payables(company_id);
CREATE INDEX idx_payables_vendor ON payables(vendor_id);
CREATE INDEX idx_payables_dates ON payables(invoice_date, due_date);
CREATE INDEX idx_payables_status ON payables(status);

-- ---------- TABLE: fixed_assets ----------
CREATE TABLE fixed_assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    asset_number VARCHAR(50) UNIQUE,
    purchase_date DATE,
    purchase_value NUMERIC(15,2),
    vendor_id UUID REFERENCES vendors(vendor_id),
    address_id UUID REFERENCES addresses(address_id),
    asset_class VARCHAR(100),
    useful_life_years INTEGER,
    depreciation_method VARCHAR(50),
    salvage_value NUMERIC(15,2),
    current_value NUMERIC(15,2),
    last_depreciation_date DATE,
    depreciation_rate NUMERIC(5,2),
    status VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fixed_assets_company_id ON fixed_assets(company_id);
CREATE INDEX idx_fixed_assets_number ON fixed_assets(asset_number);
CREATE INDEX idx_fixed_assets_class ON fixed_assets(asset_class);

-- ---------- TABLE: employees ----------
CREATE TABLE employees (
    employee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(department_id),
    employee_code VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    pan VARCHAR(10),
    pf_number VARCHAR(20),
    esi_number VARCHAR(20),
    uan VARCHAR(12),
    doj DATE,
    dol DATE,
    salary NUMERIC(15,2),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    status VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_employees_company_id ON employees(company_id);
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_code ON employees(employee_code);

-- ---------- TABLE: payroll ----------
CREATE TABLE payroll (
    payroll_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(employee_id),
    pay_period DATE NOT NULL,
    basic_salary NUMERIC(15,2),
    hra NUMERIC(12,2),
    conveyance NUMERIC(12,2),
    medical_allowance NUMERIC(12,2),
    special_allowance NUMERIC(12,2),
    gross_salary NUMERIC(15,2),
    pf_deduction NUMERIC(12,2),
    esi_deduction NUMERIC(12,2),
    tds_deduction NUMERIC(12,2),
    other_deductions NUMERIC(12,2),
    net_salary NUMERIC(15,2),
    payment_status VARCHAR(20),
    payment_date DATE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payroll_company_id ON payroll(company_id);
CREATE INDEX idx_payroll_employee ON payroll(employee_id);
CREATE INDEX idx_payroll_period ON payroll(pay_period);

-- ---------- TABLE: audit_logs ----------
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    erp_user_id UUID,
    action VARCHAR(255),
    table_name VARCHAR(100),
    record_id UUID,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX idx_audit_logs_erp_user_id ON audit_logs(erp_user_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ---------- TABLE: subscriptions ----------
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    price_per_user_per_month NUMERIC(15,2) NOT NULL,
    total_users INTEGER NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending',
    razorpay_payment_id VARCHAR(255),
    trial_start_date TIMESTAMP WITHOUT TIME ZONE,
    trial_end_date TIMESTAMP WITHOUT TIME ZONE,
    is_trial_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_company_id ON subscriptions(company_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(is_active, payment_status);

-- ---------- TABLE: payments ----------
CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
    amount NUMERIC(15,2) NOT NULL,
    payment_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed',
    razorpay_order_id VARCHAR(255),
    razorpay_payment_id VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX idx_payments_status ON payments(status);

-- ---------- TABLE: email_verifications ----------
CREATE TABLE email_verifications (
    verification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    otp VARCHAR(6) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX idx_email_verifications_email ON email_verifications(email);

-- ---------- TABLE: phone_verifications ----------
CREATE TABLE phone_verifications (
    verification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    otp VARCHAR(6) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX idx_phone_verifications_user_id ON phone_verifications(user_id);
CREATE INDEX idx_phone_verifications_phone_number ON phone_verifications(phone_number);

-- ---------- TABLE: file_exports ----------
CREATE TABLE file_exports (
    export_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    user_email VARCHAR(255),
    file_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    file_path VARCHAR(255),
    requested_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    email_sent BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_file_exports_company_id ON file_exports(company_id);
CREATE INDEX idx_file_exports_user_id ON file_exports(user_id);
CREATE INDEX idx_file_exports_status ON file_exports(status);

-- Enable Row Level Security and create policies for tables that have company_id column

-- List of tables with company_id (according to your code):
-- companies, roles, addresses, company_gstins, user_company_roles, departments, accounts,
-- transactions, customers, vendors, products, inventory, sales_orders, sales_order_items,
-- purchase_orders, purchase_order_items, invoices, payables, fixed_assets, employees,
-- payroll, audit_logs, subscriptions, payments, file_exports

-- Note: 'companies' table does NOT have company_id column referencing another table, so RLS can be applied carefully (depending on your design).
-- We'll enable RLS starting from those tables that have company_id column referencing companies.

-- You may want to enable RLS and create policy on companies as well to restrict access by company itself (customize the policy accordingly).

DO $$
DECLARE
    rls_tables TEXT[] := ARRAY[
        'roles', 'addresses', 'company_gstins', 'user_company_roles', 'departments', 'accounts',
        'transactions', 'customers', 'vendors', 'products', 'inventory', 'sales_orders', 'sales_order_items',
        'purchase_orders', 'purchase_order_items', 'invoices', 'payables', 'fixed_assets', 'employees',
        'payroll', 'audit_logs', 'subscriptions', 'payments', 'file_exports'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY rls_tables LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', tbl);
        EXECUTE format('
            CREATE POLICY company_isolation_policy ON %I
            USING (company_id = current_setting(''app.current_company_id'')::uuid);
        ', tbl);
    END LOOP;
END $$;

-- You should set the "app.current_company_id" setting in your database session to enforce RLS.

-- End of DDL script
