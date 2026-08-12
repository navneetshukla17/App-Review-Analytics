import { describe, expect, it } from 'vitest';
import { buildFilterParams } from '../filters.js';

describe('buildFilterParams', () => {
  it('drops empty filters', () => {
    expect(buildFilterParams({ q: '', rating: '', sentiment: '', start_date: '', end_date: '' })).toEqual({});
  });

  it('keeps filled filters', () => {
    expect(buildFilterParams({ q: 'crash', rating: '1' })).toEqual({ q: 'crash', rating: '1' });
  });
});
