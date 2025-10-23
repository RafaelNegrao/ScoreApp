import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import './BottomBar.css';

const BottomBar = () => {
  const [onlineCount, setOnlineCount] = useState<number>(0);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Função para buscar contagem de usuários online
  const fetchOnlineCount = async () => {
    try {
      const count = await invoke<number>('get_online_users_count');
      setOnlineCount(count);
      
      // Atualiza timestamp
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      setLastUpdate(`${hours}:${minutes}`);
    } catch (error) {
      console.error('Erro ao buscar usuários online:', error);
    }
  };

  // Busca inicial e atualização periódica
  useEffect(() => {
    // Busca imediatamente
    fetchOnlineCount();

    // Atualiza a cada 5 segundos
    const interval = setInterval(fetchOnlineCount, 5000);

    // Escuta eventos customizados de mudança de status
    const unlisten = listen('user-status-changed', () => {
      fetchOnlineCount();
    });

    return () => {
      clearInterval(interval);
      unlisten.then(fn => fn());
    };
  }, []);

  return (
    <div className="bottombar">
      <div className="bottombar-content">
        <div className="bottombar-left">
          <span className="bottombar-info">
            <i className="bi bi-clock"></i> Última atualização: {lastUpdate || '--:--'}
          </span>
        </div>
        
        <div className="bottombar-right">
          <span className="bottombar-info">
            <i className="bi bi-people-fill"></i> {onlineCount}
          </span>
        </div>
      </div>
    </div>
  );
};

export default BottomBar;
