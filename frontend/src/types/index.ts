// Aladin Book (Step 1)
export interface AladinBook {
  title: string;
  author: string | null;
  publisher: string | null;
  pubDate: string | null;
  isbn13: string | null;
  isbn: string | null;
  description: string | null;
  cover: string | null;
  categoryName: string | null;
  mainTitle: string | null;
  subTitle: string | null;
}

// Aladin Search Response
export interface AladinSearchResponse {
  query: string;
  total_count: number;
  books: AladinBook[];
}

// Book Result (Single result from a source)
export interface BookResult {
  title: string | null;
  author: string | null;
  isbn: string | null;
  availability: string | null;
  url: string | null;
  additional_info: Record<string, any> | null;
}

// Source Result
export interface SourceResult {
  source_name: string;
  priority: number;
  success: boolean;
  error_message: string | null;
  results: BookResult[];
  result_count: number;
}

// Integrated Search Response (Step 2)
export interface SearchResponse {
  query: string;
  isbn: string | null;
  selected_title: string | null;
  total_sources: number;
  sources: SourceResult[];
}

// API Error
export interface ApiError {
  detail: string;
}
