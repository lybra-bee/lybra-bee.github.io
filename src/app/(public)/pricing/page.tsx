'use client';

export default function PricingPage() {
  const handleSubscribe = async () => {
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isSubscription: true, priceId: 'price_placeholder' }), // Replaced with actual price ID in production
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error('Subscription error:', err);
    }
  };

  return (
    <div className="container mx-auto px-4 py-16 text-center">
      <h1 className="text-4xl font-bold mb-4">AquaFit Premium</h1>
      <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
        Get unlimited access to our entire library of 3D printable aquarium decor.
      </p>

      <div className="max-w-md mx-auto border rounded-xl shadow-lg overflow-hidden">
        <div className="bg-blue-600 text-white p-8">
          <h2 className="text-2xl font-bold mb-2">3D Decor Subscription</h2>
          <div className="text-5xl font-extrabold mb-2">$9.99<span className="text-xl font-normal opacity-80">/mo</span></div>
        </div>
        <div className="p-8 bg-white text-left">
          <ul className="space-y-4 mb-8">
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span> Unlimited downloads
            </li>
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span> Exclusive modular castles
            </li>
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span> Cancel anytime
            </li>
          </ul>
          <button
            onClick={handleSubscribe}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Subscribe Now
          </button>
        </div>
      </div>
    </div>
  );
}
