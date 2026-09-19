import Link from 'next/link';

export default function CheckoutSuccessPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-4xl font-bold text-green-600 mb-4">Payment Successful!</h1>
      <p className="text-gray-600 mb-8">Thank you for your purchase. You can find your items in your account.</p>
      <Link href="/account" className="bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 transition">
        Go to My Account
      </Link>
    </div>
  );
}
