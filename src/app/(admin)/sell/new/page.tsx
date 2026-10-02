'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function NewListingPage() {
  const supabase = createClient();
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [type, setType] = useState('hardscape');
  const [length, setLength] = useState('');
  const [width, setWidth] = useState('');
  const [height, setHeight] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase.from('listings').insert({
      title,
      description,
      price: parseFloat(price),
      type,
      seller_id: user.id,
      dimensions_cm: {
        length: parseFloat(length),
        width: parseFloat(width),
        height: parseFloat(height)
      },
      status: 'active'
    });

    if (error) {
      console.error(error);
      alert('Error creating listing');
    } else {
      router.push('/catalog');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Create New Listing</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <input required type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border p-2 rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Type</label>
          <select value={type} onChange={(e) => setType(e.target.value)} className="w-full border p-2 rounded">
            <option value="hardscape">Hardscape</option>
            <option value="decor_3d">3D Decor</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Price ($)</label>
          <input required type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} className="w-full border p-2 rounded" />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Length (cm)</label>
            <input required type="number" value={length} onChange={(e) => setLength(e.target.value)} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Width (cm)</label>
            <input required type="number" value={width} onChange={(e) => setWidth(e.target.value)} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Height (cm)</label>
            <input required type="number" value={height} onChange={(e) => setHeight(e.target.value)} className="w-full border p-2 rounded" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea required value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border p-2 rounded h-32" />
        </div>

        <button type="submit" className="w-full bg-black text-white p-3 rounded font-semibold hover:bg-gray-800">
          Create Listing
        </button>
      </form>
    </div>
  );
}
