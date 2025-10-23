import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  user_id: number;
  user_name: string;
  user_wwid: string;
  user_privilege: string;
}

interface Permissions {
  // Abas principais
  canAccessHome: boolean;
  canAccessScore: boolean;
  canAccessTimeline: boolean;
  canAccessRisks: boolean;
  canAccessEmail: boolean;
  canAccessLists: boolean;
  canAccessSettings: boolean;
  
  // Settings sub-abas
  canAccessSystemSettings: boolean;
  canAccessCriteria: boolean;
  canAccessSuppliers: boolean;
  canAccessUsers: boolean;
  canAccessPrivileges: boolean;
  canAccessListsSettings: boolean;
  canAccessLog: boolean;
  canAccessInfo: boolean;
  
  // Permissões especiais
  canEditAllUsers: boolean;
  canEditOnlySelf: boolean;
  canEditWWID: boolean;
  canDeleteUsers: boolean;
  canManageSuppliers: boolean;
  canEditScores: boolean;
  canDeleteScores: boolean;
  canExportData: boolean;
  canImportData: boolean;
}

interface PermissionsContextType {
  user: User | null;
  permissions: Permissions;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isUser: boolean;
}

const PermissionsContext = createContext<PermissionsContextType | undefined>(undefined);

const defaultPermissions: Permissions = {
  canAccessHome: false,
  canAccessScore: false,
  canAccessTimeline: false,
  canAccessRisks: false,
  canAccessEmail: false,
  canAccessLists: false,
  canAccessSettings: false,
  canAccessSystemSettings: false,
  canAccessCriteria: false,
  canAccessSuppliers: false,
  canAccessUsers: false,
  canAccessPrivileges: false,
  canAccessListsSettings: false,
  canAccessLog: false,
  canAccessInfo: false,
  canEditAllUsers: false,
  canEditOnlySelf: false,
  canEditWWID: false,
  canDeleteUsers: false,
  canManageSuppliers: false,
  canEditScores: false,
  canDeleteScores: false,
  canExportData: false,
  canImportData: false,
};

const getPermissionsForRole = (role: string): Permissions => {
  switch (role) {
    case 'Super Admin':
      return {
        canAccessHome: true,
        canAccessScore: true,
        canAccessTimeline: true,
        canAccessRisks: true,
        canAccessEmail: true,
        canAccessLists: true,
        canAccessSettings: true,
        canAccessSystemSettings: true,
        canAccessCriteria: true,
        canAccessSuppliers: true,
        canAccessUsers: true,
        canAccessPrivileges: true,
        canAccessListsSettings: true,
        canAccessLog: true,
        canAccessInfo: true,
        canEditAllUsers: true,
        canEditOnlySelf: true,
        canEditWWID: true,
        canDeleteUsers: true,
        canManageSuppliers: true,
        canEditScores: true,
        canDeleteScores: true,
        canExportData: true,
        canImportData: true,
      };
    
    case 'Admin':
      return {
        canAccessHome: true,
        canAccessScore: true,
        canAccessTimeline: true,
        canAccessRisks: true,
        canAccessEmail: true,
        canAccessLists: true,
        canAccessSettings: true,
        canAccessSystemSettings: true,
        canAccessCriteria: false, // Admin NÃO acessa Criteria
        canAccessSuppliers: false, // Admin NÃO acessa Suppliers
        canAccessUsers: true,
        canAccessPrivileges: false,
        canAccessListsSettings: true,
        canAccessLog: false, // Admin NÃO acessa Log
        canAccessInfo: true,
        canEditAllUsers: false,
        canEditOnlySelf: true, // Só edita ele mesmo
        canEditWWID: false, // NÃO pode editar WWID
        canDeleteUsers: false,
        canManageSuppliers: false,
        canEditScores: true,
        canDeleteScores: false,
        canExportData: true,
        canImportData: true,
      };
    
    case 'User':
      return {
        canAccessHome: true,
        canAccessScore: false, // User NÃO acessa Score
        canAccessTimeline: true, // User acessa Timeline
        canAccessRisks: false,
        canAccessEmail: false,
        canAccessLists: false,
        canAccessSettings: true,
        canAccessSystemSettings: true,
        canAccessCriteria: false,
        canAccessSuppliers: false,
        canAccessUsers: true, // Acessa Users mas só vê ele mesmo
        canAccessPrivileges: false,
        canAccessListsSettings: false,
        canAccessLog: false,
        canAccessInfo: true,
        canEditAllUsers: false,
        canEditOnlySelf: true, // Só edita ele mesmo
        canEditWWID: false, // NÃO pode editar WWID
        canDeleteUsers: false,
        canManageSuppliers: false,
        canEditScores: false,
        canDeleteScores: false,
        canExportData: false,
        canImportData: false,
      };
    
    default:
      return defaultPermissions;
  }
};

export function PermissionsProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<Permissions>(defaultPermissions);

  useEffect(() => {
    const loadUserPermissions = () => {
      const userStr = sessionStorage.getItem('user');
      console.log('🔍 Tentando carregar user do sessionStorage:', userStr);
      
      if (userStr) {
        try {
          const userData = JSON.parse(userStr);
          console.log('📦 User data parsed:', userData);
          setUser(userData);
          const userPermissions = getPermissionsForRole(userData.user_privilege || 'User');
          setPermissions(userPermissions);
          console.log('🔐 Permissions loaded for:', userData.user_privilege, userPermissions);
        } catch (e) {
          console.error('❌ Erro ao carregar permissões:', e);
        }
      } else {
        console.warn('⚠️ Nenhum user encontrado no sessionStorage');
      }
    };

    // Carrega imediatamente
    loadUserPermissions();

    // Listener para mudanças no storage
    const handleStorageChange = () => {
      console.log('🔄 Storage change detected, recarregando permissões...');
      loadUserPermissions();
    };

    // Listener customizado para login
    const handleLoginSuccess = () => {
      console.log('🎉 Login success event received, recarregando permissões...');
      loadUserPermissions();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('userLoggedIn', handleLoginSuccess);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('userLoggedIn', handleLoginSuccess);
    };
  }, []);

  const isSuperAdmin = user?.user_privilege === 'Super Admin';
  const isAdmin = user?.user_privilege === 'Admin';
  const isUser = user?.user_privilege === 'User';

  console.log('🎯 PermissionsContext state:', { user, isSuperAdmin, isAdmin, isUser, permissions });

  return (
    <PermissionsContext.Provider value={{ user, permissions, isSuperAdmin, isAdmin, isUser }}>
      {children}
    </PermissionsContext.Provider>
  );
}

export function usePermissions() {
  const context = useContext(PermissionsContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionsProvider');
  }
  return context;
}
