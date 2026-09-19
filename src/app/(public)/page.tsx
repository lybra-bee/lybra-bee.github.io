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
                  AquaFit
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-400 md:text-xl">
                  See it fit before you buy it. Unique aquarium hardscape and 3D printable decor.
                </p>
              </div>
              <div className="space-x-4">
                <Link
                  href="/catalog"
                  className="inline-flex h-9 items-center justify-center rounded-md bg-white px-4 py-2 text-sm font-medium text-black shadow transition-colors hover:bg-gray-200"
                >
                  Shop Now
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex h-9 items-center justify-center rounded-md border border-gray-600 px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-gray-800 focus-visible:outline-none"
                >
                  Subscribe for 3D Decor
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6 mx-auto text-center">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl mb-12">Featured Items</h2>
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
