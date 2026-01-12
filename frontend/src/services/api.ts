import type { AladinSearchResponse, SearchResponse, ApiError } from '../types';

const API_BASE_URL = '/api';

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(error.detail);
  }

  return response.json();
}

// Step 1: Search books in Aladin
export async function searchBooksAladin(
  query: string,
  maxResults: number = 10
): Promise<AladinSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    max_results: maxResults.toString(),
  });
  return apiFetch<AladinSearchResponse>(
    `${API_BASE_URL}/books/search?${params}`
  );
}

// Step 2: Search all sources with selected book
export async function searchAllSources(
  isbn: string,
  title: string,
  mainTitle?: string,
  maxResults: number = 5
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    isbn,
    title,
    max_results: maxResults.toString(),
  });
  if (mainTitle) {
    params.append('main_title', mainTitle);
  }
  return apiFetch<SearchResponse>(
    `${API_BASE_URL}/books/search?${params}`,
    { method: 'POST' }
  );
}
