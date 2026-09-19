'use client';

import { useState } from 'react';

interface TankFitCheckerProps {
  itemDimensions: {
    length: number;
    width: number;
    height: number;
  };
}

export default function TankFitChecker({ itemDimensions }: TankFitCheckerProps) {
  const [tankLength, setTankLength] = useState<string>('');
  const [tankWidth, setTankWidth] = useState<string>('');
  const [tankHeight, setTankHeight] = useState<string>('');
  const [result, setResult] = useState<'fits' | 'tight' | 'no_fit' | null>(null);

  const checkFit = () => {
    const l = parseFloat(tankLength);
    const w = parseFloat(tankWidth);
    const h = parseFloat(tankHeight);

    if (isNaN(l) || isNaN(w) || isNaN(h)) return;

    // Simple check: compare sorted dimensions to handle rotation (ignoring height rotation for simplicity usually, but let's just sort X and Y)
    const tankXY = [l, w].sort((a, b) => a - b);
    const itemXY = [itemDimensions.length, itemDimensions.width].sort((a, b) => a - b);

    const fitsXY = itemXY[0] <= tankXY[0] && itemXY[1] <= tankXY[1];
    const fitsZ = itemDimensions.height <= h;

    if (!fitsXY || !fitsZ) {
      setResult('no_fit');
    } else {
      // Check for tight fit (e.g., less than 5cm clearance)
      const clearanceX = tankXY[0] - itemXY[0];
      const clearanceY = tankXY[1] - itemXY[1];
      const clearanceZ = h - itemDimensions.height;

      if (clearanceX < 5 || clearanceY < 5 || clearanceZ < 5) {
         setResult('tight');
      } else {
         setResult('fits');
      }
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm mt-8">
      <h3 className="text-xl font-semibold mb-4">Tank Fit Checker</h3>
      <p className="text-sm text-gray-500 mb-4">Enter your tank dimensions to see if this item fits.</p>

      <div className="flex gap-4 mb-4">
        <input
          type="number"
          placeholder="L (cm)"
          className="border p-2 rounded w-full"
          value={tankLength}
          onChange={(e) => setTankLength(e.target.value)}
        />
        <input
          type="number"
          placeholder="W (cm)"
          className="border p-2 rounded w-full"
          value={tankWidth}
          onChange={(e) => setTankWidth(e.target.value)}
        />
        <input
          type="number"
          placeholder="H (cm)"
          className="border p-2 rounded w-full"
          value={tankHeight}
          onChange={(e) => setTankHeight(e.target.value)}
        />
      </div>

      <button
        onClick={checkFit}
        className="w-full bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 transition"
      >
        Check Fit
      </button>

      {result && (
        <div className={`mt-4 p-4 rounded ${result === 'fits' ? 'bg-green-100 text-green-800' : result === 'tight' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
          <p className="font-semibold text-center">
            {result === 'fits' && '✓ Fits Easily'}
            {result === 'tight' && '⚠ Tight Fit'}
            {result === 'no_fit' && '✗ Doesn\'t Fit'}
          </p>
        </div>
      )}
    </div>
  );
}
