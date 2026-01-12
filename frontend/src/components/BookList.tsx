import type { AladinBook } from '../types';
import { BookCard } from './BookCard';
import { LoadingSpinner } from './LoadingSpinner';

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
    return <LoadingSpinner size="lg" text="알라딘에서 도서를 검색하는 중..." />;
  }

  if (books.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          검색 결과가 없습니다
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          다른 검색어로 다시 시도해보세요
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          도서 선택
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          {books.length}개의 검색 결과를 찾았습니다. 원하는 도서를 선택하세요.
        </p>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {books.map((book, index) => (
          <BookCard
            key={book.isbn13 || book.isbn || index}
            book={book}
            onSelect={onSelectBook}
          />
        ))}
      </div>
    </div>
  );
};
