'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type UnitType = 'cm' | 'in';

interface UnitContextType {
  unit: UnitType;
  toggleUnit: () => void;
  formatDimension: (cmValue: number) => string;
}

const UnitContext = createContext<UnitContextType | undefined>(undefined);

export function UnitProvider({ children }: { children: React.ReactNode }) {
  const [unit, setUnit] = useState<UnitType>('cm');

  useEffect(() => {
    const saved = localStorage.getItem('aquafit_unit') as UnitType;
    if (saved === 'cm' || saved === 'in') {
      setTimeout(() => setUnit(saved), 0);
    }
  }, []);

  const toggleUnit = () => {
    const newUnit = unit === 'cm' ? 'in' : 'cm';
    setUnit(newUnit);
    localStorage.setItem('aquafit_unit', newUnit);
  };

  const formatDimension = (cmValue: number) => {
    if (unit === 'in') {
      return (cmValue * 0.393701).toFixed(1) + '"';
    }
    return cmValue + ' cm';
  };

  return (
    <UnitContext.Provider value={{ unit, toggleUnit, formatDimension }}>
      {children}
    </UnitContext.Provider>
  );
}

export function useUnit() {
  const context = useContext(UnitContext);
  if (context === undefined) {
    throw new Error('useUnit must be used within a UnitProvider');
  }
  return context;
}
