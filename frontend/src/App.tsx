import { useState, useEffect } from 'react';
import type { AladinBook, SearchResponse } from './types';
import { searchBooksAladin, searchAllSources } from './services/api';
import { SearchBar } from './components/SearchBar';
import { BookList } from './components/BookList';
import { SourceResults } from './components/SourceResults';
import { ErrorMessage } from './components/ErrorMessage';

type SearchStep = 'input' | 'book-selection' | 'source-results';

function App() {
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('theme') === 'dark'
  );

  const [searchStep, setSearchStep] = useState<SearchStep>('input');
  const [aladinBooks, setAladinBooks] = useState<AladinBook[]>([]);
  const [selectedBook, setSelectedBook] = useState<AladinBook | null>(null);
  const [sourceResults, setSourceResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const handleSearch = async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await searchBooksAladin(query);
      setAladinBooks(response.books);

      // 결과가 1개면 자동 선택
      if (response.books.length === 1) {
        handleSelectBook(response.books[0]);
      } else {
        setSearchStep('book-selection');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '검색 실패');
      setSearchStep('input');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectBook = async (book: AladinBook) => {
    setSelectedBook(book);
    setLoading(true);
    setError(null);
    try {
      const isbn = book.isbn13 || book.isbn || '';
      const response = await searchAllSources(
        isbn,
        book.title,
        book.mainTitle || undefined
      );
      setSourceResults(response);
      setSearchStep('source-results');
    } catch (err) {
      setError(err instanceof Error ? err.message : '통합 검색 실패');
      setSearchStep('input');
    } finally {
      setLoading(false);
    }
  };

  const handleNewSearch = () => {
    setSearchStep('input');
    setAladinBooks([]);
    setSelectedBook(null);
    setSourceResults(null);
    setError(null);
  };

  const handleBackToBookList = () => {
    setSearchStep('book-selection');
    setSelectedBook(null);
    setSourceResults(null);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
      <header className="container mx-auto px-4 py-6 border-b border-gray-200 dark:border-gray-800">
        <div className="flex justify-between items-center">
          <button
            onClick={handleNewSearch}
            className="text-2xl font-bold hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          >
            Mybrarian
          </button>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} autoHide />}

      <main className="container mx-auto px-4 py-8">
        {searchStep === 'input' && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold mb-4">통합 도서 검색</h2>
            <SearchBar onSearch={handleSearch} loading={loading} />
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              여러 도서관과 온라인 서점을 한 번에 검색합니다.
            </p>
          </div>
        )}

        {searchStep === 'book-selection' && (
          <BookList
            books={aladinBooks}
            onSelectBook={handleSelectBook}
            loading={loading}
          />
        )}

        {searchStep === 'source-results' && selectedBook && (
          <SourceResults
            selectedBook={selectedBook}
            results={sourceResults}
            onBack={handleBackToBookList}
            loading={loading}
          />
        )}
      </main>
    </div>
  );
}

export default App;
