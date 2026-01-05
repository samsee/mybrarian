import { useEffect, useState } from 'react';

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
  autoHide?: boolean;
  autoHideDuration?: number;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  onDismiss,
  autoHide = false,
  autoHideDuration = 5000
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (autoHide) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onDismiss?.();
      }, autoHideDuration);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDuration, onDismiss]);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="fixed top-4 right-4 max-w-md bg-red-50 dark:bg-red-900/20 border-2 border-red-500 dark:border-red-600 rounded-lg shadow-lg p-4 animate-in slide-in-from-top-5 z-50"
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <span className="text-red-600 dark:text-red-400 text-xl flex-shrink-0">
          ⚠
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-red-900 dark:text-red-100 mb-1">
            오류가 발생했습니다
          </h3>
          <p className="text-sm text-red-800 dark:text-red-200">
            {message}
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={() => {
              setIsVisible(false);
              onDismiss();
            }}
            className="flex-shrink-0 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 transition-colors"
            aria-label="닫기"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
