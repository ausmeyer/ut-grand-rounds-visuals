export const WEEKS = Object.freeze(Array.from({ length: 29 }, (_, i) => ((43 + i) % 52) + 1));
export const QUESTION = 'Based on U.S. outpatient surveillance, in which week of the year do you think a typical flu season peaks?';
export const isWeek = value => Number.isInteger(value) && WEEKS.includes(value);
export const isSession = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value || '');
export function weekAt(index) {
  if (!Number.isInteger(index) || index < 0 || index >= WEEKS.length) throw new Error('Invalid slider position');
  return WEEKS[index];
}
export function normalizeResults(data) {
  if (!data || !Array.isArray(data.bins) || data.bins.length !== WEEKS.length ||
      !Number.isSafeInteger(data.unsure) || data.unsure < 0) throw new Error('Invalid poll results');
  const bins = WEEKS.map((week, i) => {
    const bin = data.bins[i];
    if (bin.week !== week || !Number.isSafeInteger(bin.count) || bin.count < 0) throw new Error('Invalid histogram bin');
    return { week, count: bin.count };
  });
  return { bins, unsure: data.unsure, numericCount: bins.reduce((n, bin) => n + bin.count, 0) };
}
