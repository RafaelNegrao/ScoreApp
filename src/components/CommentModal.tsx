import React, { useState, useEffect } from 'react';
import './CommentModal.css';

interface CommentModalProps {
  isOpen: boolean;
  onClose: () => void;
  month: string;
  comment: string;
  onSave: (comment: string) => void;
}

export const CommentModal: React.FC<CommentModalProps> = ({ 
  isOpen, 
  onClose, 
  month, 
  comment, 
  onSave 
}) => {
  const [localComment, setLocalComment] = useState(comment);

  useEffect(() => {
    setLocalComment(comment);
  }, [comment]);

  if (!isOpen) return null;

  const handleSave = () => {
    console.log('💾 Modal: Salvando comentário:', localComment);
    onSave(localComment);
    onClose();
  };

  const handleCancel = () => {
    console.log('❌ Modal: Cancelando edição do comentário');
    onClose();
  };

  return (
    <div className="comment-modal-overlay" onClick={handleCancel}>
      <div className="comment-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="comment-modal-header">
          <h3>Comentário - {month}</h3>
          <button className="comment-modal-close" onClick={handleCancel}>
            <i className="bi bi-x-lg"></i>
          </button>
        </div>
        <div className="comment-modal-body">
          <textarea
            className="comment-textarea"
            placeholder="Adicione um comentário..."
            value={localComment}
            onChange={(e) => setLocalComment(e.target.value)}
            rows={8}
            autoFocus
          />
        </div>
        <div className="comment-modal-footer">
          <button className="comment-modal-button cancel" onClick={handleCancel}>
            Cancelar
          </button>
          <button className="comment-modal-button save" onClick={handleSave}>
            <i className="bi bi-check-lg"></i> Salvar
          </button>
        </div>
      </div>
    </div>
  );
};
