CREATE EXTENSION IF NOT EXISTS vector;

-- Core merchant tables
CREATE TABLE IF NOT EXISTS merchants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    logo_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(50) PRIMARY KEY,
    merchant_id VARCHAR(50) REFERENCES merchants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    category VARCHAR(100),
    image_url VARCHAR(255),
    attributes JSONB DEFAULT '{}'::jsonb,
    embedding vector(3072)
);
ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding vector(3072);

CREATE TABLE IF NOT EXISTS inventory (
    product_id VARCHAR(50) PRIMARY KEY REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    warehouse VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20)
);

-- Commerce tables
CREATE TABLE IF NOT EXISTS promotions (
    id VARCHAR(50) PRIMARY KEY,
    merchant_id VARCHAR(50) REFERENCES merchants(id),
    type VARCHAR(50) NOT NULL, -- e.g., 'percentage_discount', 'flat_discount', 'bundle'
    value DECIMAL(10, 2) NOT NULL,
    min_order_value DECIMAL(10, 2),
    max_discount DECIMAL(10, 2),
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS carts (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(50) REFERENCES customers(id),
    status VARCHAR(50) DEFAULT 'active', -- active, converted, abandoned
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart_items (
    id VARCHAR(50) PRIMARY KEY,
    cart_id VARCHAR(50) REFERENCES carts(id),
    product_id VARCHAR(50) REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(50) PRIMARY KEY,
    cart_id VARCHAR(50) REFERENCES carts(id),
    customer_id VARCHAR(50) REFERENCES customers(id),
    merchant_id VARCHAR(50) REFERENCES merchants(id),
    total DECIMAL(10, 2) NOT NULL,
    discount_total DECIMAL(10, 2) DEFAULT 0,
    final_total DECIMAL(10, 2) NOT NULL,
    razorpay_order_id VARCHAR(255),
    razorpay_payment_link_id VARCHAR(255),
    razorpay_payment_link_url VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, authorized, captured, failed
    order_status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES orders(id),
    product_id VARCHAR(50) REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0
);

-- Policy & governance tables
CREATE TABLE IF NOT EXISTS merchant_policies (
    id VARCHAR(50) PRIMARY KEY,
    merchant_id VARCHAR(50) REFERENCES merchants(id),
    policy_type VARCHAR(100) NOT NULL,
    policy_key VARCHAR(100) NOT NULL,
    policy_value JSONB NOT NULL
);

-- Audit trail (append-only)
CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    agent VARCHAR(50) NOT NULL,
    action TEXT NOT NULL,
    details JSONB,
    policy_check JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- RAG knowledge
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(50) REFERENCES merchants(id),
    doc_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(3072), -- gemini-embedding-2 produces 3072-d vectors
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Revenue tracking
CREATE TABLE IF NOT EXISTS revenue_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    original_value DECIMAL(10, 2) NOT NULL,
    ai_suggested_value DECIMAL(10, 2) NOT NULL,
    final_value DECIMAL(10, 2),
    delta DECIMAL(10, 2),
    product_id VARCHAR(50) REFERENCES products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
