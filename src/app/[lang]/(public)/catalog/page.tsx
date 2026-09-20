import { createClient } from '@/lib/supabase/server';
import Link from 'next/link';

export default async function CatalogPage() {
  const supabase = createClient();
  const { data: listings } = await supabase.from('listings').select('*').eq('status', 'active');

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Catalog</h1>

      <div className="flex flex-col md:flex-row gap-8">
        <aside className="w-full md:w-64 space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Type</h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="checkbox" /> Hardscape
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" /> 3D Decor
              </label>
            </div>
          </div>
          {/* Add more filters here later */}
        </aside>

        <main className="flex-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings?.map((listing) => (
              <Link href={`/listing/${listing.id}`} key={listing.id} className="block group">
                <div className="border rounded-lg p-4 shadow-sm group-hover:shadow-md transition">
                  <div className="bg-gray-200 w-full h-48 rounded-md mb-4 flex items-center justify-center text-gray-500">Image Placeholder</div>
                  <h3 className="font-semibold text-lg">{listing.title}</h3>
                  <p className="text-gray-500">${listing.price}</p>
                  <p className="text-sm text-gray-400 capitalize">{listing.type.replace('_', ' ')}</p>
                </div>
              </Link>
            ))}
            {!listings?.length && (
              <div className="col-span-full text-center py-12 text-gray-500">
                No active listings found.
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
