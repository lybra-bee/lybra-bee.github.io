import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createServerClient } from '@supabase/ssr';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder', {
  apiVersion: '2025-02-24.acacia' as Stripe.LatestApiVersion,
});

export async function POST(req: Request) {
  // Create a service role client to bypass RLS for webhook operations
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

  const body = await req.text(); // Read raw text for webhook signature verification
  const reqHeaders = headers();
  const signature = (await reqHeaders).get('stripe-signature') as string;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('Webhook signature verification failed:', message);
    return NextResponse.json({ error: `Webhook Error: ${message}` }, { status: 400 });
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;

        if (session.mode === 'payment' && session.metadata?.listing_id) {
          // Record one-time order
          await supabaseAdmin.from('orders').insert({
            buyer_id: session.client_reference_id,
            listing_id: session.metadata.listing_id,
            amount: session.amount_total ? session.amount_total / 100 : 0,
            status: 'paid',
            stripe_session_id: session.id,
          });

          // Optionally mark hardscape as sold
          // We would need to check if listing is hardscape first, but for now we skip this complexity.
        }
        break;
      }

      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription;
        // Find user by stripe customer id or client_reference_id if we passed it (but we don't in subscription webhooks usually without metadata).
        // For simplicity in MVP, assume we look up or pass user_id in metadata during checkout session and fetch it here.
        // As a fallback, this is just scaffolded:
        console.log('Subscription updated:', subscription.id);
        break;
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription;
        await supabaseAdmin.from('subscriptions').update({ status: 'canceled' }).eq('stripe_subscription_id', subscription.id);
        break;
      }
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json({ error: 'Webhook handler failed' }, { status: 500 });
  }
}
