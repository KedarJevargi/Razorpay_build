-- Clear existing data (for iterative seeding)
TRUNCATE TABLE inventory, cart_items, carts, order_items, orders, products, merchant_policies, promotions, customers, merchants, knowledge_documents CASCADE;

-- Insert Merchant
INSERT INTO merchants (id, name, description) 
VALUES ('merch_adventurehub', 'AdventureHub', 'Premium outdoor gear, travel essentials, and adventure equipment for every kind of explorer.');

-- Insert Customers
INSERT INTO customers (id, name, email, phone) VALUES
('cust_001', 'Alice Explorer', 'alice@example.com', '+919876543001'),
('cust_002', 'Bob Trekker', 'bob@example.com', '+919876543002'),
('cust_003', 'Charlie Climber', 'charlie@example.com', '+919876543003'),
('cust_004', 'Diana Nomad', 'diana@example.com', '+919876543004'),
('cust_005', 'Eve Ultralight', 'eve@example.com', '+919876543005'),
('cust_006', 'Frank Guide', 'frank@example.com', '+919876543006'),
('cust_007', 'Grace Weekender', 'grace@example.com', '+919876543007');

-- =============================================
-- PRODUCTS (25 items across 7 categories)
-- =============================================

-- Category: Backpacks
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_pack20', 'merch_adventurehub', 'UltraLight 20L', 'Minimalist 20L ultralight daypack for fast-and-light hikers. Roll-top closure with side mesh pockets.', 2499.00, 'backpacks', '{"waterproof": false, "capacity": "20L", "weight": "0.5kg"}'),
('prod_pack25w', 'merch_adventurehub', 'Women''s DayPack 25L', 'Ergonomically designed 25L daypack with women-specific shoulder straps and hip belt.', 3299.00, 'backpacks', '{"waterproof": false, "capacity": "25L", "weight": "0.8kg", "fit": "women"}'),
('prod_pack30', 'merch_adventurehub', 'TrailPack 30L', 'Lightweight 30L daypack with hydration sleeve.', 3799.00, 'backpacks', '{"waterproof": false, "capacity": "30L", "weight": "0.9kg"}'),
('prod_pack40', 'merch_adventurehub', 'SummitPro 40L', 'Durable 40L multi-day trekking backpack.', 4299.00, 'backpacks', '{"waterproof": true, "capacity": "40L", "weight": "1.4kg"}'),
('prod_pack60', 'merch_adventurehub', 'Expedition 60L', 'Heavy-duty 60L expedition pack with external frame, rain cover included. Built for Himalayan treks.', 7999.00, 'backpacks', '{"waterproof": true, "capacity": "60L", "weight": "2.2kg", "frame": "external"}');

-- Category: Tents
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_tent1p', 'merch_adventurehub', 'Solo Bivy Tent', 'Ultra-compact 1-person bivy tent weighing just 1.2kg. Perfect for solo trekkers.', 5499.00, 'tents', '{"capacity": "1-person", "weight": "1.2kg", "season": "3-season"}'),
('prod_tent2p', 'merch_adventurehub', 'Alpine 2-Person Tent', 'Lightweight 3-season tent with double-wall design and two vestibules.', 8499.00, 'tents', '{"capacity": "2-person", "weight": "2.1kg", "season": "3-season"}'),
('prod_tent4p', 'merch_adventurehub', 'BaseCamp 4-Person Tent', 'Spacious 4-person family camping tent with standing height and two rooms.', 12999.00, 'tents', '{"capacity": "4-person", "weight": "5.5kg", "season": "3-season"}'),
('prod_hammock', 'merch_adventurehub', 'TreeHouse Hammock Tent', 'Suspended camping hammock with integrated mosquito net and rain fly. Unique jungle camping experience.', 4999.00, 'tents', '{"capacity": "1-person", "weight": "1.8kg", "season": "3-season", "type": "hammock"}');

-- Category: Sleeping
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_sleep0', 'merch_adventurehub', 'CompactSleep Bag 0°C', 'Mummy-style sleeping bag rated to 0°C. Synthetic insulation, compresses to 8L.', 3499.00, 'sleeping', '{"temperature_rating": "0°C", "weight": "1.3kg", "insulation": "synthetic"}'),
('prod_sleep10', 'merch_adventurehub', 'UltraWarm Bag -10°C', 'Down-filled sleeping bag rated to -10°C for high-altitude winter camping.', 6499.00, 'sleeping', '{"temperature_rating": "-10°C", "weight": "1.6kg", "insulation": "down"}'),
('prod_liner', 'merch_adventurehub', 'Silk Sleeping Liner', 'Premium silk liner adds 5-8°C warmth to any sleeping bag. Also works standalone in hostels.', 1999.00, 'sleeping', '{"weight": "0.15kg", "material": "silk"}'),
('prod_mat', 'merch_adventurehub', 'AirRest Inflatable Mat', 'Self-inflating sleeping mat with R-value 3.5. Packs to 1L.', 2999.00, 'sleeping', '{"weight": "0.5kg", "r_value": 3.5, "thickness": "7cm"}');

-- Category: Footwear
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_shoes_trail', 'merch_adventurehub', 'TrailRunner Shoes', 'Lightweight trail running shoes with Vibram sole and breathable mesh upper.', 3999.00, 'footwear', '{"weight": "320g", "sole": "Vibram", "waterproof": false}'),
('prod_boots_alpine', 'merch_adventurehub', 'Alpine Trek Boots', 'Full-ankle support leather boots with Gore-Tex lining. Crampon-compatible.', 6999.00, 'footwear', '{"weight": "680g", "sole": "Vibram", "waterproof": true, "crampon_compatible": true}'),
('prod_sandals', 'merch_adventurehub', 'Camp Recovery Sandals', 'Lightweight EVA sandals for campsite recovery after long hikes.', 999.00, 'footwear', '{"weight": "180g", "material": "EVA"}');

-- Category: Clothing
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_jacket', 'merch_adventurehub', 'StormShield Windbreaker', 'Packable windbreaker jacket with DWR coating. Weighs just 200g and fits in its own pocket.', 2499.00, 'clothing', '{"weight": "200g", "waterproof_rating": "5000mm", "packable": true}'),
('prod_thermal', 'merch_adventurehub', 'ThermoBase Merino Layer', 'Merino wool base layer top. Natural odor resistance and temperature regulation.', 2999.00, 'clothing', '{"weight": "180g", "material": "merino_wool"}'),
('prod_pants', 'merch_adventurehub', 'FlexHike Convertible Pants', 'Quick-dry hiking pants with zip-off legs that convert to shorts. UPF 50+ sun protection.', 1999.00, 'clothing', '{"weight": "280g", "upf": 50, "convertible": true}');

-- Category: Accessories
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_raincover', 'merch_adventurehub', 'Universal Rain Cover', 'Waterproof rain cover for backpacks 30L-50L.', 299.00, 'accessories', '{"waterproof": true, "fits": "30L-50L"}'),
('prod_poles', 'merch_adventurehub', 'Carbon Trekking Poles', 'Adjustable carbon fiber trekking poles (pair).', 1499.00, 'accessories', '{"material": "carbon fiber", "weight": "400g"}'),
('prod_headlamp', 'merch_adventurehub', 'LumiPro Headlamp 300', 'Rechargeable 300-lumen headlamp with red-light mode. IPX6 water resistant. 40-hour battery.', 1299.00, 'accessories', '{"lumens": 300, "battery_life": "40h", "weight": "75g", "waterproof_rating": "IPX6"}'),
('prod_filter', 'merch_adventurehub', 'PureStream Water Filter', 'Portable water filter bottle that removes 99.99% bacteria and protozoa. 1L capacity.', 1799.00, 'accessories', '{"capacity": "1L", "weight": "200g", "filter_life": "4000L"}'),
('prod_firstaid', 'merch_adventurehub', 'TrailMed First Aid Kit', 'Compact 42-piece first aid kit designed for outdoor adventures. Includes splint, whistle, and emergency blanket.', 899.00, 'accessories', '{"pieces": 42, "weight": "350g"}');

-- Category: Cooking
INSERT INTO products (id, merchant_id, name, description, price, category, attributes) VALUES
('prod_stove', 'merch_adventurehub', 'JetBoil Portable Stove', 'Compact camping stove with integrated wind guard. Boils 500ml in 2 minutes.', 3499.00, 'cooking', '{"weight": "340g", "fuel": "isobutane", "boil_time": "2min"}'),
('prod_cookset', 'merch_adventurehub', 'Titanium Cookset 2-Person', 'Ultralight titanium pot and pan set for 2 people. Nesting design saves space.', 2499.00, 'cooking', '{"weight": "280g", "material": "titanium", "pieces": 4}'),
('prod_flask', 'merch_adventurehub', 'ThermoFlask 750ml', 'Double-wall vacuum insulated flask. Keeps drinks hot 12h or cold 24h.', 1299.00, 'cooking', '{"capacity": "750ml", "weight": "350g", "hot_retention": "12h", "cold_retention": "24h"}');

-- =============================================
-- INVENTORY
-- =============================================
INSERT INTO inventory (product_id, quantity, warehouse) VALUES
-- Backpacks
('prod_pack20', 60, 'WH-Delhi'),
('prod_pack25w', 30, 'WH-Mumbai'),
('prod_pack30', 42, 'WH-Delhi'),
('prod_pack40', 15, 'WH-Delhi'),
('prod_pack60', 10, 'WH-Mumbai'),
-- Tents
('prod_tent1p', 20, 'WH-Delhi'),
('prod_tent2p', 8, 'WH-Mumbai'),
('prod_tent4p', 5, 'WH-Mumbai'),
('prod_hammock', 18, 'WH-Delhi'),
-- Sleeping
('prod_sleep0', 25, 'WH-Delhi'),
('prod_sleep10', 12, 'WH-Mumbai'),
('prod_liner', 50, 'WH-Delhi'),
('prod_mat', 35, 'WH-Delhi'),
-- Footwear
('prod_shoes_trail', 40, 'WH-Delhi'),
('prod_boots_alpine', 15, 'WH-Mumbai'),
('prod_sandals', 80, 'WH-Delhi'),
-- Clothing
('prod_jacket', 45, 'WH-Delhi'),
('prod_thermal', 30, 'WH-Mumbai'),
('prod_pants', 55, 'WH-Delhi'),
-- Accessories
('prod_raincover', 120, 'WH-Delhi'),
('prod_poles', 35, 'WH-Delhi'),
('prod_headlamp', 70, 'WH-Delhi'),
('prod_filter', 40, 'WH-Mumbai'),
('prod_firstaid', 60, 'WH-Delhi'),
-- Cooking
('prod_stove', 22, 'WH-Mumbai'),
('prod_cookset', 18, 'WH-Delhi'),
('prod_flask', 65, 'WH-Delhi');

-- =============================================
-- PROMOTIONS (6 total)
-- =============================================
INSERT INTO promotions (id, merchant_id, type, value, min_order_value, max_discount, active) VALUES
('promo_welcome10', 'merch_adventurehub', 'percentage_discount', 10.00, 2000.00, NULL, true),
('promo_tentbundle', 'merch_adventurehub', 'flat_discount', 500.00, 8000.00, NULL, true),
('promo_monsoon25', 'merch_adventurehub', 'percentage_discount', 25.00, 5000.00, 2000.00, true),
('promo_firstbuy', 'merch_adventurehub', 'flat_discount', 300.00, 1500.00, NULL, true),
('promo_bigspend', 'merch_adventurehub', 'percentage_discount', 15.00, 10000.00, 3000.00, true),
('promo_accessory20', 'merch_adventurehub', 'percentage_discount', 20.00, 1000.00, 500.00, true);

-- =============================================
-- POLICIES
-- =============================================
INSERT INTO merchant_policies (id, merchant_id, policy_type, policy_key, policy_value) VALUES
('pol_txn_limit', 'merch_adventurehub', 'transaction', 'max_autonomous_txn', '{"limit": 15000}'),
('pol_disc_limit', 'merch_adventurehub', 'discount', 'max_auto_discount_pct', '{"limit": 25}'),
('pol_refund_limit', 'merch_adventurehub', 'refund', 'max_auto_refund', '{"limit": 2000}'),
('pol_free_shipping', 'merch_adventurehub', 'shipping', 'free_shipping_threshold', '{"limit": 2000}'),
('pol_express_cities', 'merch_adventurehub', 'shipping', 'express_delivery_cities', '{"cities": ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad"]}');
