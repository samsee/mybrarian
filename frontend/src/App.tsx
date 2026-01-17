import { useState, useEffect } from 'react';
import type { AladinBook, SearchResponse } from './types';
import { searchBooksAladin, searchAllSources } from './services/api';
import { SearchBar } from './components/SearchBar';
import { BookList } from './components/BookList';
import { SourceResults } from './components/SourceResults';
import './styles.css';

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

      if (response.books.length === 1) {
        handleSelectBook(response.books[0]);
      } else {
        setSearchStep('book-selection');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '검색에 실패했습니다');
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
      setError(err instanceof Error ? err.message : '통합 검색에 실패했습니다');
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
    <div className="design-b min-h-screen transition-colors duration-300">
      {/* Classic library header */}
      <header className="library-header">
        <div className="container mx-auto px-4 py-5">
          <div className="flex justify-between items-center">
            {/* Logo with classic typography */}
            <button
              onClick={handleNewSearch}
              className="group flex items-center gap-3 transition-all"
            >
              {/* Book icon */}
              <svg
                className="w-8 h-8 text-[var(--color-accent-gold-light)] group-hover:text-white transition-colors"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span
                className="text-2xl font-bold text-white group-hover:text-[var(--color-accent-gold-light)] transition-colors tracking-wide"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                MyBrarian
              </span>
            </button>

            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="theme-toggle"
              aria-label={darkMode ? '라이트 모드로 전환' : '다크 모드로 전환'}
            >
              {darkMode ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Error toast with classic styling */}
      {error && (
        <div className="fixed top-20 right-4 z-50 max-w-md animate-in slide-in-from-right">
          <div className="bg-[var(--color-error-bg)] border-2 border-[var(--color-error)] rounded-lg p-4 shadow-lg">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-[var(--color-error)] flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <p className="text-[var(--color-error)] font-medium">오류 발생</p>
                <p className="text-sm text-[var(--color-error)] mt-1">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-[var(--color-error)] hover:opacity-70 transition-opacity"
                aria-label="닫기"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="container mx-auto px-4 py-10">
        {/* Input step - Search page */}
        {searchStep === 'input' && (
          <div className="max-w-2xl mx-auto">
            {/* Welcome section with classic styling */}
            <div className="text-center mb-10">
              <h1
                className="text-4xl font-bold text-[var(--color-text-primary)] mb-4"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                통합 도서 검색
              </h1>
              <p className="text-lg text-[var(--color-text-secondary)] italic">
                여러 도서관과 온라인 서점을 한 번에 검색합니다
              </p>
            </div>

            {/* Decorative element */}
            <div className="flex justify-center mb-8">
              <div className="flex items-center gap-4">
                <div className="w-20 h-px bg-gradient-to-r from-transparent via-[var(--color-border-gold)] to-transparent" />
                <svg
                  className="w-8 h-8 text-[var(--color-accent-gold)]"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <div className="w-20 h-px bg-gradient-to-r from-transparent via-[var(--color-border-gold)] to-transparent" />
              </div>
            </div>

            {/* Search bar */}
            <SearchBar onSearch={handleSearch} loading={loading} />

            {/* Feature description with classic list styling */}
            <div className="mt-12 p-6 bg-[var(--color-bg-secondary)] rounded-lg border border-[var(--color-border)]">
              <h3
                className="text-lg font-semibold text-[var(--color-text-primary)] mb-4"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                검색 가능한 소스
              </h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[var(--color-text-secondary)]">
                {[
                  '알라딘 서점',
                  '공공도서관',
                  '싸피 e-book 도서관',
                  '리디북스 셀렉트',
                  '부커스',
                  '구글 플레이북',
                  '내 보유 장서'
                ].map((source) => (
                  <li key={source} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent-gold)]" />
                    {source}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Book selection step */}
        {searchStep === 'book-selection' && (
          <BookList
            books={aladinBooks}
            onSelectBook={handleSelectBook}
            loading={loading}
          />
        )}

        {/* Source results step */}
        {searchStep === 'source-results' && selectedBook && (
          <SourceResults
            selectedBook={selectedBook}
            results={sourceResults}
            onBack={handleBackToBookList}
            loading={loading}
          />
        )}
      </main>

      {/* Footer with classic styling */}
      <footer className="mt-auto py-6 border-t border-[var(--color-border)]">
        <div className="container mx-auto px-4 text-center">
          <p
            className="text-sm text-[var(--color-text-muted)] italic"
            style={{ fontFamily: 'var(--font-body)' }}
          >
            MyBrarian - 당신의 개인 도서관 사서
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
