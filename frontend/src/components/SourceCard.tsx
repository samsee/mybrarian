import type { SourceResult } from '../types';

interface SourceCardProps {
  source: SourceResult;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  const borderColor = source.success
    ? 'border-green-500 dark:border-green-600'
    : 'border-red-500 dark:border-red-600';

  const statusIcon = source.success ? '✓' : '✗';
  const statusColor = source.success
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-600 dark:text-red-400';

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md border-2 ${borderColor} p-6`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className={`text-2xl ${statusColor}`}>
            {statusIcon}
          </span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {source.source_name}
          </h3>
        </div>
        <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium">
          우선순위 {source.priority}
        </span>
      </div>

      {!source.success && source.error_message && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">
            {source.error_message}
          </p>
        </div>
      )}

      {source.success && source.result_count === 0 && (
        <div className="text-center py-4 text-gray-500 dark:text-gray-400">
          검색 결과 없음
        </div>
      )}

      {source.success && source.results.length > 0 && (
        <div className="space-y-3">
          {source.results.map((result, index) => (
            <div
              key={index}
              className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 dark:text-white truncate">
                    {result.title || '제목 없음'}
                  </h4>
                  {result.author && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {result.author}
                    </p>
                  )}
                  {result.availability && (
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      {result.availability}
                    </p>
                  )}
                  {result.isbn && (
                    <p className="text-xs text-gray-400 dark:text-gray-600 font-mono mt-1">
                      ISBN: {result.isbn}
                    </p>
                  )}
                </div>
                {result.url && (
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                    aria-label="링크 열기"
                  >
                    보기
                  </a>
                )}
              </div>
              {result.additional_info && Object.keys(result.additional_info).length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(result.additional_info).map(([key, value]) => (
                      <div key={key} className="text-gray-600 dark:text-gray-400">
                        <span className="font-medium">{key}:</span> {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
