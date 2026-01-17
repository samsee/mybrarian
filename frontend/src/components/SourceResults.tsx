import type { AladinBook, SearchResponse } from '../types';
import { SourceCard } from './SourceCard';

interface SourceResultsProps {
  selectedBook: AladinBook;
  results: SearchResponse | null;
  onBack: () => void;
  loading?: boolean;
}

export const SourceResults: React.FC<SourceResultsProps> = ({
  selectedBook,
  results,
  onBack,
  loading = false
}) => {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="library-spinner mb-4" />
        <p
          className="text-[var(--color-text-secondary)] italic"
          style={{ fontFamily: 'var(--font-body)' }}
        >
          모든 소스에서 도서를 검색하는 중입니다...
        </p>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  const sortedSources = [...results.sources].sort(
    (a, b) => a.priority - b.priority
  );

  const successCount = sortedSources.filter((s) => s.success).length;
  const totalResultCount = sortedSources.reduce(
    (acc, s) => acc + (s.success ? s.result_count : 0),
    0
  );

  return (
    <div className="max-w-4xl mx-auto">
      {/* Selected book card with classic styling */}
      <div className="selected-book-card p-6 mb-8 relative">
        {/* Corner ornaments */}
        <div className="corner-ornament top-left" />
        <div className="corner-ornament top-right" />
        <div className="corner-ornament bottom-left" />
        <div className="corner-ornament bottom-right" />

        <div className="flex items-start gap-6">
          {/* Book cover */}
          {selectedBook.cover && (
            <div className="flex-shrink-0">
              <div className="relative w-28 h-40 rounded-lg overflow-hidden shadow-lg">
                {/* Book spine effect */}
                <div className="absolute inset-y-0 left-0 w-3 bg-gradient-to-r from-black/20 to-transparent z-10" />
                <img
                  src={selectedBook.cover}
                  alt={`${selectedBook.title} 표지`}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          )}

          {/* Book info */}
          <div className="flex-1 min-w-0 py-2">
            <h2
              className="text-2xl font-bold text-[var(--color-text-primary)] mb-3"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              {selectedBook.title}
            </h2>

            <div className="space-y-1 text-[var(--color-text-secondary)]">
              {selectedBook.author && (
                <p className="italic">저자: {selectedBook.author}</p>
              )}
              {selectedBook.publisher && (
                <p>출판사: {selectedBook.publisher}</p>
              )}
              {selectedBook.pubDate && (
                <p>출판일: {selectedBook.pubDate}</p>
              )}
            </div>

            {selectedBook.isbn13 && (
              <p className="text-sm text-[var(--color-text-muted)] font-mono mt-3">
                ISBN: {selectedBook.isbn13}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Results header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3
            className="text-xl font-bold text-[var(--color-text-primary)]"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            통합 검색 결과
          </h3>
          <p className="text-[var(--color-text-muted)] mt-1">
            {results.total_sources}개 소스 중 {successCount}개 검색 성공,
            총 {totalResultCount}건의 결과
          </p>
        </div>

        <button
          onClick={onBack}
          className="library-btn-secondary flex items-center gap-2"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          도서 목록으로
        </button>
      </div>

      {/* Ornamental divider */}
      <div className="ornamental-divider mb-6">
        <span className="ornamental-divider-icon">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L9.19 8.63L2 9.24L7.46 13.97L5.82 21L12 17.27L18.18 21L16.54 13.97L22 9.24L14.81 8.63L12 2Z" />
          </svg>
        </span>
      </div>

      {/* Source results */}
      <div className="space-y-6">
        {sortedSources.map((source, index) => (
          <SourceCard key={index} source={source} />
        ))}
      </div>

      {/* Bottom ornament */}
      <div className="flex justify-center mt-10 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-16 h-px bg-gradient-to-r from-transparent to-[var(--color-border-gold)]" />
          <svg
            className="w-6 h-6 text-[var(--color-accent-gold)]"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <div className="w-16 h-px bg-gradient-to-l from-transparent to-[var(--color-border-gold)]" />
        </div>
      </div>
    </div>
  );
};
