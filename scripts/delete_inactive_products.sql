-- ============================================================
-- Aurum Ghana: Permanently Delete Inactive Products
-- Run this in pgAdmin 4: Tools > Query Tool > Open this file
-- ============================================================

-- STEP 1: Inspect order items that reference inactive products
-- Review this list carefully before proceeding
-- ============================================================
SELECT 
    oi.id AS order_item_id,
    oi.order_id,
    oi.product_id,
    oi.name AS product_name,
    oi.quantity,
    oi.unit_price,
    p.name AS current_product_name,
    p.is_active
FROM order_items oi
JOIN products p ON p.id = oi.product_id
WHERE p.is_active = false;

-- STEP 2: Delete cart items referencing inactive products
-- These are safe to remove - carts are ephemeral
-- ============================================================
DELETE FROM cart_items 
WHERE product_id IN (
    SELECT id FROM products WHERE is_active = false
);

-- STEP 3: Delete order items referencing inactive products
-- Uncomment the line below ONLY if you confirm these are test orders to remove
-- ============================================================
DELETE FROM order_items 
WHERE product_id IN (
    SELECT id FROM products WHERE is_active = false
);

-- STEP 4: Permanently delete all inactive products
-- ============================================================
DELETE FROM products 
WHERE is_active = false;

-- STEP 5: Verify - should return 0 rows
-- ============================================================
SELECT 
    'Inactive products remaining:' AS status,
    COUNT(*) AS count 
FROM products 
WHERE is_active = false

UNION ALL

SELECT 
    'Total active products:' AS status,
    COUNT(*) AS count 
FROM products 
WHERE is_active = true

UNION ALL

SELECT 
    'Total products deleted (this session):' AS status,
    0 AS count;
