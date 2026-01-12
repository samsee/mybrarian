import type { AladinBook, SearchResponse } from '../types';
import { SourceCard } from './SourceCard';
import { LoadingSpinner } from './LoadingSpinner';

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
    return <LoadingSpinner size="lg" text="모든 소스를 검색하는 중..." />;
  }

  if (!results) {
    return null;
  }

  const sortedSources = [...results.sources].sort(
    (a, b) => a.priority - b.priority
  );

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {selectedBook.title}
            </h2>
            {selectedBook.author && (
              <p className="text-gray-600 dark:text-gray-400 mb-1">
                저자: {selectedBook.author}
              </p>
            )}
            {selectedBook.publisher && (
              <p className="text-gray-600 dark:text-gray-400 mb-1">
                출판사: {selectedBook.publisher}
              </p>
            )}
            {selectedBook.isbn13 && (
              <p className="text-sm text-gray-500 dark:text-gray-500 font-mono mt-2">
                ISBN: {selectedBook.isbn13}
              </p>
            )}
          </div>
          {selectedBook.cover && (
            <img
              src={selectedBook.cover}
              alt={`${selectedBook.title} 표지`}
              className="w-24 h-32 object-cover rounded-lg shadow-sm"
            />
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
          검색 결과 ({results.total_sources}개 소스)
        </h3>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors"
        >
          다시 검색
        </button>
      </div>

      <div className="space-y-4">
        {sortedSources.map((source, index) => (
          <SourceCard key={index} source={source} />
        ))}
      </div>
    </div>
  );
};
