'use client';

import { useState } from 'react';
import { useUnit } from '@/contexts/UnitContext';

interface TankFitCheckerProps {
  itemDimensions: {
    length: number; // in cm
    width: number;  // in cm
    height: number; // in cm
  };
}

const PRESETS = [
  { name: 'ADA 45P', l: 45, w: 27, h: 30 },
  { name: 'ADA 60P', l: 60, w: 30, h: 36 },
  { name: 'UNS 90U', l: 90, w: 45, h: 45 },
  { name: 'Standard 10 Gal', l: 50.8, w: 25.4, h: 30.5 },
  { name: 'Standard 20 Gal Long', l: 76.2, w: 30.5, h: 30.5 },
];

export default function TankFitChecker({ itemDimensions }: TankFitCheckerProps) {
  const { unit } = useUnit();
  const [tankLength, setTankLength] = useState<string>('');
  const [tankWidth, setTankWidth] = useState<string>('');
  const [tankHeight, setTankHeight] = useState<string>('');
  const [result, setResult] = useState<'fits' | 'tight' | 'no_fit' | null>(null);

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (!val) {
      setTankLength(''); setTankWidth(''); setTankHeight('');
      return;
    }
    const preset = PRESETS[parseInt(val)];
    // Presets are in CM. We convert to display unit if needed.
    const l = unit === 'in' ? (preset.l * 0.393701).toFixed(1) : preset.l.toString();
    const w = unit === 'in' ? (preset.w * 0.393701).toFixed(1) : preset.w.toString();
    const h = unit === 'in' ? (preset.h * 0.393701).toFixed(1) : preset.h.toString();

    setTankLength(l);
    setTankWidth(w);
    setTankHeight(h);
  };

  const checkFit = () => {
    const lInput = parseFloat(tankLength);
    const wInput = parseFloat(tankWidth);
    const hInput = parseFloat(tankHeight);

    if (isNaN(lInput) || isNaN(wInput) || isNaN(hInput)) return;

    // Convert input back to CM for calculation if they are in IN
    const l = unit === 'in' ? lInput / 0.393701 : lInput;
    const w = unit === 'in' ? wInput / 0.393701 : wInput;
    const h = unit === 'in' ? hInput / 0.393701 : hInput;

    const tankXY = [l, w].sort((a, b) => a - b);
    const itemXY = [itemDimensions.length, itemDimensions.width].sort((a, b) => a - b);

    const fitsXY = itemXY[0] <= tankXY[0] && itemXY[1] <= tankXY[1];
    const fitsZ = itemDimensions.height <= h;

    if (!fitsXY || !fitsZ) {
      setResult('no_fit');
    } else {
      const clearanceX = tankXY[0] - itemXY[0];
      const clearanceY = tankXY[1] - itemXY[1];
      const clearanceZ = h - itemDimensions.height;

      if (clearanceX < 3 || clearanceY < 3 || clearanceZ < 3) {
         setResult('tight');
      } else {
         setResult('fits');
      }
    }
  };

  return (
    <div className="border border-gray-800 rounded-lg p-6 bg-zinc-900 shadow-sm mt-8 text-white">
      <h3 className="text-xl font-semibold mb-4">Tank Fit Checker</h3>
      <p className="text-sm text-gray-400 mb-4">Select a preset or enter your tank dimensions to see if this item fits.</p>

      <div className="mb-4">
        <select onChange={handlePresetChange} className="w-full bg-black border border-gray-700 p-2 rounded text-sm outline-none focus:ring-1 focus:ring-gray-500">
          <option value="">-- Choose Standard Tank Preset --</option>
          {PRESETS.map((p, i) => (
            <option key={p.name} value={i}>{p.name}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-4 mb-4">
        <input
          type="number"
          placeholder={`L (${unit})`}
          className="bg-black border border-gray-700 p-2 rounded w-full outline-none focus:ring-1 focus:ring-gray-500"
          value={tankLength}
          onChange={(e) => setTankLength(e.target.value)}
        />
        <input
          type="number"
          placeholder={`W (${unit})`}
          className="bg-black border border-gray-700 p-2 rounded w-full outline-none focus:ring-1 focus:ring-gray-500"
          value={tankWidth}
          onChange={(e) => setTankWidth(e.target.value)}
        />
        <input
          type="number"
          placeholder={`H (${unit})`}
          className="bg-black border border-gray-700 p-2 rounded w-full outline-none focus:ring-1 focus:ring-gray-500"
          value={tankHeight}
          onChange={(e) => setTankHeight(e.target.value)}
        />
      </div>

      <button
        onClick={checkFit}
        className="w-full bg-gray-100 text-black py-2 rounded font-medium hover:bg-gray-300 transition"
      >
        Check Fit
      </button>

      {result && (
        <div className={`mt-4 p-4 rounded ${result === 'fits' ? 'bg-green-900/40 text-green-400 border border-green-800' : result === 'tight' ? 'bg-yellow-900/40 text-yellow-400 border border-yellow-800' : 'bg-red-900/40 text-red-400 border border-red-800'}`}>
          <p className="font-semibold text-center mb-1">
            {result === 'fits' && '🟢 Fits Well (Margin > 3cm for easy maintenance)'}
            {result === 'tight' && '🟡 Tight Fit (Margin < 3cm)'}
            {result === 'no_fit' && '🔴 Exceeds Tank Dimensions'}
          </p>
          {result === 'no_fit' && (
            <p className="text-sm text-center opacity-90 mt-2">
              Action: Scale down the model (e.g., to 75% or 50%) in your slicer (Bambu Studio / Cura) to fit perfectly!
            </p>
          )}
        </div>
      )}
    </div>
  );
}
