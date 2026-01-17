import type { AladinBook } from '../types';
import { BookCard } from './BookCard';

interface BookListProps {
  books: AladinBook[];
  onSelectBook: (book: AladinBook) => void;
  loading?: boolean;
}

export const BookList: React.FC<BookListProps> = ({
  books,
  onSelectBook,
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
          도서를 검색하는 중입니다...
        </p>
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <div className="text-center py-16">
        {/* Empty state with book icon */}
        <div className="mb-6">
          <svg
            className="w-24 h-24 mx-auto text-[var(--color-text-muted)] opacity-50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        </div>
        <h3
          className="text-xl font-semibold text-[var(--color-text-primary)] mb-2"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          검색 결과가 없습니다
        </h3>
        <p className="text-[var(--color-text-muted)] italic">
          다른 검색어로 다시 시도해 주세요
        </p>
      </div>
    );
  }

  // Group books into shelves (5 books per shelf for desktop)
  const booksPerShelf = 5;
  const shelves: AladinBook[][] = [];
  for (let i = 0; i < books.length; i += booksPerShelf) {
    shelves.push(books.slice(i, i + booksPerShelf));
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header with ornamental styling */}
      <div className="mb-8 text-center">
        <h2
          className="text-2xl font-bold text-[var(--color-text-primary)] mb-2"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          검색 결과
        </h2>
        <p className="text-[var(--color-text-secondary)]">
          {books.length}권의 도서를 찾았습니다. 원하시는 도서를 선택하세요.
        </p>

        {/* Ornamental divider */}
        <div className="ornamental-divider">
          <span className="ornamental-divider-icon">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L9.19 8.63L2 9.24L7.46 13.97L5.82 21L12 17.27L18.18 21L16.54 13.97L22 9.24L14.81 8.63L12 2Z" />
            </svg>
          </span>
        </div>
      </div>

      {/* Bookshelf display */}
      <div className="bookshelf-container">
        {shelves.map((shelfBooks, shelfIndex) => (
          <div key={shelfIndex}>
            {/* Books on this shelf */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 py-4">
              {shelfBooks.map((book, index) => (
                <BookCard
                  key={book.isbn13 || book.isbn || `${shelfIndex}-${index}`}
                  book={book}
                  onSelect={onSelectBook}
                />
              ))}
            </div>

            {/* Shelf divider (except after last shelf) */}
            {shelfIndex < shelves.length - 1 && (
              <div className="shelf-divider" />
            )}
          </div>
        ))}
      </div>

      {/* Bottom ornament */}
      <div className="flex justify-center mt-8">
        <div className="flex items-center gap-3">
          <div className="w-16 h-px bg-gradient-to-r from-transparent to-[var(--color-border-gold)]" />
          <svg
            className="w-4 h-4 text-[var(--color-accent-gold)]"
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
