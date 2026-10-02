import { createClient } from '@/lib/supabase/server';
import { notFound } from 'next/navigation';
import TankFitChecker from '@/components/listing/TankFitChecker';
import BuyButton from '@/components/listing/BuyButton';

export default async function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = createClient();
  const { data: listing } = await supabase
    .from('listings')
    .select('*, listing_images(*)')
    .eq('id', id)
    .single();

  if (!listing || listing.status !== 'active') {
    notFound();
  }

  const dimensions = listing.dimensions_cm as { length: number; width: number; height: number };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        {/* Images */}
        <div className="space-y-4">
          <div className="bg-gray-100 aspect-square rounded-lg flex items-center justify-center text-gray-400">
            {listing.listing_images?.[0] ? 'Image' : 'No Image'}
          </div>
          <div className="flex gap-4 overflow-x-auto">
             {/* Thumbnail placeholders */}
             {[1, 2, 3].map(i => (
                <div key={i} className="bg-gray-100 w-24 h-24 rounded flex-shrink-0" />
             ))}
          </div>
        </div>

        {/* Details */}
        <div className="space-y-6">
          <h1 className="text-3xl font-bold">{listing.title}</h1>
          <p className="text-2xl font-semibold">${listing.price}</p>
          <div className="prose max-w-none">
            <p>{listing.description}</p>
          </div>

          <div className="bg-zinc-900 border border-gray-800 p-6 rounded-lg text-white">
             <h3 className="font-semibold mb-4 text-lg border-b border-gray-800 pb-2">3D Print Technical Specs</h3>
             <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-center gap-2">
                   <span className="font-semibold text-white">Dimensions:</span>
                   {dimensions.length} x {dimensions.width} x {dimensions.height} cm
                </li>
                {listing.recommended_filament && (
                   <li className="flex items-center gap-2"><span className="font-semibold text-white">Recommended Filament:</span> {listing.recommended_filament}</li>
                )}
                {listing.infill_recommendation && (
                   <li className="flex items-center gap-2"><span className="font-semibold text-white">Infill:</span> {listing.infill_recommendation}</li>
                )}
                <li className="flex items-center gap-2">
                   <span className="font-semibold text-white">Supports:</span>
                   {listing.supports_required ? <span className="text-yellow-400">Yes (Required)</span> : <span className="text-green-400 border border-green-800 bg-green-900/30 px-2 py-0.5 rounded text-xs">No Supports Needed</span>}
                </li>
                {listing.min_bed_size_mm && (
                   <li className="flex items-center gap-2"><span className="font-semibold text-white">Min Bed Size:</span> {JSON.parse(JSON.stringify(listing.min_bed_size_mm)).join('x')} mm</li>
                )}
             </ul>
             <div className="mt-4 pt-4 border-t border-gray-800 text-xs text-gray-500">
                License: Personal Use Only (Single User)
             </div>
          </div>

          <TankFitChecker itemDimensions={dimensions} />

          <BuyButton listingId={listing.id} priceId="placeholder" type={listing.type} />
        </div>
      </div>
    </div>
  );
}
