import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_status?: string;
}

interface ScoreContextType {
  // Estado da página Score
  selectedSuppliers: Set<string>;
  setSelectedSuppliers: (suppliers: Set<string>) => void;
  selectedSuppliersData: Map<string, Supplier>;
  setSelectedSuppliersData: (data: Map<string, Supplier>) => void;
  selectedMonth: string;
  setSelectedMonth: (month: string) => void;
  selectedYear: string;
  setSelectedYear: (year: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  inputValues: Map<string, any>;
  setInputValues: (values: Map<string, any>) => void;
  yearlyView: boolean;
  setYearlyView: (view: boolean) => void;
}

const ScoreContext = createContext<ScoreContextType | undefined>(undefined);

export function ScoreProvider({ children }: { children: ReactNode }) {
  const [selectedSuppliers, setSelectedSuppliers] = useState<Set<string>>(new Set());
  const [selectedSuppliersData, setSelectedSuppliersData] = useState<Map<string, Supplier>>(new Map());
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [inputValues, setInputValues] = useState<Map<string, any>>(new Map());
  const [yearlyView, setYearlyView] = useState<boolean>(() => {
    const saved = localStorage.getItem('yearlyView');
    return saved === 'true';
  });

  return (
    <ScoreContext.Provider
      value={{
        selectedSuppliers,
        setSelectedSuppliers,
        selectedSuppliersData,
        setSelectedSuppliersData,
        selectedMonth,
        setSelectedMonth,
        selectedYear,
        setSelectedYear,
        searchQuery,
        setSearchQuery,
        inputValues,
        setInputValues,
        yearlyView,
        setYearlyView,
      }}
    >
      {children}
    </ScoreContext.Provider>
  );
}

export function useScoreContext() {
  const context = useContext(ScoreContext);
  if (context === undefined) {
    throw new Error('useScoreContext must be used within a ScoreProvider');
  }
  return context;
}
