import Link from 'next/link';

export default function CheckoutCancelPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-4xl font-bold text-red-600 mb-4">Checkout Canceled</h1>
      <p className="text-gray-600 mb-8">Your payment was canceled. No charges were made.</p>
      <Link href="/catalog" className="bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 transition">
        Return to Catalog
      </Link>
    </div>
  );
}
