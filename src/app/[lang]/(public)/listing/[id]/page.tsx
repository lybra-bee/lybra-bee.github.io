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

          <div className="bg-gray-50 p-4 rounded-lg">
             <h3 className="font-semibold mb-2">Item Dimensions</h3>
             <p>{dimensions.length} x {dimensions.width} x {dimensions.height} cm (L x W x H)</p>
          </div>

          <TankFitChecker itemDimensions={dimensions} />

          <BuyButton listingId={listing.id} priceId="placeholder" type={listing.type} />
        </div>
      </div>
    </div>
  );
}
