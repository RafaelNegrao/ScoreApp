import { invoke } from '@tauri-apps/api/tauri';
import { emit } from '@tauri-apps/api/event';

/**
 * Gerenciador de status online do usuário
 * Mantém o status online atualizado e sincronizado com o backend
 */
class UserStatusManager {
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private userId: number | null = null;

  /**
   * Inicia o gerenciamento de status online
   */
  start(userId: number) {
    this.userId = userId;
    this.setOnline(true);

    // Atualiza status a cada 30 segundos (heartbeat)
    this.heartbeatInterval = setInterval(() => {
      this.heartbeat();
    }, 30000);
  }

  /**
   * Para o gerenciamento de status online
   */
  async stop() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.userId !== null) {
      await this.setOnline(false);
      console.log('🔴 UserStatusManager parado - usuário definido como offline');
    }
  }

  /**
   * Atualiza o status online do usuário
   */
  private async setOnline(isOnline: boolean) {
    if (this.userId === null) return;

    try {
      await invoke('set_user_online_status', {
        userId: this.userId,
        isOnline
      });

      // Emite evento para atualizar UI
      await emit('user-status-changed', {});
      
      console.log(`✅ Status ${isOnline ? 'online' : 'offline'} atualizado para user_id: ${this.userId}`);
    } catch (error) {
      console.error('❌ Erro ao atualizar status:', error);
    }
  }

  /**
   * Heartbeat - mantém o usuário online
   */
  private async heartbeat() {
    await this.setOnline(true);
  }
}

// Singleton
export const userStatusManager = new UserStatusManager();
