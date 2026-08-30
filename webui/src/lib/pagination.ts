/**
 * Pagination utilities
 */

export type PaginationParams = {
  page: number;
  limit: number;
};

export type PaginatedResponse<T> = {
  data: T[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

export const DEFAULT_PAGE_SIZE = 50;
export const MAX_PAGE_SIZE = 500;

/**
 * Parse and validate pagination parameters
 */
export function parsePaginationParams(
  searchParams: Record<string, string | string[] | undefined>,
): PaginationParams {
  const page = Math.max(1, parseInt(String(searchParams.page ?? "1"), 10) || 1);
  let limit = parseInt(String(searchParams.limit ?? DEFAULT_PAGE_SIZE), 10) || DEFAULT_PAGE_SIZE;

  // Clamp limit between 1 and MAX_PAGE_SIZE
  limit = Math.min(Math.max(1, limit), MAX_PAGE_SIZE);

  return { page, limit };
}

/**
 * Calculate offset for database queries
 */
export function getOffset(page: number, limit: number): number {
  return (page - 1) * limit;
}

/**
 * Build paginated response
 */
export function buildPaginatedResponse<T>(
  data: T[],
  page: number,
  limit: number,
  total: number,
): PaginatedResponse<T> {
  return {
    data,
    page,
    limit,
    total,
    hasMore: page * limit < total,
  };
}
