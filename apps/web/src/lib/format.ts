export function formatCurrency(value: number | null): string {
  if (value === null) {
    return "Provisional";
  }

  return new Intl.NumberFormat("en-NZ", {
    style: "currency",
    currency: "NZD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatNumber(value: number | null): string {
  if (value === null) {
    return "TBC";
  }

  return new Intl.NumberFormat("en-NZ", {
    maximumFractionDigits: 2,
  }).format(value);
}

