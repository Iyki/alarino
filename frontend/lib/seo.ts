export function makeWordPageTitle(word: string): string {
  const normalized = word.trim();
  if (!normalized) {
    return "Alarino Dictionary";
  }

  return `${normalized.charAt(0).toUpperCase()}${normalized.slice(1)} in Yoruba | Alarino Dictionary`;
}
