'use client';
import { useUnit } from '@/contexts/UnitContext';

export default function UnitSwitcher() {
  const { unit, toggleUnit } = useUnit();

  return (
    <button
      onClick={toggleUnit}
      className="text-xs font-mono border border-gray-600 rounded px-3 py-1 hover:bg-gray-800 transition uppercase"
    >
      {unit === 'cm' ? 'Unit: CM' : 'Unit: IN'}
    </button>
  );
}
