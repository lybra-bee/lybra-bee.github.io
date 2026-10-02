import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 bg-black text-white">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                  Aquarium-Safe 3D Printable Scapes & Functional Gear
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-400 md:text-xl">
                  Instant STL & 3MF downloads engineered for aquarists. Tested for fish safety, neutral buoyancy, and zero water toxicity.
                </p>
              </div>
              <div className="space-x-4 mt-8 flex flex-wrap justify-center gap-4">
                <Link
                  href="/catalog"
                  className="inline-flex h-12 items-center justify-center rounded-md bg-white px-8 text-sm font-medium text-black shadow transition-colors hover:bg-gray-200"
                >
                  Browse STL Catalog
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex h-12 items-center justify-center rounded-md border border-gray-600 px-8 text-sm font-medium shadow-sm transition-colors hover:bg-gray-800 focus-visible:outline-none"
                >
                  Join 3D Print Pass ($9.99/mo)
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Badges Section */}
        <section className="w-full py-12 bg-zinc-900">
           <div className="container px-4 md:px-6 mx-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 text-center text-gray-300">
                 <div className="flex flex-col items-center gap-2">
                    <span className="text-3xl">⚡</span>
                    <h3 className="font-semibold text-white">Instant Download</h3>
                    <p className="text-sm">Direct access to STL & 3MF files post-checkout.</p>
                 </div>
                 <div className="flex flex-col items-center gap-2">
                    <span className="text-3xl">🐟</span>
                    <h3 className="font-semibold text-white">Fish-Safe Geometry</h3>
                    <p className="text-sm">Chamfered/rounded edges to protect delicate fins.</p>
                 </div>
                 <div className="flex flex-col items-center gap-2">
                    <span className="text-3xl">🧲</span>
                    <h3 className="font-semibold text-white">Sink-Optimized</h3>
                    <p className="text-sm">Designed for complete submersion without chemical leaching.</p>
                 </div>
                 <div className="flex flex-col items-center gap-2">
                    <span className="text-3xl">📐</span>
                    <h3 className="font-semibold text-white">Scale-Ready</h3>
                    <p className="text-sm">Seamlessly fit ADA, UNS, and rimless aquarium dimensions.</p>
                 </div>
              </div>
           </div>
        </section>

        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6 mx-auto text-center">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl mb-12 text-white">Featured Items</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Placeholder for featured items */}
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="border rounded-lg p-4 shadow-sm hover:shadow-md transition">
                  <div className="bg-gray-200 w-full h-48 rounded-md mb-4 flex items-center justify-center text-gray-500">Image</div>
                  <h3 className="font-semibold text-lg">Product {i}</h3>
                  <p className="text-gray-500">$29.99</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
