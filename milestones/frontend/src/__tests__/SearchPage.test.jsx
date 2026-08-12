import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SearchPage from '../pages/SearchPage.jsx';
import * as api from '../api.js';

vi.mock('../api.js', () => ({
  searchApps: vi.fn(),
  createApp: vi.fn(),
  startFetch: vi.fn(),
  getJob: vi.fn(),
}));

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('searches and displays candidate apps', async () => {
    api.searchApps.mockResolvedValue({
      results: [
        { platform: 'playstore', store_app_id: 'com.spotify.music', name: 'Spotify', developer: 'Spotify AB' },
      ],
      errors: [],
    });
    render(
      <MemoryRouter>
        <SearchPage />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/app name/i), { target: { value: 'Spotify' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('Spotify')).toBeInTheDocument());
    expect(api.searchApps).toHaveBeenCalledWith('Spotify', 'both');
  });

  it('creates the app and starts a fetch when clicking fetch', async () => {
    api.searchApps.mockResolvedValue({
      results: [{ platform: 'appstore', store_app_id: '389801252', name: 'Instagram', developer: 'Instagram, Inc.' }],
      errors: [],
    });
    api.createApp.mockResolvedValue({ id: 7 });
    api.startFetch.mockResolvedValue({ id: 42 });
    api.getJob.mockResolvedValue({ status: 'completed', fetched_count: 10 });

    render(
      <MemoryRouter>
        <SearchPage />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/app name/i), { target: { value: 'Instagram' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('Instagram')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /import reviews/i }));
    await waitFor(() => expect(api.createApp).toHaveBeenCalledWith(
      expect.objectContaining({ store_app_id: '389801252' }),
    ));
    await waitFor(() => expect(api.startFetch).toHaveBeenCalledWith(7));
  });
});
