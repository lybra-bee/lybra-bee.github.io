-- Update Listings table to enforce decor_3d and add 3D specific fields
ALTER TABLE listings ALTER COLUMN type SET DEFAULT 'decor_3d';

-- We update existing rows if any
UPDATE listings SET type = 'decor_3d';

-- Re-apply check constraint to only allow decor_3d
ALTER TABLE listings DROP CONSTRAINT IF EXISTS listings_type_check;
ALTER TABLE listings ADD CONSTRAINT listings_type_check CHECK (type = 'decor_3d');

-- Update category to use the new 3D categories
ALTER TABLE listings DROP COLUMN IF EXISTS category;
ALTER TABLE listings ADD COLUMN category TEXT CHECK (category IN ('functional_gear', 'fish_caves', 'aquascaping_decor'));

-- Add 3D-specific metadata
ALTER TABLE listings ADD COLUMN recommended_filament TEXT;
ALTER TABLE listings ADD COLUMN supports_required BOOLEAN DEFAULT false;
ALTER TABLE listings ADD COLUMN infill_recommendation TEXT;
ALTER TABLE listings ADD COLUMN min_bed_size_mm JSONB; -- [x, y, z]
ALTER TABLE listings ADD COLUMN included_formats TEXT[];

-- Update listing_files format check to include 3mf
ALTER TABLE listing_files DROP CONSTRAINT IF EXISTS listing_files_format_check;
ALTER TABLE listing_files ADD CONSTRAINT listing_files_format_check CHECK (format IN ('stl', 'obj', 'fbx', '3mf', 'zip'));


-- Seed dummy profile for the seller
DO $$
DECLARE
    admin_id UUID := '00000000-0000-0000-0000-000000000001';
BEGIN
    INSERT INTO auth.users (id, email) VALUES (admin_id, 'admin@aquafit.com') ON CONFLICT DO NOTHING;
    INSERT INTO profiles (id, email, role) VALUES (admin_id, 'admin@aquafit.com', 'admin') ON CONFLICT DO NOTHING;

    -- Seed Listings
    INSERT INTO listings (seller_id, type, title, description, price, currency, dimensions_cm, category, recommended_filament, supports_required, infill_recommendation, min_bed_size_mm, included_formats, status)
    VALUES
    (admin_id, 'decor_3d', 'Shrimp Pyramid Shelter & Breeding Tower', 'Perfect shelter for Neocaridina and Caridina shrimp.', 4.99, 'USD', '{"length": 8, "width": 8, "height": 7}', 'fish_caves', 'PETG (Food-Safe) / Non-toxic PLA', false, '100% infill to sink', '[180, 180, 180]', '{"stl", "3mf"}', 'active'),
    (admin_id, 'decor_3d', 'Modular Pleco & Cichlid Spawning Cave', 'Stackable and expandable spawning caves.', 6.49, 'USD', '{"length": 16, "width": 6, "height": 5}', 'fish_caves', 'PETG', true, '100% infill to sink', '[180, 180, 180]', '{"stl", "3mf"}', 'active'),
    (admin_id, 'decor_3d', 'Rimless Tank Surface Skimmer Guard', 'Prevents baby shrimp and small fish from being sucked into the skimmer.', 3.99, 'USD', '{"length": 4, "width": 4, "height": 6}', 'functional_gear', 'PETG', false, '100% infill to sink', '[180, 180, 180]', '{"stl"}', 'active'),
    (admin_id, 'decor_3d', 'Floating Plant Corral & Feeding Ring System', 'Keeps floating plants organized and creates a clear area for feeding.', 4.99, 'USD', '{"length": 12, "width": 12, "height": 2}', 'functional_gear', 'PETG (Food-Safe) / Non-toxic PLA', false, '15% infill (needs to float)', '[180, 180, 180]', '{"stl", "3mf"}', 'active'),
    (admin_id, 'decor_3d', 'Zen Ancient Ruin Archway (Aquascape Centerpiece)', 'A beautiful centerpiece optimized for moss growth.', 8.99, 'USD', '{"length": 22, "width": 12, "height": 18}', 'aquascaping_decor', 'PETG', true, 'Hollow with ballast pocket', '[256, 256, 256]', '{"stl", "obj"}', 'active'),
    (admin_id, 'decor_3d', 'Modular Magnetic Anubias / Buce Ledge', 'Attach epiphytes directly to the glass.', 5.49, 'USD', '{"length": 10, "width": 7, "height": 4}', 'functional_gear', 'PETG', false, '100% infill to sink', '[180, 180, 180]', '{"stl", "3mf"}', 'active');
END $$;
