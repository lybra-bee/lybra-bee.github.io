import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder', {
  apiVersion: '2025-02-24.acacia' as Stripe.LatestApiVersion,
});

export async function POST(request: Request) {
  try {
    const { listingId, priceId, isSubscription } = await request.json();
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (isSubscription) {
      const session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        line_items: [
          {
            price: priceId, // Stripe Price ID for subscription
            quantity: 1,
          },
        ],
        mode: 'subscription',
        success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/checkout/success`,
        cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/checkout/cancel`,
        client_reference_id: user.id,
      });

      return NextResponse.json({ url: session.url });
    } else {
      // Fetch listing details for one-time purchase
      const { data: listing } = await supabase.from('listings').select('*').eq('id', listingId).single();
      if (!listing) return NextResponse.json({ error: 'Listing not found' }, { status: 404 });

      const session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        line_items: [
          {
            price_data: {
              currency: listing.currency.toLowerCase(),
              product_data: {
                name: listing.title,
                description: listing.description || undefined,
              },
              unit_amount: Math.round(listing.price * 100), // Stripe expects cents
            },
            quantity: 1,
          },
        ],
        mode: 'payment',
        success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/checkout/success`,
        cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/checkout/cancel`,
        client_reference_id: user.id,
        metadata: {
          listing_id: listing.id,
        },
      });

      return NextResponse.json({ url: session.url });
    }
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : 'Unknown error' }, { status: 500 });
  }
}
