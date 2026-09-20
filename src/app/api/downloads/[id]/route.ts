import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

import { NextRequest } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id: listingId } = await params;
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check if listing exists and is decor_3d
  const { data: listing } = await supabase.from('listings').select('type').eq('id', listingId).single();
  if (!listing || listing.type !== 'decor_3d') {
    return NextResponse.json({ error: 'Not found or not a digital product' }, { status: 404 });
  }

  // Condition 1: Check if user has paid order for this item
  const { data: orders } = await supabase
    .from('orders')
    .select('id')
    .eq('buyer_id', user.id)
    .eq('listing_id', listingId)
    .eq('status', 'paid');

  let hasAccess = orders && orders.length > 0;

  // Condition 2: Check if user has active subscription
  if (!hasAccess) {
    const { data: subscriptions } = await supabase
      .from('subscriptions')
      .select('id')
      .eq('user_id', user.id)
      .eq('status', 'active');

    if (subscriptions && subscriptions.length > 0) {
      hasAccess = true;
    }
  }

  if (!hasAccess) {
    return NextResponse.json({ error: 'Payment or active subscription required' }, { status: 403 });
  }

  // Use admin client to bypass RLS for fetching file_url
  const { createServerClient } = await import('@supabase/ssr');
  const supabaseAdmin = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY || 'placeholder',
    {
      cookies: {
        getAll: () => [],
        setAll: () => {},
      },
    }
  );

  // Get the file details
  const { data: listingFiles } = await supabaseAdmin
    .from('listing_files')
    .select('file_url')
    .eq('listing_id', listingId)
    .single();

  if (!listingFiles || !listingFiles.file_url) {
     return NextResponse.json({ error: 'File not found' }, { status: 404 });
  }

  // Generate signed URL (expires in 60 seconds)
  // Also using admin client since users may not have direct access to generate signed urls on their own without RLS bypass or proper storage policies
  const { data, error } = await supabaseAdmin
    .storage
    .from('3d_files')
    .createSignedUrl(listingFiles.file_url, 60);

  if (error || !data) {
    return NextResponse.json({ error: 'Failed to generate download link' }, { status: 500 });
  }

  return NextResponse.redirect(data.signedUrl);
}
