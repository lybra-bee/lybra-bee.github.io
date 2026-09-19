'use client';

export default function BuyButton({ listingId, priceId }: { listingId: string, priceId: string, type: string }) {
  const handleBuy = async () => {
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ listingId, priceId, isSubscription: false }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error('Checkout error:', err);
    }
  };

  return (
    <button
      onClick={handleBuy}
      className="w-full bg-black text-white py-3 rounded-lg font-semibold text-lg hover:bg-gray-800 transition"
    >
      Buy Now
    </button>
  );
}
