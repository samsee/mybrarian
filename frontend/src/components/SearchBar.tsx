import { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  loading = false,
  disabled = false
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedQuery = query.trim();
    if (trimmedQuery) {
      onSearch(trimmedQuery);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        {/* Decorative ornament above search */}
        <div className="flex justify-center mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-px bg-gradient-to-r from-transparent to-[var(--color-border-gold)]" />
            <svg
              className="w-6 h-6 text-[var(--color-accent-gold)]"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 2L9.19 8.63L2 9.24L7.46 13.97L5.82 21L12 17.27L18.18 21L16.54 13.97L22 9.24L14.81 8.63L12 2Z" />
            </svg>
            <div className="w-12 h-px bg-gradient-to-l from-transparent to-[var(--color-border-gold)]" />
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            {/* Search icon */}
            <svg
              className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="도서명 또는 ISBN을 입력하세요..."
              disabled={disabled || loading}
              className="library-input w-full pl-12 pr-4 py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="도서 검색"
            />
          </div>
          <button
            type="submit"
            disabled={disabled || loading || !query.trim()}
            className="library-btn px-8 py-4 text-lg whitespace-nowrap"
            aria-label="검색"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                검색 중...
              </span>
            ) : (
              '도서 검색'
            )}
          </button>
        </div>

        {/* Decorative ornament below search */}
        <div className="flex justify-center mt-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-px bg-[var(--color-border)]" />
            <div className="w-2 h-2 rotate-45 border border-[var(--color-border-gold)]" />
            <div className="w-8 h-px bg-[var(--color-border)]" />
          </div>
        </div>
      </div>
    </form>
  );
};
