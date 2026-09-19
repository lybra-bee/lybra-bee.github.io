-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles table
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer', 'seller', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Listings table
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('hardscape', 'decor_3d')),
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    dimensions_cm JSONB NOT NULL, -- {length, width, height}
    category TEXT,
    style_tags TEXT[],
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'sold')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Listing Images table
CREATE TABLE listing_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID REFERENCES listings(id) ON DELETE CASCADE NOT NULL,
    url TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- Listing Files table
CREATE TABLE listing_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID REFERENCES listings(id) ON DELETE CASCADE NOT NULL,
    file_url TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('stl', 'obj', 'fbx')),
    -- Ensure files are only for decor_3d (this might require a trigger, but simple check is okay for now if application enforces it)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    listing_id UUID REFERENCES listings(id) ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'fulfilled')),
    stripe_session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tank Presets table
CREATE TABLE tank_presets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    length_cm DECIMAL(5, 2) NOT NULL,
    width_cm DECIMAL(5, 2) NOT NULL,
    height_cm DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Set up Row Level Security (RLS)

-- Profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public profiles are viewable by everyone." ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can insert their own profile." ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile." ON profiles FOR UPDATE USING (auth.uid() = id);

-- Listings
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Active listings are viewable by everyone." ON listings FOR SELECT USING (status = 'active');
CREATE POLICY "Sellers can view own listings." ON listings FOR SELECT USING (auth.uid() = seller_id);
CREATE POLICY "Admins can view all listings." ON listings FOR SELECT USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
CREATE POLICY "Admins can insert listings." ON listings FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
CREATE POLICY "Admins can update listings." ON listings FOR UPDATE USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- Listing Images
ALTER TABLE listing_images ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Images of active listings are viewable by everyone." ON listing_images FOR SELECT USING (EXISTS (SELECT 1 FROM listings WHERE listings.id = listing_images.listing_id AND listings.status = 'active'));
CREATE POLICY "Admins can insert images." ON listing_images FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
CREATE POLICY "Admins can update images." ON listing_images FOR UPDATE USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
CREATE POLICY "Admins can delete images." ON listing_images FOR DELETE USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- Listing Files
ALTER TABLE listing_files ENABLE ROW LEVEL SECURITY;
-- For download, the server will fetch via service role. Admin can view.
CREATE POLICY "Admins can view files." ON listing_files FOR SELECT USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
CREATE POLICY "Admins can insert files." ON listing_files FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- Orders
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own orders." ON orders FOR SELECT USING (auth.uid() = buyer_id);
CREATE POLICY "Admins can view all orders." ON orders FOR SELECT USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));
-- Orders should be inserted/updated securely by the server, not directly by clients.

-- Subscriptions
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own subscriptions." ON subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Admins can view all subscriptions." ON subscriptions FOR SELECT USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- Tank Presets
ALTER TABLE tank_presets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own presets." ON tank_presets FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own presets." ON tank_presets FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own presets." ON tank_presets FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own presets." ON tank_presets FOR DELETE USING (auth.uid() = user_id);

-- Storage Buckets and RLS
-- Note: Requires `storage` schema to be available in Supabase.
INSERT INTO storage.buckets (id, name, public) VALUES ('listing_images', 'listing_images', true) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public) VALUES ('3d_files', '3d_files', false) ON CONFLICT (id) DO NOTHING;

-- Public read access for listing_images
CREATE POLICY "Images are publicly accessible." ON storage.objects FOR SELECT USING (bucket_id = 'listing_images');

-- Admins can insert to listing_images
CREATE POLICY "Admins can upload images." ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = 'listing_images' AND EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin')
);

-- Admins can insert to 3d_files
CREATE POLICY "Admins can upload 3d files." ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = '3d_files' AND EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin')
);

-- Signed URLs bypass RLS on objects when generated by Service Role, but if we need explicit read for service role it is usually granted by default.
