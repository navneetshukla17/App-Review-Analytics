export function buildFilterParams(filters) {
  const params = {};
  for (const [key, value] of Object.entries(filters)) {
    if (value !== '' && value !== null && value !== undefined) params[key] = value;
  }
  return params;
}
