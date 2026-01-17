import type { AladinBook } from '../types';

interface BookCardProps {
  book: AladinBook;
  onSelect: (book: AladinBook) => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onSelect }) => {
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="280" viewBox="0 0 200 280"%3E%3Crect fill="%23f5efe6" width="200" height="280"/%3E%3Ctext x="50%25" y="45%25" dominant-baseline="middle" text-anchor="middle" font-family="Georgia,serif" font-size="14" fill="%238b7355"%3ENo Cover%3C/text%3E%3Ctext x="50%25" y="55%25" dominant-baseline="middle" text-anchor="middle" font-family="Georgia,serif" font-size="12" fill="%23a89880"%3EAvailable%3C/text%3E%3C/svg%3E';
  };

  return (
    <button
      onClick={() => onSelect(book)}
      className="book-card w-full text-left focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-gold)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg-secondary)]"
      aria-label={`${book.title} 선택`}
    >
      {/* Book cover with realistic book styling */}
      <div className="relative aspect-[2/3] bg-[var(--color-bg-secondary)] overflow-hidden">
        {/* Book spine shadow effect */}
        <div className="absolute inset-y-0 left-0 w-3 bg-gradient-to-r from-black/20 to-transparent z-10" />

        {/* Top edge highlight */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-b from-white/30 to-transparent z-10" />

        <img
          src={book.cover || ''}
          alt={`${book.title} 표지`}
          onError={handleImageError}
          className="w-full h-full object-cover"
          loading="lazy"
        />

        {/* Bottom page effect */}
        <div className="absolute bottom-0 inset-x-0 h-2 bg-gradient-to-t from-[var(--color-bg-secondary)] to-transparent" />
      </div>

      {/* Book info */}
      <div className="p-3 border-t border-[var(--color-border)]">
        <h3
          className="font-semibold text-sm text-[var(--color-text-primary)] line-clamp-2 mb-1"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {book.title}
        </h3>
        {book.author && (
          <p className="text-xs text-[var(--color-text-secondary)] line-clamp-1 mb-1 italic">
            {book.author}
          </p>
        )}
        {book.publisher && (
          <p className="text-xs text-[var(--color-text-muted)] line-clamp-1">
            {book.publisher}
          </p>
        )}
        {book.pubDate && (
          <p className="text-xs text-[var(--color-text-muted)] mt-1 opacity-70">
            {book.pubDate.slice(0, 4)}
          </p>
        )}
      </div>

      {/* Hover indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-[var(--color-accent-gold)] transform scale-x-0 transition-transform origin-left group-hover:scale-x-100" />
    </button>
  );
};
