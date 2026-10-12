-- A small online shop: four related tables.
-- Used by the example notebooks. PostgreSQL syntax; structure only.

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name   VARCHAR(120) NOT NULL,
    email       VARCHAR(160) NOT NULL UNIQUE,
    country     VARCHAR(60)  NOT NULL,
    signup_date DATE         NOT NULL
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name VARCHAR(120)  NOT NULL,
    category     VARCHAR(20)   NOT NULL CHECK (category IN ('Electronics', 'Home', 'Kitchen', 'Toys', 'Sports', 'Books')),
    unit_price   NUMERIC(10,2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER       NOT NULL REFERENCES customers(customer_id),
    order_date  DATE          NOT NULL,
    status      VARCHAR(12)   NOT NULL CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled')),
    order_total NUMERIC(12,2) NOT NULL
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER       NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER       NOT NULL REFERENCES products(product_id),
    quantity      INTEGER       NOT NULL,
    unit_price    NUMERIC(10,2) NOT NULL,
    line_total    NUMERIC(12,2) NOT NULL
);
