'use client';

export default function PricingPage() {
  const handleSubscribe = async (priceId: string) => {
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isSubscription: true, priceId: priceId }),
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

      <div className="max-w-6xl mx-auto overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

          {/* Tier 1 */}
          <div className="border border-gray-700 rounded-xl bg-zinc-900 p-8 flex flex-col">
             <h2 className="text-2xl font-bold text-white mb-2">Pay Per File</h2>
             <div className="text-gray-400 mb-6">Default</div>
             <div className="text-4xl font-extrabold text-white mb-6">Varies</div>
             <ul className="space-y-4 mb-8 text-gray-300 text-left flex-1">
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Lifetime download access per file</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Personal use only</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Print guidelines included</li>
             </ul>
             <a href="/catalog" className="w-full block text-center bg-gray-700 text-white py-3 rounded-lg font-semibold hover:bg-gray-600 transition">
                Browse Catalog
             </a>
          </div>

          {/* Tier 2 */}
          <div className="border border-blue-500 rounded-xl bg-blue-900/20 p-8 flex flex-col relative transform md:-translate-y-4 shadow-2xl">
             <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-bold tracking-wide">RECOMMENDED</div>
             <h2 className="text-2xl font-bold text-white mb-2">Personal 3D Pass</h2>
             <div className="text-gray-400 mb-6">Or $89/year</div>
             <div className="text-4xl font-extrabold text-white mb-6">$9.99<span className="text-lg font-normal text-gray-400">/mo</span></div>
             <ul className="space-y-4 mb-8 text-gray-300 text-left flex-1">
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Unlimited downloads (current & future)</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Slicer print-profile presets</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Cancel anytime</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Personal use only</li>
             </ul>
             <button onClick={() => handleSubscribe('price_personal')} className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                Subscribe Now
             </button>
          </div>

          {/* Tier 3 */}
          <div className="border border-gray-700 rounded-xl bg-zinc-900 p-8 flex flex-col">
             <h2 className="text-2xl font-bold text-white mb-2">Commercial Tier</h2>
             <div className="text-gray-400 mb-6">For sellers</div>
             <div className="text-4xl font-extrabold text-white mb-6">$29.99<span className="text-lg font-normal text-gray-400">/mo</span></div>
             <ul className="space-y-4 mb-8 text-gray-300 text-left flex-1">
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Full library access</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Commercial license (sell physical prints)</li>
                <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Sell on Etsy & local stores</li>
             </ul>
             <button onClick={() => handleSubscribe('price_commercial')} className="w-full bg-gray-100 text-black py-3 rounded-lg font-semibold hover:bg-gray-300 transition">
                Get Commercial License
             </button>
          </div>

        </div>
      </div>
    </div>
  );
}
