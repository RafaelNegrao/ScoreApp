import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_status?: string;
}

interface TimelineContextType {
  // Estado da página Timeline
  selectedSupplier: Supplier | null;
  setSelectedSupplier: (supplier: Supplier | null) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  selectedYear: string;
  setSelectedYear: (year: string) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TimelineContext = createContext<TimelineContextType | undefined>(undefined);

export function TimelineProvider({ children }: { children: ReactNode }) {
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('2025');
  const [activeTab, setActiveTab] = useState<string>('metricas');

  return (
    <TimelineContext.Provider
      value={{
        selectedSupplier,
        setSelectedSupplier,
        searchTerm,
        setSearchTerm,
        selectedYear,
        setSelectedYear,
        activeTab,
        setActiveTab,
      }}
    >
      {children}
    </TimelineContext.Provider>
  );
}

export function useTimelineContext() {
  const context = useContext(TimelineContext);
  if (context === undefined) {
    throw new Error('useTimelineContext must be used within a TimelineProvider');
  }
  return context;
}
