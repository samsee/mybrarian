import type { SourceResult } from '../types';

interface SourceCardProps {
  source: SourceResult;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  const isSuccess = source.success;

  return (
    <div
      className={`source-card ${isSuccess ? 'success' : 'error'} overflow-hidden`}
    >
      {/* Header with decorative top border */}
      <div className="relative">
        <div
          className={`absolute top-0 left-0 right-0 h-1 ${
            isSuccess
              ? 'bg-[var(--color-success)]'
              : 'bg-[var(--color-error)]'
          }`}
        />

        <div className="p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Status icon with classic styling */}
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                isSuccess
                  ? 'border-[var(--color-success)] text-[var(--color-success)]'
                  : 'border-[var(--color-error)] text-[var(--color-error)]'
              }`}
            >
              {isSuccess ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>

            <div>
              <h3
                className="text-lg font-semibold text-[var(--color-text-primary)]"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {source.source_name}
              </h3>
              <p className="text-sm text-[var(--color-text-muted)]">
                {isSuccess
                  ? `${source.result_count}건의 결과`
                  : '검색 실패'}
              </p>
            </div>
          </div>

          {/* Priority badge */}
          <span className="priority-badge">
            우선순위 {source.priority}
          </span>
        </div>
      </div>

      {/* Error message */}
      {!isSuccess && source.error_message && (
        <div className="mx-5 mb-5 p-4 rounded-lg bg-[var(--color-error-bg)] border border-[var(--color-error)]/30">
          <p className="text-sm text-[var(--color-error)] italic">
            {source.error_message}
          </p>
        </div>
      )}

      {/* No results message */}
      {isSuccess && source.result_count === 0 && (
        <div className="px-5 pb-5">
          <div className="text-center py-6 border border-dashed border-[var(--color-border)] rounded-lg">
            <svg
              className="w-8 h-8 mx-auto mb-2 text-[var(--color-text-muted)] opacity-50"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-[var(--color-text-muted)] italic">
              이 소스에서 검색 결과를 찾지 못했습니다
            </p>
          </div>
        </div>
      )}

      {/* Results list */}
      {isSuccess && source.results.length > 0 && (
        <div className="px-5 pb-5 space-y-3">
          {source.results.map((result, index) => (
            <div key={index} className="result-item">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h4
                    className="font-medium text-[var(--color-text-primary)] truncate"
                    style={{ fontFamily: 'var(--font-serif)' }}
                  >
                    {result.title || '제목 없음'}
                  </h4>
                  {result.author && (
                    <p className="text-sm text-[var(--color-text-secondary)] mt-1 italic">
                      {result.author}
                    </p>
                  )}
                  {result.availability && (
                    <p className="text-sm text-[var(--color-success)] mt-1 font-medium">
                      {result.availability}
                    </p>
                  )}
                  {result.isbn && (
                    <p className="text-xs text-[var(--color-text-muted)] font-mono mt-1">
                      ISBN: {result.isbn}
                    </p>
                  )}
                </div>

                {result.url && (
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="library-btn-secondary flex-shrink-0 text-sm"
                    aria-label="상세 보기"
                  >
                    상세 보기
                  </a>
                )}
              </div>

              {/* Additional info */}
              {result.additional_info && Object.keys(result.additional_info).length > 0 && (
                <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {Object.entries(result.additional_info).map(([key, value]) => (
                      <div key={key} className="text-[var(--color-text-muted)]">
                        <span className="font-medium">{key}:</span>{' '}
                        <span>{String(value)}</span>
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
