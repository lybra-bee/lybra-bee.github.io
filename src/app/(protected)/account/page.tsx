import { createClient } from '@/lib/supabase/server';

export default async function AccountPage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) return null; // Middleware will redirect, but TypeScript needs this

  const { data: orders } = await supabase
    .from('orders')
    .select('*, listings(*)')
    .eq('buyer_id', user.id);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Account</h1>

      <div className="mb-8 p-6 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-semibold mb-2">Profile</h2>
        <p className="text-gray-600">{user.email}</p>
        <form action="/auth/signout" method="post" className="mt-4">
          <button type="submit" className="text-sm text-red-600 hover:underline">Sign Out</button>
        </form>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">My Purchases</h2>
        {orders && orders.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {orders.map((order) => (
              <div key={order.id} className="border p-4 rounded-lg">
                <h3 className="font-semibold">{order.listings?.title || 'Unknown Item'}</h3>
                <p className="text-sm text-gray-500">Status: {order.status}</p>
                {order.listings?.type === 'decor_3d' && order.status === 'paid' && (
                  <a
                    href={`/api/downloads/${order.listing_id}`}
                    className="mt-4 inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm font-medium hover:bg-blue-200"
                  >
                    Download 3D File
                  </a>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No purchases yet.</p>
        )}
      </div>
    </div>
  );
}
