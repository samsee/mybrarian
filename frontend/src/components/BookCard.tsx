import type { AladinBook } from '../types';

interface BookCardProps {
  book: AladinBook;
  onSelect: (book: AladinBook) => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onSelect }) => {
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="280" viewBox="0 0 200 280"%3E%3Crect fill="%23e5e7eb" width="200" height="280"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14" fill="%239ca3af"%3E표지 없음%3C/text%3E%3C/svg%3E';
  };

  return (
    <button
      onClick={() => onSelect(book)}
      className="w-full bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-xl border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 overflow-hidden text-left"
      aria-label={`${book.title} 선택`}
    >
      <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <img
          src={book.cover || ''}
          alt={`${book.title} 표지`}
          onError={handleImageError}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-sm text-gray-900 dark:text-white line-clamp-2 mb-1">
          {book.title}
        </h3>
        {book.author && (
          <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1 mb-1">
            {book.author}
          </p>
        )}
        {book.publisher && (
          <p className="text-xs text-gray-500 dark:text-gray-500 line-clamp-1">
            {book.publisher}
          </p>
        )}
      </div>
    </button>
  );
};
