import { useState, useEffect } from "react";
import styles from "./YearlyPageTransition.module.css";
import SupplierInfoModal from "../components/SupplierInfoModal";
import { CommentModal } from "../components/CommentModal";
import ExportFormModal from "../components/ExportFormModal";
import ImportScoreModal from "../components/ImportScoreModal";
import { invoke } from '@tauri-apps/api/tauri';
import { save } from '@tauri-apps/api/dialog';
import { Info } from "lucide-react";
import './FullScoreModalAnimation.css';
import { useToastContext } from '../contexts/ToastContext';
import { useScoreContext } from '../contexts/ScoreContext';
import 'bootstrap-icons/font/bootstrap-icons.css';
import "./Score.css";

interface Supplier {
  supplier_id: string;
  vendor_name: string;
  supplier_po?: string;
  bu?: string;
  supplier_status?: string;
}

interface SupplierScore {
  record_id?: number;
  supplier_id: string;
  month: number;
  year: number;
  otif_score?: string;
  nil_score?: string;
  pickup_score?: string;
  package_score?: string;
  total_score?: string;
  comment?: string;  // Backend retorna 'comment' (singular)
  comments?: string; // Mantido para compatibilidade
}

interface UserPermissions {
  otif: string;
  nil: string;
  pickup: string;
  package: string;
}

/**
 * Componente da aba de Critérios - Apenas informativo
 */
function CriteriaTab() {
  const [isCarousel, setIsCarousel] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);

  // Detectar tamanho da tela
  useEffect(() => {
    const detectScreenSize = () => {
      if (typeof window === 'undefined') return;
      const width = window.innerWidth;
      setIsCarousel(width < 1200);
    };

    detectScreenSize();
    window.addEventListener('resize', detectScreenSize);
    return () => window.removeEventListener('resize', detectScreenSize);
  }, []);

  const handlePrevCard = () => {
    setCurrentCardIndex((prev) => (prev === 0 ? 3 : prev - 1));
  };

  const handleNextCard = () => {
    setCurrentCardIndex((prev) => (prev === 3 ? 0 : prev + 1));
  };

  const criteriaCards = [
    // OTIF
    <div className="criterio-card" key="otif">
      <div className="criterio-header">
        <i className="bi bi-clock-history"></i>
        <h3>OTIF</h3>
      </div>
      <div className="criterio-body">
        <p className="criterio-description">As notas são de 0 a 100%, porém a conversão para adição é multiplicar por 10.</p>
        <div className="criterio-example">
          <strong>Exemplo:</strong> 87% × 10 = 8,7
        </div>
        <div className="criterio-table">
          <div className="table-row header">
            <span>OTIF (%)</span>
            <span>Nota Final</span>
          </div>
          <div className="table-row nota-10">
            <span>100%</span>
            <span>10,0</span>
          </div>
          <div className="table-row nota-9">
            <span>90%</span>
            <span>9,0</span>
          </div>
          <div className="table-row nota-8">
            <span>87%</span>
            <span>8,7</span>
          </div>
          <div className="table-row nota-7">
            <span>75%</span>
            <span>7,5</span>
          </div>
          <div className="table-row nota-5">
            <span>50%</span>
            <span>5,0</span>
          </div>
          <div className="table-row nota-0">
            <span>0%</span>
            <span>0,0</span>
          </div>
        </div>
      </div>
    </div>,
    // NIL
    <div className="criterio-card" key="nil">
      <div className="criterio-header">
        <i className="bi bi-box-seam"></i>
        <h3>NIL</h3>
      </div>
      <div className="criterio-body">
        <div className="criterio-rules">
          <div className="rule-item nota-10">
            <i className="bi bi-check-circle-fill"></i>
            <span><strong>0 problemas</strong> → Nota 10</span>
          </div>
          <div className="rule-item nota-5">
            <i className="bi bi-exclamation-triangle-fill"></i>
            <span><strong>1 problema</strong> → Nota 5</span>
          </div>
          <div className="rule-item nota-0">
            <i className="bi bi-x-circle-fill"></i>
            <span><strong>Mais de 1 problema</strong> → Nota 0</span>
          </div>
        </div>
      </div>
    </div>,
    // PICKUP
    <div className="criterio-card" key="pickup">
      <div className="criterio-header">
        <i className="bi bi-truck"></i>
        <h3>Pickup</h3>
      </div>
      <div className="criterio-body">
        <div className="criterio-rules">
          <div className="rule-item nota-10">
            <i className="bi bi-check-circle-fill"></i>
            <span><strong>0 problemas</strong> → Nota 10</span>
          </div>
          <div className="rule-item nota-5">
            <i className="bi bi-exclamation-triangle-fill"></i>
            <span><strong>1 problema</strong> → Nota 5</span>
          </div>
          <div className="rule-item nota-0">
            <i className="bi bi-x-circle-fill"></i>
            <span><strong>Mais de 1 problema</strong> → Nota 0</span>
          </div>
        </div>
      </div>
    </div>,
    // PACKAGE
    <div className="criterio-card" key="package">
      <div className="criterio-header">
        <i className="bi bi-box"></i>
        <h3>Package</h3>
      </div>
      <div className="criterio-body">
        <div className="criterio-rules">
          <div className="rule-item nota-10">
            <i className="bi bi-check-circle-fill"></i>
            <span><strong>0 problemas</strong> → Nota 10</span>
          </div>
          <div className="rule-item nota-5">
            <i className="bi bi-exclamation-triangle-fill"></i>
            <span><strong>1 problema</strong> → Nota 5</span>
          </div>
          <div className="rule-item nota-0">
            <i className="bi bi-x-circle-fill"></i>
            <span><strong>Mais de 1 problema</strong> → Nota 0</span>
          </div>
        </div>
      </div>
    </div>
  ];

  return (
    <div className="criterios-content">
      {isCarousel ? (
        <>
          <div className="criterios-carousel">
            <button className="criterios-carousel-btn prev" onClick={handlePrevCard}>
              <i className="bi bi-chevron-left"></i>
            </button>
            
            <div className="criterios-carousel-track">
              {criteriaCards[currentCardIndex]}
            </div>

            <button className="criterios-carousel-btn next" onClick={handleNextCard}>
              <i className="bi bi-chevron-right"></i>
            </button>
          </div>
          
          <div className="criterios-carousel-indicators">
            {criteriaCards.map((_, index) => (
              <button
                key={index}
                className={`criterios-carousel-dot ${index === currentCardIndex ? 'active' : ''}`}
                onClick={() => setCurrentCardIndex(index)}
                aria-label={`Ir para critério ${index + 1}`}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="criterios-grid">
        {/* OTIF */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-clock-history"></i>
            <h3>OTIF</h3>
          </div>
          <div className="criterio-body">
            <p className="criterio-description">As notas são de 0 a 100%, porém a conversão para adição é multiplicar por 10.</p>
            <div className="criterio-example">
              <strong>Exemplo:</strong> 87% × 10 = 8,7
            </div>
            <div className="criterio-table">
              <div className="table-row header">
                <span>OTIF (%)</span>
                <span>Nota Final</span>
              </div>
              <div className="table-row nota-10">
                <span>100%</span>
                <span>10,0</span>
              </div>
              <div className="table-row nota-9">
                <span>90%</span>
                <span>9,0</span>
              </div>
              <div className="table-row nota-8">
                <span>87%</span>
                <span>8,7</span>
              </div>
              <div className="table-row nota-7">
                <span>75%</span>
                <span>7,5</span>
              </div>
              <div className="table-row nota-5">
                <span>50%</span>
                <span>5,0</span>
              </div>
              <div className="table-row nota-0">
                <span>0%</span>
                <span>0,0</span>
              </div>
            </div>
          </div>
        </div>

        {/* NIL */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-box-seam"></i>
            <h3>NIL</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>

        {/* PICKUP */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-truck"></i>
            <h3>Pickup</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>

        {/* PACKAGE */}
        <div className="criterio-card">
          <div className="criterio-header">
            <i className="bi bi-box"></i>
            <h3>Package</h3>
          </div>
          <div className="criterio-body">
            <div className="criterio-rules">
              <div className="rule-item nota-10">
                <i className="bi bi-check-circle-fill"></i>
                <span><strong>0 problemas</strong> → Nota 10</span>
              </div>
              <div className="rule-item nota-5">
                <i className="bi bi-exclamation-triangle-fill"></i>
                <span><strong>1 problema</strong> → Nota 5</span>
              </div>
              <div className="rule-item nota-0">
                <i className="bi bi-x-circle-fill"></i>
                <span><strong>Mais de 1 problema</strong> → Nota 0</span>
              </div>
            </div>
          </div>
        </div>
        </div>
      )}
    </div>
  );
}

/**
 * Componente de visualização anual por fornecedor
 */
interface YearlyViewTableProps {
  selectedSuppliers: Set<string>;
  selectedYear: string;
  getSupplierById: (id: string) => Supplier | undefined;
  permissions: UserPermissions;
  criteriaWeights: { otif: number; nil: number; pickup: number; package: number };
  showToast: (message: string, type?: 'success' | 'error' | 'warning' | 'info', duration?: number) => void;
  handleRemoveSupplier: (supplierId: string) => void;
}

interface YearlyMonthData {
  month: number;
  monthName: string;
  otif: number | null;
  nil: number | null;
  pickup: number | null;
  package: number | null;
  total: number | null;
  comment: string | null;
}

function YearlyViewTable({ selectedSuppliers, selectedYear, getSupplierById, permissions, criteriaWeights, showToast, handleRemoveSupplier }: YearlyViewTableProps) {
  const [yearlyData, setYearlyData] = useState<Map<string, YearlyMonthData[]>>(new Map());
  const [fadeKey, setFadeKey] = useState(0);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [selectedComment, setSelectedComment] = useState<{ supplierId: string; supplierName: string; month: number; monthName: string; comment: string } | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showSupplierInfo, setShowSupplierInfo] = useState<Supplier | null>(null);
  const [inputValues, setInputValues] = useState<Map<string, any>>(new Map());
  const [originalValues, setOriginalValues] = useState<Map<string, any>>(new Map()); // Rastreia valores originais
  const [modifiedCells, setModifiedCells] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [cardsPerPage, setCardsPerPage] = useState(2);

  const monthNames = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
  const suppliersArray = Array.from(selectedSuppliers);
  const totalSuppliers = suppliersArray.length;

  // Detecta largura da tela para ajustar cardsPerPage
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 1200) {
        setCardsPerPage(1);
      } else {
        setCardsPerPage(2);
      }
    };

    handleResize(); // Executa na montagem
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Verifica se o mês é futuro
  const isFutureMonth = (month: number): boolean => {
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth() + 1; // 0-indexed, então +1
    const selectedYearNum = parseInt(selectedYear);

    if (selectedYearNum > currentYear) return true;
    if (selectedYearNum === currentYear && month > currentMonth) return true;
    return false;
  };

  // Verifica se o usuário tem permissão para editar um campo específico
  const canEdit = (field: 'otif' | 'nil' | 'pickup' | 'package'): boolean => {
    const permission = permissions[field];
    return permission === 'Sim' || permission === 'sim' || permission === 'SIM' || permission === '1' || permission === 'true';
  };

  useEffect(() => {
    if (selectedYear && selectedSuppliers.size > 0) {
      loadYearlyData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedYear, selectedSuppliers]);

  const loadYearlyData = async () => {
    console.log('Loading yearly data for year:', selectedYear);
    const data = new Map<string, YearlyMonthData[]>();
    const newInputValues = new Map<string, any>();
    const newOriginalValues = new Map<string, any>(); // Rastreia valores originais

    for (const supplierId of Array.from(selectedSuppliers)) {
      const monthsData: YearlyMonthData[] = [];

      for (let month = 1; month <= 12; month++) {
        try {
          const scores = await invoke<any[]>('get_supplier_scores', {
            supplierIds: [supplierId],
            month,
            year: parseInt(selectedYear)
          });

          const score = scores && scores.length > 0 ? scores[0] : null;

          const rowKey = `${supplierId}-${month}`;

          // Preenche os inputValues com os dados existentes (IGUAL AO TIMELINE)
          const otif = score?.otif_score ? parseFloat(score.otif_score).toFixed(1) : '';
          const nil = score?.nil_score ? parseFloat(score.nil_score).toFixed(1) : '';
          const pickup = score?.pickup_score ? parseFloat(score.pickup_score).toFixed(1) : '';
          const pack = score?.package_score ? parseFloat(score.package_score).toFixed(1) : '';
          const comment = score?.comment || '';

          console.log(`Month ${month} - Comment from DB:`, comment, 'Full score:', score);

          newInputValues.set(`${rowKey}-otif`, otif);
          newInputValues.set(`${rowKey}-nil`, nil);
          newInputValues.set(`${rowKey}-pickup`, pickup);
          newInputValues.set(`${rowKey}-package`, pack);
          newInputValues.set(`${rowKey}-comments`, comment);

          // Salva os valores originais
          newOriginalValues.set(`${rowKey}-otif`, otif);
          newOriginalValues.set(`${rowKey}-nil`, nil);
          newOriginalValues.set(`${rowKey}-pickup`, pickup);
          newOriginalValues.set(`${rowKey}-package`, pack);
          newOriginalValues.set(`${rowKey}-comments`, comment);

          let calculatedTotal: number | null = null;

          if (otif !== '' || nil !== '' || pickup !== '' || pack !== '') {
            const scores: { value: number, weight: number }[] = [];
            
            if (otif !== '') {
              const otifNum = parseFloat(otif);
              if (!isNaN(otifNum)) scores.push({ value: otifNum, weight: criteriaWeights.otif });
            }
            if (nil !== '') {
              const nilNum = parseFloat(nil);
              if (!isNaN(nilNum)) scores.push({ value: nilNum, weight: criteriaWeights.nil });
            }
            if (pickup !== '') {
              const pickupNum = parseFloat(pickup);
              if (!isNaN(pickupNum)) scores.push({ value: pickupNum, weight: criteriaWeights.pickup });
            }
            if (pack !== '') {
              const packageNum = parseFloat(pack);
              if (!isNaN(packageNum)) scores.push({ value: packageNum, weight: criteriaWeights.package });
            }
            
            if (scores.length > 0) {
              const totalWeightedScore = scores.reduce((sum, s) => sum + (s.value * s.weight), 0);
              const totalWeight = scores.reduce((sum, s) => sum + s.weight, 0);
              calculatedTotal = (totalWeightedScore / totalWeight);
            }
          }

          monthsData.push({
            month,
            monthName: monthNames[month - 1],
            otif: otif ? parseFloat(otif) : null,
            nil: nil ? parseFloat(nil) : null,
            pickup: pickup ? parseFloat(pickup) : null,
            package: pack ? parseFloat(pack) : null,
            total: calculatedTotal,
            comment: comment || null
          });
        } catch (error) {
          const rowKey = `${supplierId}-${month}`;
          newInputValues.set(`${rowKey}-otif`, '');
          newInputValues.set(`${rowKey}-nil`, '');
          newInputValues.set(`${rowKey}-pickup`, '');
          newInputValues.set(`${rowKey}-package`, '');
          newInputValues.set(`${rowKey}-comments`, '');

          newOriginalValues.set(`${rowKey}-otif`, '');
          newOriginalValues.set(`${rowKey}-nil`, '');
          newOriginalValues.set(`${rowKey}-pickup`, '');
          newOriginalValues.set(`${rowKey}-package`, '');
          newOriginalValues.set(`${rowKey}-comments`, '');

          monthsData.push({
            month,
            monthName: monthNames[month - 1],
            otif: null,
            nil: null,
            pickup: null,
            package: null,
            total: null,
            comment: null
          });
        }
      }

      data.set(supplierId, monthsData);
    }

    setYearlyData(data);
    setInputValues(newInputValues);
    setOriginalValues(newOriginalValues); // Atualiza valores originais
  };

  const handleInputChange = (supplierId: string, month: number, field: string, value: string) => {
    const rowKey = `${supplierId}-${month}`;
    const key = `${rowKey}-${field}`;

    // Valida o valor para campos numéricos
    if (field !== 'comments') {
      const numValue = parseFloat(value);
      if (value !== '' && (isNaN(numValue) || numValue < 0 || numValue > 10)) {
        return; // Ignora valores inválidos
      }
      // Limita a 1 casa decimal
      if (value.includes('.')) {
        const parts = value.split('.');
        if (parts[1] && parts[1].length > 1) {
          value = `${parts[0]}.${parts[1].substring(0, 1)}`;
        }
      }
    }

    const newInputValues = new Map(inputValues);
    newInputValues.set(key, value);
    setInputValues(newInputValues);

    // Recalcula o total
    if (field !== 'comments') {
      updateTotal(supplierId, month, newInputValues);
    }
  };

  const handleInputBlur = async (supplierId: string, month: number, field?: string) => {
    const rowKey = `${supplierId}-${month}`;

    // Formata o número para ter 1 casa decimal se for um campo numérico
    if (field && field !== 'comments') {
      const key = `${rowKey}-${field}`;
      const value = inputValues.get(key);

      if (value && value !== '') {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          const formatted = numValue.toFixed(1);
          const newInputValues = new Map(inputValues);
          newInputValues.set(key, formatted);
          setInputValues(newInputValues);

          // Recalcula o total com o valor formatado
          updateTotal(supplierId, month, newInputValues);
        }
      }
    }

    // Verifica se houve mudanças reais comparando com valores originais
    const fields = ['otif', 'nil', 'pickup', 'package'];
    let hasChanges = false;

    for (const f of fields) {
      const key = `${rowKey}-${f}`;
      const currentValue = inputValues.get(key) || '';
      const originalValue = originalValues.get(key) || '';

      if (currentValue !== originalValue) {
        hasChanges = true;
        break;
      }
    }

    // Se nenhum campo foi alterado ou se todos estão vazios, não salva
    const allEmpty = fields.every(f => {
      const value = inputValues.get(`${rowKey}-${f}`) || '';
      return value === '';
    });

    if (!hasChanges && allEmpty) {
      console.log('🚫 Nenhuma mudança detectada ou todos os campos vazios - não salvando');
      return;
    }

    // Salva quando o campo perde o foco
    await saveScore(supplierId, month);
  };

  const updateTotal = (supplierId: string, month: number, values: Map<string, any>) => {
    const rowKey = `${supplierId}-${month}`;
    const scores: { value: number, weight: number }[] = [];
    
    const otifValue = values.get(`${rowKey}-otif`);
    if (otifValue !== null && otifValue !== undefined && otifValue !== '') {
      const otif = parseFloat(otifValue);
      if (!isNaN(otif)) scores.push({ value: otif, weight: criteriaWeights.otif });
    }
    
    const nilValue = values.get(`${rowKey}-nil`);
    if (nilValue !== null && nilValue !== undefined && nilValue !== '') {
      const nil = parseFloat(nilValue);
      if (!isNaN(nil)) scores.push({ value: nil, weight: criteriaWeights.nil });
    }
    
    const pickupValue = values.get(`${rowKey}-pickup`);
    if (pickupValue !== null && pickupValue !== undefined && pickupValue !== '') {
      const pickup = parseFloat(pickupValue);
      if (!isNaN(pickup)) scores.push({ value: pickup, weight: criteriaWeights.pickup });
    }
    
    const packageValue = values.get(`${rowKey}-package`);
    if (packageValue !== null && packageValue !== undefined && packageValue !== '') {
      const packageScore = parseFloat(packageValue);
      if (!isNaN(packageScore)) scores.push({ value: packageScore, weight: criteriaWeights.package });
    }
    
    const total = scores.length > 0 
      ? (scores.reduce((sum, s) => sum + (s.value * s.weight), 0) / scores.reduce((sum, s) => sum + s.weight, 0))
      : 0;

    // Atualiza o yearlyData
    const data = new Map(yearlyData);
    const months = data.get(supplierId);
    if (months) {
      const monthData = months.find(m => m.month === month);
      if (monthData) {
        const otifVal = otifValue !== '' ? parseFloat(otifValue) : null;
        const nilVal = nilValue !== '' ? parseFloat(nilValue) : null;
        const pickupVal = pickupValue !== '' ? parseFloat(pickupValue) : null;
        const packageVal = packageValue !== '' ? parseFloat(packageValue) : null;
        
        monthData.otif = (otifVal !== null && !isNaN(otifVal)) ? otifVal : null;
        monthData.nil = (nilVal !== null && !isNaN(nilVal)) ? nilVal : null;
        monthData.pickup = (pickupVal !== null && !isNaN(pickupVal)) ? pickupVal : null;
        monthData.package = (packageVal !== null && !isNaN(packageVal)) ? packageVal : null;
        monthData.total = total;
      }
      data.set(supplierId, [...months]);
      setYearlyData(data);
    }
  };

  const saveScore = async (supplierId: string, month: number) => {
    if (isSaving) return;

    try {
      setIsSaving(true);

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'Unknown';
      const parsedUser = storedUser ? JSON.parse(storedUser) : null;
      const userWwid = parsedUser ? String(parsedUser.user_wwid || parsedUser.user_id || 'Unknown') : 'Unknown';

      console.log('🔍 [saveScore] Objeto user completo:', parsedUser);
      console.log('🔍 [saveScore] WWID sendo enviado:', userWwid);

      const supplier = getSupplierById(supplierId);
      const supplierName = supplier?.vendor_name || '';

      const rowKey = `${supplierId}-${month}`;
      const otif = inputValues.get(`${rowKey}-otif`) || null;
      const nil = inputValues.get(`${rowKey}-nil`) || null;
      const pickup = inputValues.get(`${rowKey}-pickup`) || null;
      const packageScore = inputValues.get(`${rowKey}-package`) || null;
      const comments = inputValues.get(`${rowKey}-comments`) || null;

      // Calcula o total
      const scores: { value: number, weight: number }[] = [];
      
      if (otif !== null && otif !== '') {
        const otifNum = parseFloat(otif);
        if (!isNaN(otifNum)) scores.push({ value: otifNum, weight: criteriaWeights.otif });
      }
      if (nil !== null && nil !== '') {
        const nilNum = parseFloat(nil);
        if (!isNaN(nilNum)) scores.push({ value: nilNum, weight: criteriaWeights.nil });
      }
      if (pickup !== null && pickup !== '') {
        const pickupNum = parseFloat(pickup);
        if (!isNaN(pickupNum)) scores.push({ value: pickupNum, weight: criteriaWeights.pickup });
      }
      if (packageScore !== null && packageScore !== '') {
        const packageNum = parseFloat(packageScore);
        if (!isNaN(packageNum)) scores.push({ value: packageNum, weight: criteriaWeights.package });
      }
      
      const totalScore = scores.length > 0
        ? (scores.reduce((sum, s) => sum + (s.value * s.weight), 0) / scores.reduce((sum, s) => sum + s.weight, 0))
        : 0;

      console.log('💾 Saving score with comment:', comments);

      console.log('========================================');
      console.log('🔍 DADOS SENDO ENVIADOS PARA save_supplier_score:');
      console.log('userName:', userName);
      console.log('userWwid:', userWwid);
      console.log('========================================');

      await invoke('save_supplier_score', {
        supplierId,
        supplierName,
        month,
        year: parseInt(selectedYear),
        otifScore: otif,
        nilScore: nil,
        pickupScore: pickup,
        packageScore: packageScore,
        totalScore: totalScore.toString(),
        comments,
        userName,
        userWwid
      });

      // Remove as células modificadas desta linha
      const newModifiedCells = new Set(modifiedCells);
      ['otif', 'nil', 'pickup', 'package', 'comments'].forEach(field => {
        newModifiedCells.delete(`${supplierId}-${month}-${field}`);
      });
      setModifiedCells(newModifiedCells);

      // Atualiza os dados localmente ao invés de recarregar
      const data = new Map(yearlyData);
      const months = data.get(supplierId);
      if (months) {
        const monthData = months.find(m => m.month === month);
        if (monthData) {
          monthData.otif = otif ? parseFloat(otif) : null;
          monthData.nil = nil ? parseFloat(nil) : null;
          monthData.pickup = pickup ? parseFloat(pickup) : null;
          monthData.package = packageScore ? parseFloat(packageScore) : null;
          monthData.total = totalScore;
          monthData.comment = comments || null;
        }
        data.set(supplierId, months);
        setYearlyData(data);
      }

    } catch (error) {
      console.error('Erro ao salvar:', error);
      showToast('Erro ao salvar as notas', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCommentClick = (supplierId: string, month: number, monthName: string) => {
    const supplier = getSupplierById(supplierId);
    const rowKey = `${supplierId}-${month}`;
    const comment = inputValues.get(`${rowKey}-comments`) || '';
    const supplierName = supplier?.vendor_name || '';
    console.log('🔍 Opening comment modal - rowKey:', rowKey, 'comment:', comment, 'all inputValues:', Array.from(inputValues.entries()));
    setSelectedComment({ supplierId, supplierName, month, monthName, comment });
    setCommentModalOpen(true);
  };

  const handleCommentSave = async (comment: string) => {
    if (selectedComment) {
      console.log('💬 Saving comment:', comment, 'for supplier:', selectedComment.supplierId, 'month:', selectedComment.month);

      // Atualiza o inputValues primeiro
      const rowKey = `${selectedComment.supplierId}-${selectedComment.month}`;
      const key = `${rowKey}-comments`;
      const newInputValues = new Map(inputValues);
      newInputValues.set(key, comment);
      setInputValues(newInputValues);

      // Agora salva com o valor atualizado
      const supplierId = selectedComment.supplierId;
      const month = selectedComment.month;

      if (isSaving) return;

      try {
        setIsSaving(true);

        const storedUser = sessionStorage.getItem('user');
        const userName = storedUser ? JSON.parse(storedUser).user_name : 'Unknown';
        const parsedUser2 = storedUser ? JSON.parse(storedUser) : null;
        const userWwid2 = parsedUser2 ? String(parsedUser2.user_wwid || parsedUser2.user_id || 'Unknown') : 'Unknown';

        const supplier = getSupplierById(supplierId);
        const supplierName = supplier?.vendor_name || '';

        const otif = newInputValues.get(`${rowKey}-otif`) || null;
        const nil = newInputValues.get(`${rowKey}-nil`) || null;
        const pickup = newInputValues.get(`${rowKey}-pickup`) || null;
        const packageScore = newInputValues.get(`${rowKey}-package`) || null;

        // Calcula o total
        const scores: { value: number, weight: number }[] = [];
        
        if (otif !== null && otif !== '') {
          const otifNum = parseFloat(otif);
          if (!isNaN(otifNum)) scores.push({ value: otifNum, weight: criteriaWeights.otif });
        }
        if (nil !== null && nil !== '') {
          const nilNum = parseFloat(nil);
          if (!isNaN(nilNum)) scores.push({ value: nilNum, weight: criteriaWeights.nil });
        }
        if (pickup !== null && pickup !== '') {
          const pickupNum = parseFloat(pickup);
          if (!isNaN(pickupNum)) scores.push({ value: pickupNum, weight: criteriaWeights.pickup });
        }
        if (packageScore !== null && packageScore !== '') {
          const packageNum = parseFloat(packageScore);
          if (!isNaN(packageNum)) scores.push({ value: packageNum, weight: criteriaWeights.package });
        }
        
        const totalScore = scores.length > 0
          ? (scores.reduce((sum, s) => sum + (s.value * s.weight), 0) / scores.reduce((sum, s) => sum + s.weight, 0))
          : 0;

        console.log('💾 Saving score with comment:', comment);

        await invoke('save_supplier_score', {
          supplierId,
          supplierName,
          month,
          year: parseInt(selectedYear),
          otifScore: otif,
          nilScore: nil,
          pickupScore: pickup,
          packageScore: packageScore,
          totalScore: totalScore.toString(),
          comments: comment,
          userName,
          userWwid: userWwid2
        });

        // Atualiza os dados localmente
        const data = new Map(yearlyData);
        const months = data.get(supplierId);
        if (months) {
          const monthData = months.find(m => m.month === month);
          if (monthData) {
            monthData.comment = comment || null;
          }
          data.set(supplierId, months);
          setYearlyData(data);
        }

      } catch (error) {
        console.error('Erro ao salvar comentário:', error);
        showToast('Erro ao salvar comentário', 'error');
      } finally {
        setIsSaving(false);
      }
    }
  };

  const totalPages = Math.ceil(totalSuppliers / cardsPerPage);

  const handlePrev = () => {
    setFadeKey((k) => k + 1);
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : totalPages - 1));
  };

  const handleNext = () => {
    setFadeKey((k) => k + 1);
    setCurrentIndex((prev) => (prev < totalPages - 1 ? prev + 1 : 0));
  };

  if (totalSuppliers === 0) return null;

  const startIndex = currentIndex * cardsPerPage;
  const endIndex = Math.min(startIndex + cardsPerPage, totalSuppliers);
  const currentSuppliers = suppliersArray.slice(startIndex, endIndex);

  return (
    <>
      <div className="yearly-carousel-container">
        {/* Navegação e Contador */}
        {totalPages > 1 && (
          <div className="yearly-carousel-header">
            <button
              className="yearly-carousel-nav yearly-nav-left"
              onClick={handlePrev}
              title="Anterior"
            >
              <i className="bi bi-chevron-left"></i>
            </button>

            <div className="yearly-carousel-counter">
              <span>{currentIndex + 1} / {totalPages}</span>
            </div>

            <button
              className="yearly-carousel-nav yearly-nav-right"
              onClick={handleNext}
              title="Próximo"
            >
              <i className="bi bi-chevron-right"></i>
            </button>
          </div>
        )}

        {/* Cards dos Suppliers */}
        <div className={`yearly-cards-grid ${styles["yearly-cards-fade"]}`} key={fadeKey}>
          {currentSuppliers.map((supplierId) => {
            const supplier = getSupplierById(supplierId);
            const months = yearlyData.get(supplierId) || [];

            if (!supplier) return null;

            return (
              <div key={supplierId} className="yearly-supplier-card">
                <div className="yearly-supplier-header">
                  <div className="yearly-supplier-title-row">
                    <div>
                      <h3 className="yearly-supplier-name">{supplier.vendor_name}</h3>
                      <div className="yearly-supplier-info">
                        <span className="supplier-info-text">PO: {supplier.supplier_po || ''}</span>
                        <span className="supplier-info-text">BU: {supplier.bu || ''}</span>
                        <span
                          className={`supplier-status-indicator ${supplier.supplier_status === 'Active' ? 'status-active' : 'status-inactive'}`}
                          title={supplier.supplier_status || 'Status desconhecido'}
                        >
                          <i className="bi bi-circle-fill"></i>
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button
                        className="supplier-info-icon-btn"
                        onClick={() => setShowSupplierInfo(supplier)}
                        title="Ver informações do fornecedor"
                      >
                        <Info size={18} />
                      </button>
                      <button
                        className="supplier-info-icon-btn"
                        onClick={() => handleRemoveSupplier(supplierId)}
                        title="Remover fornecedor da lista"
                        style={{ color: 'var(--error-color)' }}
                      >
                        <i className="bi bi-dash-circle" style={{ fontSize: '18px' }}></i>
                      </button>
                    </div>
                  </div>
                </div>
                <div className="yearly-table-wrapper">
                  <table className="yearly-view-table">
                    <thead>
                      <tr>
                        <th>Mês</th>
                        <th>OTIF</th>
                        <th>NIL</th>
                        <th>Pickup</th>
                        <th>Package</th>
                        <th>Total</th>
                        <th>Comments</th>
                      </tr>
                    </thead>
                    <tbody>
                      {months.map((monthData) => {
                        const rowKey = `${supplierId}-${monthData.month}`;
                        const hasModifications = ['otif', 'nil', 'pickup', 'package', 'comments'].some(
                          field => modifiedCells.has(`${supplierId}-${monthData.month}-${field}`)
                        );

                        return (
                          <tr key={monthData.month}>
                            <td className="month-cell">{monthData.monthName}</td>
                            <td>
                              <input
                                type="number"
                                className={`yearly-score-input ${!canEdit('otif') || isFutureMonth(monthData.month) ? 'readonly' : ''}`}
                                value={inputValues.get(`${rowKey}-otif`) || ''}
                                onChange={(e) => handleInputChange(supplierId, monthData.month, 'otif', e.target.value)}
                                onFocus={() => {
                                  const key = `${rowKey}-otif`;
                                  const newOriginal = new Map(originalValues);
                                  newOriginal.set(key, inputValues.get(key) || '');
                                  setOriginalValues(newOriginal);
                                }}
                                onBlur={() => handleInputBlur(supplierId, monthData.month, 'otif')}
                                disabled={!canEdit('otif') || isFutureMonth(monthData.month)}
                                title={isFutureMonth(monthData.month) ? 'Não é possível editar meses futuros' : ''}
                                min="0"
                                max="10"
                                step="0.1"
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                className={`yearly-score-input ${!canEdit('nil') || isFutureMonth(monthData.month) ? 'readonly' : ''}`}
                                value={inputValues.get(`${rowKey}-nil`) || ''}
                                onChange={(e) => handleInputChange(supplierId, monthData.month, 'nil', e.target.value)}
                                onFocus={() => {
                                  const key = `${rowKey}-nil`;
                                  const newOriginal = new Map(originalValues);
                                  newOriginal.set(key, inputValues.get(key) || '');
                                  setOriginalValues(newOriginal);
                                }}
                                onBlur={() => handleInputBlur(supplierId, monthData.month, 'nil')}
                                disabled={!canEdit('nil') || isFutureMonth(monthData.month)}
                                title={isFutureMonth(monthData.month) ? 'Não é possível editar meses futuros' : ''}
                                min="0"
                                max="10"
                                step="0.1"
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                className={`yearly-score-input ${!canEdit('pickup') || isFutureMonth(monthData.month) ? 'readonly' : ''}`}
                                value={inputValues.get(`${rowKey}-pickup`) || ''}
                                onChange={(e) => handleInputChange(supplierId, monthData.month, 'pickup', e.target.value)}
                                onFocus={() => {
                                  const key = `${rowKey}-pickup`;
                                  const newOriginal = new Map(originalValues);
                                  newOriginal.set(key, inputValues.get(key) || '');
                                  setOriginalValues(newOriginal);
                                }}
                                onBlur={() => handleInputBlur(supplierId, monthData.month, 'pickup')}
                                disabled={!canEdit('pickup') || isFutureMonth(monthData.month)}
                                title={isFutureMonth(monthData.month) ? 'Não é possível editar meses futuros' : ''}
                                min="0"
                                max="10"
                                step="0.1"
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                className={`yearly-score-input ${!canEdit('package') || isFutureMonth(monthData.month) ? 'readonly' : ''}`}
                                value={inputValues.get(`${rowKey}-package`) || ''}
                                onChange={(e) => handleInputChange(supplierId, monthData.month, 'package', e.target.value)}
                                onFocus={() => {
                                  const key = `${rowKey}-package`;
                                  const newOriginal = new Map(originalValues);
                                  newOriginal.set(key, inputValues.get(key) || '');
                                  setOriginalValues(newOriginal);
                                }}
                                onBlur={() => handleInputBlur(supplierId, monthData.month, 'package')}
                                disabled={!canEdit('package') || isFutureMonth(monthData.month)}
                                title={isFutureMonth(monthData.month) ? 'Não é possível editar meses futuros' : ''}
                                min="0"
                                max="10"
                                step="0.1"
                              />
                            </td>
                            <td className="total-cell">{monthData.total !== null ? monthData.total.toFixed(1) : '-'}</td>
                            <td className="comment-cell">
                              <button
                                className="comment-icon-btn"
                                onClick={() => !isFutureMonth(monthData.month) && handleCommentClick(supplierId, monthData.month, monthData.monthName)}
                                disabled={isFutureMonth(monthData.month)}
                                title={
                                  isFutureMonth(monthData.month)
                                    ? 'Não é possível adicionar comentários em meses futuros'
                                    : (inputValues.get(`${rowKey}-comments`) ? 'Ver/Editar comentário' : 'Adicionar comentário')
                                }
                                style={{
                                  opacity: isFutureMonth(monthData.month) ? '0.3' : (inputValues.get(`${rowKey}-comments`) ? '1' : '0.5'),
                                  color: isFutureMonth(monthData.month) ? 'var(--text-muted)' : (inputValues.get(`${rowKey}-comments`) ? 'var(--accent-primary)' : 'var(--text-muted)'),
                                  cursor: isFutureMonth(monthData.month) ? 'not-allowed' : 'pointer'
                                }}
                              >
                                <i className="bi bi-chat-left-text-fill"></i>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {commentModalOpen && selectedComment && (
        <CommentModal
          isOpen={commentModalOpen}
          onClose={() => setCommentModalOpen(false)}
          comment={selectedComment.comment}
          supplierName={selectedComment.supplierName}
          month={selectedComment.monthName}
          year={selectedYear}
          onSave={handleCommentSave}
        />
      )}

      {showSupplierInfo && (
        <SupplierInfoModal
          isOpen={true}
          supplier={showSupplierInfo}
          onClose={() => setShowSupplierInfo(null)}
        />
      )}
    </>
  );
}

/**
 * Página de Score.
 * Exibe e gerencia pontuações e avaliações.
 */
function Score() {
  const { showToast } = useToastContext();
  const {
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
  } = useScoreContext();

  const [showSupplierInfo, setShowSupplierInfo] = useState<null | Supplier>(null);
  const [activeTab, setActiveTab] = useState<'input' | 'criterios'>('input');
  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [showSelectedModal, setShowSelectedModal] = useState<boolean>(false);
  const [scores, setScores] = useState<Map<string, SupplierScore>>(new Map());
  const [permissions, setPermissions] = useState<UserPermissions>({
    otif: 'Não',
    nil: 'Não',
    pickup: 'Não',
    package: 'Não',
  });
  const [autoSave, setAutoSave] = useState<boolean>(() => {
    const saved = localStorage.getItem('autoSave');
    return saved === null || saved === 'true'; // Default: true
  });
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [modifiedRows, setModifiedRows] = useState<Set<string>>(new Set());
  const [criteriaWeights, setCriteriaWeights] = useState({
    otif: 0.25,
    nil: 0.25,
    pickup: 0.25,
    package: 0.25,
  });
  const [showFullScoreModal, setShowFullScoreModal] = useState<boolean>(false);
  const [fullScoreMonth, setFullScoreMonth] = useState<string>('');
  const [fullScoreYear, setFullScoreYear] = useState<string>('');
  const [includeInactive, setIncludeInactive] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [generationMessage, setGenerationMessage] = useState<string>('');
  const [showOptionsMenu, setShowOptionsMenu] = useState<boolean>(false);
  const [showExportFormModal, setShowExportFormModal] = useState<boolean>(false);
  const [showImportScoreModal, setShowImportScoreModal] = useState<boolean>(false);
  const [importRefreshKey, setImportRefreshKey] = useState<number>(0);
  const [isSuperAdmin, setIsSuperAdmin] = useState<boolean>(false);
  const [allowImportExport, setAllowImportExport] = useState<boolean>(() => {
    return localStorage.getItem('allowImportExport') === 'true';
  });
  const [normalViewCommentModal, setNormalViewCommentModal] = useState(false);
  const [normalViewSelectedComment, setNormalViewSelectedComment] = useState<{ supplierId: string; supplierName: string; comment: string } | null>(null);

  // Listener para mudanças na permissão de importar/exportar
  useEffect(() => {
    const handleImportExportChange = () => {
      const newValue = localStorage.getItem('allowImportExport') === 'true';
      setAllowImportExport(newValue);
    };

    window.addEventListener('importExportChanged', handleImportExportChange);
    return () => window.removeEventListener('importExportChanged', handleImportExportChange);
  }, []);

  // Carregar critérios (pesos) do banco de dados
  useEffect(() => {
    const loadCriteria = async () => {
      try {
        const criteria = await invoke<any[]>('get_criteria');
        const weights: any = {};

        criteria.forEach((c: any) => {
          const name = c.criteria_name.toLowerCase();
          if (name.includes('otif')) weights.otif = c.criteria_weight;
          else if (name.includes('nil')) weights.nil = c.criteria_weight;
          else if (name.includes('pickup') || name.includes('pick up')) weights.pickup = c.criteria_weight;
          else if (name.includes('package')) weights.package = c.criteria_weight;
        });

        setCriteriaWeights(weights);
        console.log('✅ Critérios carregados:', weights);
      } catch (error) {
        console.error('❌ Erro ao carregar critérios:', error);
      }
    };

    loadCriteria();
  }, []);

  // Carregar permissões do usuário
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        if (user.permissions) {
          setPermissions(user.permissions);
        }
        const privilege = (user.user_privilege || '').toLowerCase();
        const isSuper = privilege === 'super admin';
        setIsSuperAdmin(isSuper);
        
        // Carregar configuração de import/export
        const importExportEnabled = localStorage.getItem('allowImportExport') === 'true';
        setAllowImportExport(importExportEnabled);
      } catch (error) {
        console.error('❌ Erro ao carregar dados do usuário:', error);
        setIsSuperAdmin(false);
        setAllowImportExport(false);
      }
    } else {
      setIsSuperAdmin(false);
      setAllowImportExport(false);
    }
  }, []);

  // Salvar preferência de auto-save
  useEffect(() => {
    localStorage.setItem('autoSave', autoSave.toString());
  }, [autoSave]);

  // Sincronizar autoSave quando alterado em Settings
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'autoSave') {
        const newValue = e.newValue === null || e.newValue === 'true';
        setAutoSave(newValue);
        console.log('🔄 Auto Save atualizado de outra aba:', newValue);
      }
    };

    const handleAutoSaveChanged = (e: CustomEvent) => {
      setAutoSave(e.detail);
      console.log('🔄 Auto Save atualizado:', e.detail);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('autoSaveChanged', handleAutoSaveChanged as EventListener);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('autoSaveChanged', handleAutoSaveChanged as EventListener);
    };
  }, []);

  // Carregar scores quando mês/ano ou suppliers mudarem
  useEffect(() => {
    const loadScores = async () => {
      if (selectedSuppliers.size > 0 && selectedMonth && selectedYear) {
        try {
          const supplierIds = Array.from(selectedSuppliers);
          const month = parseInt(selectedMonth);
          const year = parseInt(selectedYear);

          console.log('🔍 Frontend - Carregando scores para:', {
            supplierIds,
            month,
            year,
            tipos: {
              supplierIds: typeof supplierIds,
              month: typeof month,
              year: typeof year
            }
          });

          const loadedScores = await invoke<SupplierScore[]>('get_supplier_scores', {
            supplierIds,
            month,
            year,
          });

          console.log('📦 Frontend - Scores recebidos do backend:', loadedScores);
          console.log('📦 Frontend - Quantidade de scores:', loadedScores?.length);

          const scoresMap = new Map<string, SupplierScore>();
          const newInputValues = new Map<string, any>();

          loadedScores.forEach(score => {
            scoresMap.set(score.supplier_id, score);
            console.log(`📊 Score para ${score.supplier_id}:`, {
              otif: score.otif_score,
              nil: score.nil_score,
              pickup: score.pickup_score,
              package: score.package_score,
              total: score.total_score,
              comment: score.comment
            });

            // Inicializa os valores dos inputs
            newInputValues.set(`${score.supplier_id}-otif`, score.otif_score ? parseFloat(score.otif_score).toFixed(1) : '');
            newInputValues.set(`${score.supplier_id}-nil`, score.nil_score ? parseFloat(score.nil_score).toFixed(1) : '');
            newInputValues.set(`${score.supplier_id}-pickup`, score.pickup_score || '');
            newInputValues.set(`${score.supplier_id}-package`, score.package_score || '');
            newInputValues.set(`${score.supplier_id}-comments`, score.comment || '');  // Backend retorna 'comment'
            console.log(`💬 Comentário carregado para ${score.supplier_id}:`, score.comment, 'Key:', `${score.supplier_id}-comments`);
          });

          // Calcular total score inicial para cada supplier
          loadedScores.forEach(score => {
            const totalScore = calculateTotalScore(score.supplier_id, newInputValues);
            newInputValues.set(`${score.supplier_id}-total`, totalScore);
          });

          setScores(scoresMap);
          setInputValues(newInputValues);
          console.log('✅ Estados atualizados com sucesso!');
        } catch (error) {
          console.error('❌ Erro ao carregar scores:', error);
        }
      }
      // Removido: não limpar dados automaticamente quando condições não são atendidas
      // Isso permite manter o estado ao trocar de abas
    };

    loadScores();
  }, [selectedSuppliers, selectedMonth, selectedYear, importRefreshKey]);

  // Função para calcular o total score
  const calculateTotalScore = (supplierId: string, values: Map<string, any>) => {
    const scores: { value: number, weight: number }[] = [];
    
    const otifValue = values.get(`${supplierId}-otif`);
    if (otifValue !== null && otifValue !== undefined && otifValue !== '') {
      const otif = parseFloat(otifValue);
      if (!isNaN(otif)) {
        scores.push({ value: otif, weight: criteriaWeights.otif });
      }
    }
    
    const nilValue = values.get(`${supplierId}-nil`);
    if (nilValue !== null && nilValue !== undefined && nilValue !== '') {
      const nil = parseFloat(nilValue);
      if (!isNaN(nil)) {
        scores.push({ value: nil, weight: criteriaWeights.nil });
      }
    }
    
    const pickupValue = values.get(`${supplierId}-pickup`);
    if (pickupValue !== null && pickupValue !== undefined && pickupValue !== '') {
      const pickup = parseFloat(pickupValue);
      if (!isNaN(pickup)) {
        scores.push({ value: pickup, weight: criteriaWeights.pickup });
      }
    }
    
    const packageValue = values.get(`${supplierId}-package`);
    if (packageValue !== null && packageValue !== undefined && packageValue !== '') {
      const packageScore = parseFloat(packageValue);
      if (!isNaN(packageScore)) {
        scores.push({ value: packageScore, weight: criteriaWeights.package });
      }
    }
    
    if (scores.length === 0) return '0.00';
    
    const totalWeightedScore = scores.reduce((sum, s) => sum + (s.value * s.weight), 0);
    const totalWeight = scores.reduce((sum, s) => sum + s.weight, 0);
    
    return (totalWeightedScore / totalWeight).toFixed(2);
  };

  const handleSearchInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

    // Se o campo estiver vazio, esconder dropdown
    if (query.trim().length === 0) {
      setShowDropdown(false);
      setSearchResults([]);
      return;
    }

    // Busca instantânea - sem debounce
    try {
      console.log('Buscando fornecedores com query:', query.trim());
      const results = await invoke<Supplier[]>('search_suppliers', { query: query.trim() });
      console.log('Resultados encontrados:', results);
      setSearchResults(results);
      setShowDropdown(true); // Sempre mostrar dropdown quando há texto, mesmo sem resultados
    } catch (error) {
      console.error('Erro ao buscar fornecedores:', error);
      setSearchResults([]);
      setShowDropdown(true); // Mostrar dropdown com mensagem de erro
    }
  };

  const handleSelectSupplier = (supplier: Supplier) => {
    const newSelected = new Set(selectedSuppliers);
    const newData = new Map(selectedSuppliersData);

    if (newSelected.has(supplier.supplier_id)) {
      // Se já está selecionado, remove
      newSelected.delete(supplier.supplier_id);
      newData.delete(supplier.supplier_id);
    } else {
      // Se não está selecionado, adiciona
      newSelected.add(supplier.supplier_id);
      newData.set(supplier.supplier_id, supplier);
    }

    setSelectedSuppliers(newSelected);
    setSelectedSuppliersData(newData);
  };

  const handleRemoveSupplier = (supplierId: string) => {
    const newSelected = new Set(selectedSuppliers);
    newSelected.delete(supplierId);
    setSelectedSuppliers(newSelected);

    const newData = new Map(selectedSuppliersData);
    newData.delete(supplierId);
    setSelectedSuppliersData(newData);
  };

  const getSupplierById = (supplierId: string): Supplier | undefined => {
    return selectedSuppliersData.get(supplierId);
  };

  // Formata o valor para sempre ter uma casa decimal (ex: 5 -> 5.0, 7,2 -> 7.2)
  const formatScoreValue = (value: string): string => {
    if (!value || value.trim() === '') return '';

    // Remove vírgulas e substitui por ponto
    const normalized = value.replace(',', '.');
    const numValue = parseFloat(normalized);

    if (isNaN(numValue)) return '';

    // Garante que está entre 0 e 10
    const clamped = Math.max(0, Math.min(10, numValue));

    // Formata com 1 casa decimal
    return clamped.toFixed(1);
  };

  // Verifica se o usuário tem permissão para editar um campo específico
  const canEdit = (field: 'otif' | 'nil' | 'pickup' | 'package'): boolean => {
    const permission = permissions[field];
    return permission === 'Sim' || permission === 'sim' || permission === 'SIM' || permission === '1' || permission === 'true';
  };

  // Função para salvar um score individual
  const saveScore = async (supplierId: string) => {
    if (!selectedMonth || !selectedYear || isSaving) return;

    try {
      setIsSaving(true);
      const supplier = getSupplierById(supplierId);
      if (!supplier) return;

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'Unknown';
      const parsedUser3 = storedUser ? JSON.parse(storedUser) : null;
      const userWwid3 = parsedUser3 ? String(parsedUser3.user_wwid || parsedUser3.user_id || 'Unknown') : 'Unknown';

      const month = parseInt(selectedMonth);
      const year = parseInt(selectedYear);

      const otif = inputValues.get(`${supplierId}-otif`) || null;
      const nil = inputValues.get(`${supplierId}-nil`) || null;
      const pickup = inputValues.get(`${supplierId}-pickup`) || null;
      const packageScore = inputValues.get(`${supplierId}-package`) || null;
      const comments = inputValues.get(`${supplierId}-comments`) || null;
      const totalScore = calculateTotalScore(supplierId, inputValues);

      console.log('💾 Salvando score:', { supplierId, month, year, otif, nil, pickup, packageScore, totalScore, comments });
      console.log('💬 Comentário a ser salvo:', comments, 'Tipo:', typeof comments, 'Key:', `${supplierId}-comments`);

      await invoke('save_supplier_score', {
        supplierId: supplierId,
        supplierName: supplier.vendor_name,
        month,
        year,
        otifScore: otif,
        nilScore: nil,
        pickupScore: pickup,
        packageScore: packageScore,
        totalScore: totalScore,
        comments,
        userName,
        userWwid: userWwid3
      });

      console.log('✅ Score salvo com sucesso!');

      // Remover linha do set de modificadas
      setModifiedRows(prev => {
        const newSet = new Set(prev);
        newSet.delete(supplierId);
        return newSet;
      });
    } catch (error) {
      console.error('❌ Erro ao salvar score:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Funções para modal de comentário na visualização normal
  const handleNormalViewCommentClick = (supplierId: string) => {
    const supplier = getSupplierById(supplierId);
    const comment = inputValues.get(`${supplierId}-comments`) || '';
    const supplierName = supplier?.vendor_name || '';
    setNormalViewSelectedComment({ supplierId, supplierName, comment });
    setNormalViewCommentModal(true);
  };

  const handleNormalViewCommentSave = async (comment: string) => {
    if (normalViewSelectedComment) {
      const { supplierId } = normalViewSelectedComment;
      const key = `${supplierId}-comments`;
      
      console.log('💬 Salvando comentário:', { supplierId, comment, key, autoSave });
      
      const newValues = new Map(inputValues);
      newValues.set(key, comment);
      setInputValues(newValues);

      console.log('✅ Comentário setado no inputValues. Valor atual:', newValues.get(key));

      // Marcar linha como modificada
      setModifiedRows(prev => new Set(prev).add(supplierId));

      // Se auto-save estiver ativo, salvar automaticamente
      if (autoSave) {
        console.log('🔄 Auto-save ativo, salvando score...');
        await saveScore(supplierId);
      } else {
        console.log('⚠️ Auto-save desativado, usuário precisa clicar em Salvar');
      }

      setNormalViewCommentModal(false);
    }
  };

  // Função para gerar nota cheia
  const handleGenerateFullScore = async () => {
    if (!fullScoreMonth || !fullScoreYear) {
      setGenerationMessage('Mês e ano devem ser selecionados para gerar notas.');
      return;
    }

    // Validação para não gerar para meses futuros
    const now = new Date();
    const monthInt = parseInt(fullScoreMonth);
    const yearInt = parseInt(fullScoreYear);

    if ((yearInt > now.getFullYear()) || (yearInt === now.getFullYear() && monthInt > now.getMonth() + 1)) {
      setGenerationMessage('❌ Não é possível gerar notas para meses futuros.');
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationMessage('Carregando critérios...');

    try {
      // Carregar critérios
      const criteria = await invoke<any[]>('get_criteria');
      const criteriaMap: any = {};

      criteria.forEach((crit: any) => {
        const name = crit.criteria_name.toLowerCase();
        if (name.includes('package')) {
          criteriaMap.package = crit.criteria_weight;
        } else if (name.includes('pick')) {
          criteriaMap.pickup = crit.criteria_weight;
        } else if (name.includes('nil')) {
          criteriaMap.nil = crit.criteria_weight;
        } else if (name.includes('otif')) {
          criteriaMap.otif = crit.criteria_weight;
        }
      });

      if (!criteriaMap.package || !criteriaMap.pickup || !criteriaMap.nil || !criteriaMap.otif) {
        setGenerationMessage('Um ou mais critérios de pontuação estão faltando.');
        setIsGenerating(false);
        return;
      }

      setGenerationMessage('Carregando fornecedores...');

      // Carregar TODOS os fornecedores da tabela por status
      const suppliers = await invoke<Supplier[]>('get_all_suppliers_by_status', {
        includeInactive: includeInactive
      });

      if (suppliers.length === 0) {
        setGenerationMessage('Nenhum fornecedor encontrado no banco de dados.');
        setIsGenerating(false);
        return;
      }

      console.log(`Total de fornecedores carregados: ${suppliers.length}`);

      setGenerationProgress(0);
      setGenerationMessage('Gerando notas...');

      const storedUser = sessionStorage.getItem('user');
      const userName = storedUser ? JSON.parse(storedUser).user_name : 'System';
      const parsedUser4 = storedUser ? JSON.parse(storedUser) : null;
      const userWwid4 = parsedUser4 ? String(parsedUser4.user_wwid || parsedUser4.user_id || 'Unknown') : 'Unknown';

      let added = 0;
      let ignored = 0;

      const notaFixa = 10.0;
      const month = parseInt(fullScoreMonth);
      const year = parseInt(fullScoreYear);

      // Processar em lotes para não travar a interface
      const batchSize = 10;
      const totalBatches = Math.ceil(suppliers.length / batchSize);

      for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
        const startIdx = batchIndex * batchSize;
        const endIdx = Math.min(startIdx + batchSize, suppliers.length);
        const batch = suppliers.slice(startIdx, endIdx);

        // Processar batch em paralelo
        const promises = batch.map(async (supplier) => {
          // Calcular total
          const total = (
            notaFixa * criteriaMap.otif +
            notaFixa * criteriaMap.nil +
            notaFixa * criteriaMap.package +
            notaFixa * criteriaMap.pickup
          );

          try {
            const result = await invoke<string>('save_supplier_score', {
              supplierId: supplier.supplier_id,
              supplierName: supplier.vendor_name,
              month,
              year,
              otifScore: notaFixa.toString(),
              nilScore: notaFixa.toString(),
              pickupScore: notaFixa.toString(),
              packageScore: notaFixa.toString(),
              totalScore: total.toFixed(2),
              comments: '',
              userName,
              userWwid: userWwid4
            });

            // Verifica se foi ignorado ou inserido
            if (result.includes('ignorado') || result.includes('já existe')) {
              ignored++;
            } else {
              added++;
            }
          } catch (error) {
            console.error(`Erro ao salvar score para ${supplier.supplier_id}:`, error);
          }
        });

        // Aguardar batch completar
        // O erro aqui pode ser tratado individualmente em cada promise, caso dê problema , eu volto aqui
        // O erro é que não estava colocando o await, então não esperava as promessas terminarem antes de continuar
        await Promise.all(promises);

        // Atualizar progresso de 0 a 100%
        const progress = ((endIdx) / suppliers.length) * 100;
        setGenerationProgress(progress);
        setGenerationMessage(`Gerando notas... ${endIdx} de ${suppliers.length}`);

        // Pequeno delay para não travar a UI
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      setGenerationProgress(100);
      setGenerationMessage(
        `Geração de notas concluída!\n\n` +
        `Inseridos: ${added}\n` +
        `Ignorados: ${ignored}\n` +
        `Total processado: ${suppliers.length}`
      );

      // Registra log único da geração em lote
      if (added > 0) {
        try {
          await invoke('log_bulk_generation', {
            userName,
            userWwid: userWwid4,
            month,
            year,
            count: added
          });
          console.log(`Log de geração em lote registrado: ${added} fornecedores`);
        } catch (error) {
          console.error('Erro ao registrar log de geração em lote:', error);
        }
      }

    } catch (error) {
      console.error('Erro ao gerar notas cheias:', error);
      setGenerationMessage(`Erro durante a geração: ${error}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Função para exportar formulário de avaliação
  const handleExportForm = async (
    criteria: string,
    includeScore: boolean,
    month?: string,
    year?: string
  ) => {
    try {
      console.log('🔵 [Frontend] Iniciando exportação:', { criteria, includeScore, month, year });

      // Chama o backend para gerar o arquivo Excel
      console.log('🔵 [Frontend] Chamando invoke export_evaluation_form...');
      const excelBuffer = await invoke<number[]>('export_evaluation_form', {
        criteria,
        includeScore,
        month: month ? parseInt(month) : null,
        year: year ? parseInt(year) : null,
      });

      console.log('🔵 [Frontend] Buffer recebido, tamanho:', excelBuffer.length);

      // Converte o buffer para Uint8Array
      const uint8Array = new Uint8Array(excelBuffer);
      console.log('🔵 [Frontend] Uint8Array criado, tamanho:', uint8Array.length);

      // Define o nome do arquivo
      const criteriaName = criteria.toUpperCase();
      const dateStr = includeScore && month && year
        ? `_${year}_${month.padStart(2, '0')}`
        : '';
      const fileName = `Formulario_${criteriaName}${dateStr}.xlsx`;
      console.log('🔵 [Frontend] Nome do arquivo:', fileName);

      // Abre diálogo para salvar arquivo
      console.log('🔵 [Frontend] Abrindo diálogo de salvamento...');
      const filePath = await save({
        defaultPath: fileName,
        filters: [{
          name: 'Excel',
          extensions: ['xlsx']
        }]
      });

      console.log('🔵 [Frontend] Caminho selecionado:', filePath);

      if (filePath) {
        // Salva o arquivo usando FileSystem API do Tauri
        console.log('🔵 [Frontend] Salvando arquivo...');
        const { writeBinaryFile } = await import('@tauri-apps/api/fs');
        await writeBinaryFile(filePath, uint8Array);

        console.log('✅ [Frontend] Arquivo salvo com sucesso!');
        showToast(`Formulário exportado com sucesso!`, 'success');
        setShowExportFormModal(false);
      } else {
        console.log('⚠️ [Frontend] Usuário cancelou o salvamento');
      }
    } catch (error) {
      console.error('❌ [Frontend] Erro ao exportar formulário:', error);
      showToast(`Erro ao exportar formulário: ${error}`, 'error');
    }
  };

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.search-input-wrapper')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // DEBUG: Monitorar quando o modal é aberto
  useEffect(() => {
    if (showSelectedModal) {
      console.log('🔴 Modal de fornecedores selecionados foi ABERTO');
      console.trace('Stack trace de quem abriu o modal:');
    }
  }, [showSelectedModal]);

  return (
    <div className="score-page">
      {/* Tabs de navegação */}
      <div className="score-tabs">
        <button
          className={`score-tab ${activeTab === 'input' ? 'active' : ''}`}
          onClick={() => setActiveTab('input')}
        >
          <i className="bi bi-search"></i>
          <span>Pesquisa</span>
        </button>
        <button
          className={`score-tab ${activeTab === 'criterios' ? 'active' : ''}`}
          onClick={() => setActiveTab('criterios')}
        >
          <i className="bi bi-list-check"></i>
          <span>Critérios</span>
        </button>
      </div>

      {/* Conteúdo das abas */}
      <div className="score-content">
        {/* Aba Input/Pesquisa */}
        <div className="tab-panel" style={{ display: activeTab === 'input' ? 'flex' : 'none' }}>
          <>
            <div className="search-section">
              <div className="search-bar-container">
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Buscar por Nome, ID, PO ou BU..."
                    value={searchQuery}
                    onChange={handleSearchInput}
                    onFocus={() => searchQuery.trim().length > 0 && setShowDropdown(true)}
                  />

                  {selectedSuppliers.size > 0 && (
                    <button
                      type="button"
                      className="selected-badge"
                      onClick={() => setShowSelectedModal(true)}
                    >
                      <i className="bi bi-check2-circle"></i>
                      <span className="selected-count">{selectedSuppliers.size}</span>
                    </button>
                  )}

                  {showDropdown && (
                    <div className="search-dropdown show">
                      {searchResults.length > 0 ? (
                        searchResults.map((supplier) => {
                          const isSelected = selectedSuppliers.has(supplier.supplier_id);

                          return (
                            <div
                              key={supplier.supplier_id}
                              className="dropdown-item"
                              onClick={() => handleSelectSupplier(supplier)}
                            >
                              <div className="dropdown-checkbox">
                                {isSelected ? (
                                  <i className="bi bi-check-circle-fill" style={{ color: '#10b981', fontSize: 20 }}></i>
                                ) : (
                                  <i className="bi bi-circle" style={{ color: 'var(--border-color)', fontSize: 20 }}></i>
                                )}
                              </div>
                              <div className="dropdown-item-content">
                                <div className="dropdown-item-line1">
                                  <strong>{supplier.vendor_name}</strong>
                                </div>
                                <div className="dropdown-item-line2">
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">ID:</span> {supplier.supplier_id || '—'}
                                  </span>
                                  <span className="dropdown-detail-separator">•</span>
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">PO:</span> {supplier.supplier_po || '—'}
                                  </span>
                                  <span className="dropdown-detail-separator">•</span>
                                  <span className="dropdown-detail-item">
                                    <span className="dropdown-detail-label">BU:</span> {supplier.bu || '—'}
                                  </span>
                                </div>
                              </div>
                              {supplier.supplier_status && (
                                <div className={`status-indicator ${supplier.supplier_status.toLowerCase()}`}>
                                  <i className="bi bi-circle-fill"></i>
                                </div>
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <div className="dropdown-item no-results">
                          <div className="dropdown-item-main">
                            <i className="bi bi-search" style={{ marginRight: '8px', opacity: 0.5 }}></i>
                            <span style={{ color: 'var(--text-secondary)' }}>Nenhum fornecedor encontrado</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="search-filters">
                  {!yearlyView && (
                    <div className="custom-select-wrapper month-selector-transition">
                      <select
                        className="filter-select"
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        required
                      >
                        <option value="">Mês</option>
                        <option value="1">Janeiro</option>
                        <option value="2">Fevereiro</option>
                        <option value="3">Março</option>
                        <option value="4">Abril</option>
                        <option value="5">Maio</option>
                        <option value="6">Junho</option>
                        <option value="7">Julho</option>
                        <option value="8">Agosto</option>
                        <option value="9">Setembro</option>
                        <option value="10">Outubro</option>
                        <option value="11">Novembro</option>
                        <option value="12">Dezembro</option>
                      </select>
                      <i className="bi bi-chevron-down select-icon"></i>
                    </div>
                  )}
                  <div className="custom-select-wrapper">
                    <select
                      className="filter-select"
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(e.target.value)}
                      required
                    >
                      <option value="">Ano</option>
                      {Array.from({ length: 6 }, (_, i) => new Date().getFullYear() + i).map((year) => (
                        <option key={year} value={year.toString()}>{year}</option>
                      ))}
                    </select>
                    <i className="bi bi-chevron-down select-icon"></i>
                  </div>

                  {/* Botão para menu de opções */}
                  <div className="options-menu-wrapper">
                    <button
                      className="more-options-btn"
                      onClick={() => setShowOptionsMenu(!showOptionsMenu)}
                      title="Mais opções"
                    >
                      <i className="bi bi-gear"></i>
                    </button>

                    {showOptionsMenu && (
                      <>
                        <div
                          className="options-menu-overlay"
                          onClick={() => setShowOptionsMenu(false)}
                        />
                        <div className="options-menu-dropdown">
                          <button
                            className="options-menu-item"
                            onClick={() => {
                              setShowFullScoreModal(true);
                              setShowOptionsMenu(false);
                            }}
                          >
                            <i className="bi bi-stars"></i>
                            <span>Gerar nota cheia</span>
                          </button>

                          {allowImportExport && (
                            <>
                              <div className="options-menu-divider"></div>

                              <button
                                className="options-menu-item"
                                onClick={() => {
                                  setShowExportFormModal(true);
                                  setShowOptionsMenu(false);
                                }}
                              >
                                <i className="bi bi-file-earmark-arrow-down"></i>
                                <span>Exportar formulário</span>
                              </button>

                              <button
                                className="options-menu-item"
                                onClick={() => {
                                  setShowImportScoreModal(true);
                                  setShowOptionsMenu(false);
                                }}
                              >
                                <i className="bi bi-file-earmark-arrow-up"></i>
                                <span>Importar Score</span>
                              </button>

                              <div className="options-menu-divider"></div>
                            </>
                          )}

                          <div className="options-menu-item switch-item">
                            <div className="switch-label">
                              <i className="bi bi-calendar3"></i>
                              <span>Visualização por ano</span>
                            </div>
                            <label className="switch">
                              <input
                                type="checkbox"
                                checked={yearlyView}
                                onChange={(e) => {
                                  const newValue = e.target.checked;
                                  setYearlyView(newValue);
                                  localStorage.setItem('yearlyView', newValue.toString());
                                }}
                              />
                              <span className="slider"></span>
                            </label>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {selectedSuppliers.size === 0 && searchQuery.trim().length === 0 ? (
                <div className="empty-state">
                  <i className="bi bi-search"></i>
                  <p>Pesquise por fornecedores</p>
                  <small>Use os filtros acima para buscar</small>
                </div>
              ) : null}

              {/* Tabela de fornecedores selecionados */}
              {selectedSuppliers.size > 0 && (
                <div className="suppliers-table-section">
                  {!yearlyView ? (
                    <div className="info-message">
                      <i className="bi bi-info-circle"></i>
                      <p>Selecione o mês e o ano para carregar as notas salvas</p>
                    </div>
                  ) : null}

                  {yearlyView && !selectedYear ? (
                    <div className="info-message">
                      <i className="bi bi-info-circle"></i>
                      <p>Selecione o ano para visualizar os dados anuais</p>
                    </div>
                  ) : null}

                  {yearlyView && selectedYear ? (
                    <div className="view-transition">
                      <YearlyViewTable
                        selectedSuppliers={selectedSuppliers}
                        selectedYear={selectedYear}
                        getSupplierById={getSupplierById}
                        permissions={permissions}
                        criteriaWeights={criteriaWeights}
                        showToast={showToast}
                        handleRemoveSupplier={handleRemoveSupplier}
                      />
                    </div>
                  ) : !yearlyView ? (
                    <div className="view-transition">
                      <div className="table-container">
                        <table className="suppliers-table">
                          <thead>
                            <tr>
                              <th>ID</th>
                              <th>Supplier ID</th>
                              <th>PO</th>
                              <th>BU</th>
                              <th>Supplier Name</th>
                              <th>OTIF</th>
                              <th>NIL</th>
                              <th>Pickup</th>
                              <th>Package</th>
                              <th>Total</th>
                              <th>Comments</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Array.from(selectedSuppliers).map((supplierId, index) => {
                              const supplier = getSupplierById(supplierId);
                              if (!supplier) return null;

                              const score = scores.get(supplierId);
                              const commentValue = inputValues.get(`${supplierId}-comments`);
                              console.log(`🎨 Renderizando ícone para ${supplierId}:`, 'commentValue:', commentValue, 'hasContent:', !!(commentValue || '').trim());

                              return (
                                <tr key={`${supplierId}-${selectedMonth}-${selectedYear}`}>
                                  <td>{index + 1}</td>
                                  <td>{supplier.supplier_id}</td>
                                  <td>{supplier.supplier_po || '—'}</td>
                                  <td>{supplier.bu || '—'}</td>
                                  <td className="supplier-name-cell">{supplier.vendor_name}</td>
                                  <td>
                                    <input
                                      type="number"
                                      className={`score-input ${!canEdit('otif') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                      min="0"
                                      max="10"
                                      step="0.1"

                                      value={inputValues.get(`${supplierId}-otif`) || ''}
                                      readOnly={!canEdit('otif') || !selectedMonth || !selectedYear}
                                      disabled={!canEdit('otif') || !selectedMonth || !selectedYear}
                                      onChange={(e) => {
                                        if (!canEdit('otif') || !selectedMonth || !selectedYear) return;
                                        let value = e.target.value;
                                        const numValue = parseFloat(value);
                                        if (numValue > 10) value = '10.0';
                                        if (numValue < 0) value = '0.0';
                                        const newValues = new Map(inputValues);
                                        newValues.set(`${supplierId}-otif`, value);

                                        // Calcular e atualizar o total score em tempo real
                                        const totalScore = calculateTotalScore(supplierId, newValues);
                                        newValues.set(`${supplierId}-total`, totalScore);

                                        // Marcar linha como modificada
                                        setModifiedRows(prev => new Set(prev).add(supplierId));

                                        setInputValues(newValues);
                                      }}
                                      onBlur={(e) => {
                                        if (!canEdit('otif') || !selectedMonth || !selectedYear) return;
                                        const formatted = formatScoreValue(e.target.value);
                                        if (formatted !== '') {
                                          const newValues = new Map(inputValues);
                                          newValues.set(`${supplierId}-otif`, formatted);
                                          setInputValues(newValues);
                                        }
                                        if (autoSave) {
                                          saveScore(supplierId);
                                        }
                                      }}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      type="number"
                                      className={`score-input ${!canEdit('nil') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                      min="0"
                                      max="10"
                                      step="0.1"

                                      value={inputValues.get(`${supplierId}-nil`) || ''}
                                      readOnly={!canEdit('nil') || !selectedMonth || !selectedYear}
                                      disabled={!canEdit('nil') || !selectedMonth || !selectedYear}
                                      onChange={(e) => {
                                        if (!canEdit('nil') || !selectedMonth || !selectedYear) return;
                                        let value = e.target.value;
                                        const numValue = parseFloat(value);
                                        if (numValue > 10) value = '10.0';
                                        if (numValue < 0) value = '0.0';
                                        const newValues = new Map(inputValues);
                                        newValues.set(`${supplierId}-nil`, value);

                                        // Calcular e atualizar o total score em tempo real
                                        const totalScore = calculateTotalScore(supplierId, newValues);
                                        newValues.set(`${supplierId}-total`, totalScore);

                                        // Marcar linha como modificada
                                        setModifiedRows(prev => new Set(prev).add(supplierId));

                                        setInputValues(newValues);
                                      }}
                                      onBlur={(e) => {
                                        if (!canEdit('nil') || !selectedMonth || !selectedYear) return;
                                        const formatted = formatScoreValue(e.target.value);
                                        if (formatted !== '') {
                                          const newValues = new Map(inputValues);
                                          newValues.set(`${supplierId}-nil`, formatted);
                                          setInputValues(newValues);
                                        }
                                        if (autoSave) {
                                          saveScore(supplierId);
                                        }
                                      }}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      type="number"
                                      className={`score-input ${!canEdit('pickup') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                      min="0"
                                      max="10"
                                      step="0.1"

                                      value={inputValues.get(`${supplierId}-pickup`) || ''}
                                      readOnly={!canEdit('pickup') || !selectedMonth || !selectedYear}
                                      disabled={!canEdit('pickup') || !selectedMonth || !selectedYear}
                                      onChange={(e) => {
                                        if (!canEdit('pickup') || !selectedMonth || !selectedYear) return;
                                        let value = e.target.value;
                                        const numValue = parseFloat(value);
                                        if (numValue > 10) value = '10';
                                        if (numValue < 0) value = '0';
                                        const newValues = new Map(inputValues);
                                        newValues.set(`${supplierId}-pickup`, value);

                                        // Calcular e atualizar o total score em tempo real
                                        const totalScore = calculateTotalScore(supplierId, newValues);
                                        newValues.set(`${supplierId}-total`, totalScore);

                                        // Marcar linha como modificada
                                        setModifiedRows(prev => new Set(prev).add(supplierId));

                                        setInputValues(newValues);
                                      }}
                                      onBlur={(e) => {
                                        if (!canEdit('pickup') || !selectedMonth || !selectedYear) return;
                                        const formatted = formatScoreValue(e.target.value);
                                        if (formatted !== '') {
                                          const newValues = new Map(inputValues);
                                          newValues.set(`${supplierId}-pickup`, formatted);
                                          setInputValues(newValues);
                                        }
                                        if (autoSave) {
                                          saveScore(supplierId);
                                        }
                                      }}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      type="number"
                                      className={`score-input ${!canEdit('package') || !selectedMonth || !selectedYear ? 'readonly' : ''}`}
                                      min="0"
                                      max="10"
                                      step="0.1"

                                      value={inputValues.get(`${supplierId}-package`) || ''}
                                      readOnly={!canEdit('package') || !selectedMonth || !selectedYear}
                                      disabled={!canEdit('package') || !selectedMonth || !selectedYear}
                                      onChange={(e) => {
                                        if (!canEdit('package') || !selectedMonth || !selectedYear) return;
                                        let value = e.target.value;
                                        const numValue = parseFloat(value);
                                        if (numValue > 10) value = '10';
                                        if (numValue < 0) value = '0';
                                        const newValues = new Map(inputValues);
                                        newValues.set(`${supplierId}-package`, value);

                                        // Calcular e atualizar o total score em tempo real
                                        const totalScore = calculateTotalScore(supplierId, newValues);
                                        newValues.set(`${supplierId}-total`, totalScore);

                                        // Marcar linha como modificada
                                        setModifiedRows(prev => new Set(prev).add(supplierId));

                                        setInputValues(newValues);
                                      }}
                                      onBlur={(e) => {
                                        if (!canEdit('package') || !selectedMonth || !selectedYear) return;
                                        const formatted = formatScoreValue(e.target.value);
                                        if (formatted !== '') {
                                          const newValues = new Map(inputValues);
                                          newValues.set(`${supplierId}-package`, formatted);
                                          setInputValues(newValues);
                                        }
                                        if (autoSave) {
                                          saveScore(supplierId);
                                        }
                                      }}
                                    />
                                  </td>
                                  <td className="total-cell">
                                    <span className="total-score">
                                      {parseFloat(inputValues.get(`${supplierId}-total`) || calculateTotalScore(supplierId, inputValues)).toFixed(1)}
                                    </span>
                                  </td>
                                  <td className="comment-cell">
                                    <button
                                      className="comment-icon-btn"
                                      onClick={() => selectedMonth && selectedYear && handleNormalViewCommentClick(supplierId)}
                                      disabled={!selectedMonth || !selectedYear}
                                      title={
                                        !selectedMonth || !selectedYear
                                          ? 'Selecione mês e ano para adicionar comentário'
                                          : ((inputValues.get(`${supplierId}-comments`) || '').trim() ? 'Ver/Editar comentário' : 'Adicionar comentário')
                                      }
                                      style={{
                                        opacity: !selectedMonth || !selectedYear ? '0.3' : ((inputValues.get(`${supplierId}-comments`) || '').trim() ? '1' : '0.5'),
                                        color: !selectedMonth || !selectedYear ? 'var(--text-muted)' : ((inputValues.get(`${supplierId}-comments`) || '').trim() ? 'var(--accent-primary)' : 'var(--text-muted)'),
                                        cursor: !selectedMonth || !selectedYear ? 'not-allowed' : 'pointer'
                                      }}
                                    >
                                      <i className="bi bi-chat-left-text-fill"></i>
                                    </button>
                                  </td>
                                  <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      {/* Ícone de info */}
                                      <button
                                        className="action-btn info-btn"
                                        style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
                                        title="Informações do fornecedor"
                                        onClick={e => { e.stopPropagation(); setShowSupplierInfo(supplier); }}
                                      >
                                        <Info size={16} color="var(--accent-primary)" />
                                      </button>
                                      {/* Ícone de modificado */}
                                      {modifiedRows.has(supplierId) && (
                                        <i
                                          className="bi bi-pencil-fill"
                                          style={{ color: '#f39c12', fontSize: '16px' }}
                                          title="Modificado - não salvo"
                                        ></i>
                                      )}
                                      {/* Botão Salvar - apenas quando auto-save está desativado */}
                                      {!autoSave && (
                                        <button
                                          className="action-btn save-btn"
                                          onClick={() => saveScore(supplierId)}
                                          disabled={isSaving || !selectedMonth || !selectedYear}
                                          title={!selectedMonth || !selectedYear ? "Selecione mês e ano" : "Salvar"}
                                        >
                                          <i className="bi bi-save"></i>
                                        </button>
                                      )}
                                      {/* Botão Remover */}
                                      <button
                                        className="action-btn remove-btn"
                                        style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'var(--error-color)' }}
                                        title="Remover fornecedor da lista"
                                        onClick={() => handleRemoveSupplier(supplierId)}
                                      >
                                        <i className="bi bi-dash-circle" style={{ fontSize: '16px' }}></i>
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>

            {/* Modal de fornecedores selecionados */}
            {showSelectedModal && (
              <div className="selected-modal-overlay" onClick={() => setShowSelectedModal(false)}>
                <div className="selected-modal" onClick={(e) => e.stopPropagation()}>
                  <div className="selected-modal-header">
                    <h3>Fornecedores Selecionados ({selectedSuppliers.size})</h3>
                    <button className="modal-close" onClick={() => setShowSelectedModal(false)}>
                      <i className="bi bi-x-lg"></i>
                    </button>
                  </div>
                  <div className="selected-modal-content">
                    {selectedSuppliers.size > 0 ? (
                      Array.from(selectedSuppliers).map((supplierId) => {
                        const supplier = getSupplierById(supplierId);
                        return supplier ? (
                          <div key={supplierId} className="supplier-card-modal">
                            <div className="supplier-card-header">
                              <h4>{supplier.vendor_name}</h4>
                              {supplier.supplier_status && (
                                <span className={`status-badge ${supplier.supplier_status.toLowerCase()}`}>
                                  {supplier.supplier_status}
                                </span>
                              )}
                            </div>
                            <div className="supplier-card-details">
                              <div className="detail-item">
                                <i className="bi bi-hash"></i>
                                <span className="detail-label">ID:</span>
                                <span className="detail-value">{supplier.supplier_id || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <i className="bi bi-file-text"></i>
                                <span className="detail-label">PO:</span>
                                <span className="detail-value">{supplier.supplier_po || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <i className="bi bi-building"></i>
                                <span className="detail-label">BU:</span>
                                <span className="detail-value">{supplier.bu || '—'}</span>
                              </div>
                            </div>
                          </div>
                        ) : null;
                      })
                    ) : (
                      <div className="empty-state-modal">
                        <i className="bi bi-inbox" style={{ fontSize: '48px', color: 'var(--text-secondary)', marginBottom: '16px' }}></i>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>Nenhum fornecedor selecionado</p>
                        <small style={{ color: 'var(--text-tertiary)', fontSize: '14px' }}>Use a busca acima para adicionar fornecedores</small>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        </div>

        {/* Aba Critérios */}
        <div className="tab-panel" style={{ display: activeTab === 'criterios' ? 'flex' : 'none' }}>
          <CriteriaTab />
        </div>
      </div>

      {/* Modal de informações do fornecedor */}
      {showSupplierInfo && (
        <SupplierInfoModal
          isOpen={true}
          supplier={showSupplierInfo}
          onClose={() => setShowSupplierInfo(null)}
        />
      )}

      {/* Modal Gerar Nota Cheia */}
      {showFullScoreModal && (
        <>
          <div className="modal-overlay" onClick={() => !isGenerating && setShowFullScoreModal(false)} />
          <div className="full-score-modal">
            <div className="full-score-header">
              <h2>Gerar Nota Cheia</h2>
              <button
                className="close-modal-btn"
                onClick={() => !isGenerating && setShowFullScoreModal(false)}
                disabled={isGenerating}
              >
                <i className="bi bi-x"></i>
              </button>
            </div>

            <div className="full-score-content">
              <p className="full-score-description">
                Selecione o mês e ano para gerar notas máximas para todos os fornecedores ativos:
              </p>

              <div className="full-score-selects">
                <div className="full-score-select-wrapper">
                  <label>Mês</label>
                  <select
                    value={fullScoreMonth}
                    onChange={(e) => setFullScoreMonth(e.target.value)}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">Selecione</option>
                    <option value="1">Janeiro</option>
                    <option value="2">Fevereiro</option>
                    <option value="3">Março</option>
                    <option value="4">Abril</option>
                    <option value="5">Maio</option>
                    <option value="6">Junho</option>
                    <option value="7">Julho</option>
                    <option value="8">Agosto</option>
                    <option value="9">Setembro</option>
                    <option value="10">Outubro</option>
                    <option value="11">Novembro</option>
                    <option value="12">Dezembro</option>
                  </select>
                </div>

                <div className="full-score-select-wrapper">
                  <label>Ano</label>
                  <select
                    value={fullScoreYear}
                    onChange={(e) => setFullScoreYear(e.target.value)}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">Selecione</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                    <option value="2027">2027</option>
                    <option value="2028">2028</option>
                    <option value="2029">2029</option>
                    <option value="2030">2030</option>
                  </select>
                </div>
              </div>

              <div className="full-score-switch">
                <label className="switch-container">
                  <input
                    type="checkbox"
                    checked={includeInactive}
                    onChange={(e) => setIncludeInactive(e.target.checked)}
                    disabled={isGenerating}
                  />
                  <span className="switch-slider"></span>
                </label>
                <span className="switch-label">Gerar score também para Inactives</span>
              </div>

              {generationMessage && (
                <div className="generation-status">
                  <div className={`generation-message-container ${!isGenerating ? 'complete' : ''}`}>
                    {!isGenerating ? (
                      <i className="bi bi-check-circle-fill" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    ) : generationProgress === 0 ? (
                      <i className="bi bi-arrow-repeat spinning-icon" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    ) : (
                      <i className="bi bi-hourglass-split" style={{ color: 'var(--accent-primary)', fontSize: '20px' }}></i>
                    )}
                    <p className="generation-message">{generationMessage}</p>
                  </div>
                  {isGenerating && generationProgress > 0 && (
                    <div className="progress-bar-container">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${generationProgress}%` }}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="full-score-footer">
              <button
                className="btn-cancel"
                onClick={() => setShowFullScoreModal(false)}
                disabled={isGenerating}
              >
                {isGenerating ? 'Cancelar' : 'Fechar'}
              </button>
              <button
                className="btn-generate"
                onClick={handleGenerateFullScore}
                disabled={isGenerating || !fullScoreMonth || !fullScoreYear}
              >
                Gerar
              </button>
            </div>
          </div>
        </>
      )}

      {/* Modal Exportar Formulário */}
      <ExportFormModal
        isOpen={showExportFormModal}
        onClose={() => setShowExportFormModal(false)}
        onExport={handleExportForm}
      />

      {/* Modal Importar Score */}
      <ImportScoreModal
        isOpen={showImportScoreModal}
        onClose={() => setShowImportScoreModal(false)}
        onImportSuccess={() => {
          setImportRefreshKey((prev) => prev + 1);
        }}
      />

      {/* Modal de comentário para visualização normal */}
      {normalViewCommentModal && normalViewSelectedComment && (
        <CommentModal
          isOpen={normalViewCommentModal}
          onClose={() => setNormalViewCommentModal(false)}
          comment={normalViewSelectedComment.comment}
          supplierName={normalViewSelectedComment.supplierName}
          month={selectedMonth ? ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][parseInt(selectedMonth)] : ''}
          year={selectedYear}
          onSave={handleNormalViewCommentSave}
        />
      )}
    </div>
  );
}

export default Score;
